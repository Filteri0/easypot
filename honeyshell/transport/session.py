"""The shell session: the interactive REPL that drives the interpreter.

Deliberately transport-agnostic. It reads lines from an injected ``reader``
(``async readline() -> str | None``) and writes to injected ``stdout`` /
``stderr`` sinks, so it can be unit-tested with in-memory fakes and reused
unchanged behind asyncssh. The asyncssh glue in ``ssh_server.py`` simply adapts
a connection's streams to this interface.

A fresh :class:`~honeyshell.fs.VirtualFS` is loaded per session, giving each
attacker an independent, throw-away filesystem (matching Cowrie semantics).
"""

from __future__ import annotations

from honeyshell.commands.context import ShellContext
from honeyshell.commands.streams import Readable, Writable
from honeyshell.fs import load_json
from honeyshell.shell import Interpreter
from honeyshell.transport.config import ServerConfig

__all__ = ["ShellSession", "INTERRUPT"]


class _Interrupt:
    """Sentinel a reader returns for Ctrl-C (SIGINT) instead of a line.

    Distinct from ``""`` (a real empty line — the user pressed Enter) and
    ``None`` (EOF / Ctrl-D). The interactive loop treats it as "abandon the
    current input and show a fresh prompt", matching bash: Ctrl-C prints ``^C``,
    drops the half-typed line, and redraws ONE new prompt — it does not run
    anything and does not stack extra prompts.

    Transport-agnostic: the asyncssh reader in ``ssh_server`` maps
    ``BreakReceived`` onto this; in-memory test readers simply never emit it,
    so unit tests are unaffected.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return "INTERRUPT"


#: Module-level singleton sentinel (compare with ``is``).
INTERRUPT = _Interrupt()


class ShellSession:
    def __init__(
        self,
        config: ServerConfig,
        reader: Readable,
        stdout: Writable,
        stderr: Writable | None = None,
        *,
        username: str | None = None,
        is_tty: bool = False,
        term_width: int = 80,
        miss_handler=None,
        memory_settings=None,
    ) -> None:
        self.config = config
        self.reader = reader
        self.stdout = stdout
        self.stderr = stderr or stdout
        self.username = username or config.default_user


        environ = dict(config.base_environ)
        home = "/root" if self.username == "root" else f"/home/{self.username}"
        environ.update(
            {
                "USER": self.username,
                "LOGNAME": self.username,
                "HOME": home,
                "HOSTNAME": config.hostname,
            }
        )
        fs = load_json(config.fs_path)
        # Honeypots accept arbitrary usernames, but the base filesystem only
        # ships a handful of home directories. If the login's home is missing,
        # materialise it (owned by the user) so `ls`/`cd ..` behave like a real
        # box — a real Linux would either have the home or fall back to /, and
        # an absent home is an easy honeypot tell. This mirrors how Cowrie
        # provisions a home for the session's user.
        self._ensure_home(fs, home)
        self.ctx = ShellContext(
            fs=fs,
            cwd=home,
            environ=environ,
            username=self.username,
            hostname=config.hostname,
            is_tty=is_tty,
            term_width=term_width,
            system=config.system,
        )
        # Attach per-session dynamic memory when the LLM backend is active. Done
        # here (not in ShellContext defaults) so a non-LLM session stays lean
        # and memory imports don't load unless needed.
        if miss_handler is not None:
            from honeyshell.core.config import MemorySettings
            from honeyshell.memory import Pruner, SessionMemory
            self.ctx.memory = SessionMemory()
            self.ctx.pruner = Pruner(memory_settings or MemorySettings())
        self.interp = Interpreter(
            self.ctx, self.stdout, self.stderr, miss_handler=miss_handler
        )

    @staticmethod
    def _ensure_home(fs, home: str) -> None:
        """Create ``home`` in the VFS if absent, owned by a non-root uid.

        Non-root homes are created with uid/gid 1000 via ``mkdir`` (parent
        dirs materialised first with ``makedirs``); root's home (/root) is
        expected to exist in the base tree already. Failures are swallowed: a
        missing home must never crash the session. This mirrors how Cowrie
        provisions a home for the session's user so an absent directory can't
        be used to fingerprint the honeypot.
        """
        if not home or fs.exists(home):
            return
        parent = home.rsplit("/", 1)[0] or "/"
        try:
            if not fs.exists(parent):
                fs.makedirs(parent, perm=0o755)
            uid = 0 if home == "/root" else 1000
            fs.mkdir(home, uid=uid, gid=uid, perm=0o755)
        except Exception:  # noqa: BLE001 — never let provisioning break login
            pass

    # -- prompt --

    def prompt(self) -> str:
        cwd, home = self.ctx.cwd, self.ctx.home
        if cwd == home:
            disp = "~"
        elif cwd.startswith(home + "/"):
            disp = "~" + cwd[len(home):]
        else:
            disp = cwd
        sym = "#" if self.username == "root" else "$"
        return f"{self.username}@{self.config.hostname}:{disp}{sym} "

    # -- run modes --

    async def run_interactive(self) -> int:
        if self.config.motd:
            self.stdout.write(self.config.motd)
            if not self.config.motd.endswith("\n"):
                self.stdout.write("\n")

        while True:
            self.stdout.write(self.prompt())
            line = await self.reader.readline()
            if line is None:  # EOF (Ctrl-D)
                self.stdout.write("logout\n")
                break
            if line is INTERRUPT:  # Ctrl-C: abandon this line, redraw prompt.
                # The reader already emitted "^C\n"; we just loop so exactly one
                # fresh prompt is drawn. No command runs. (Fixes the prompt
                # storm from treating BreakReceived as an empty line.)
                continue
            line = line.rstrip("\r\n")
            # A PTY client runs in canonical mode: it echoes typed input and
            # emits the newline itself, so the server must NOT echo or add a
            # newline (doing so double-prints the line). We just run it.
            await self.interp.execute(line)
            if self.ctx.should_exit:
                self.stdout.write("logout\n")
                break
        return self.interp.last_status

    async def run_exec(self, command: str) -> int:
        """Non-interactive single command (``ssh host "cmd"``)."""
        await self.interp.execute(command)
        return self.interp.last_status
