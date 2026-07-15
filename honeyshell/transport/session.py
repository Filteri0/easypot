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

import time as _time
import uuid

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

#: How long the emulated host has "been up" at login. A fixed, plausible span
#: (~7 days) so `uptime`/`who` are stable and consistent with the emulated
#: clock. boot_time = now - this.
_BOOT_AGE_SECONDS = 7 * 86400 + 3 * 3600 + 14 * 60  # 7 days, 3:14


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
        fetch_content=None,
        read_prompt=None,
        event_bus=None,
        src_ip=None,
        src_port=None,
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
        # Runtime-created files (echo > f, mkdir, touch) must not default to
        # mtime 0 -> "Jan 1 1970", which an attacker spots instantly via
        # `echo x > f; ls -l`. Stamp them with wall-clock now. (Full emulated-
        # clock consistency across date/uptime/ls is a separate, larger task;
        # this fixes the glaring 1970 tell.)
        fs._clock = _time.time
        # Slide the shipped 2024 timeline forward so the newest file sits a bit
        # before "now" — keeping relative layering but making absolute dates
        # agree with date/uptime. Anchor a day before boot so recent activity
        # predates the current session plausibly.
        try:
            fs.shift_mtimes(_time.time() - _BOOT_AGE_SECONDS - 86400)
        except Exception:  # noqa: BLE001 — never let time-shift break login
            pass
        # Provision the login user so uid / home / passwd all agree. A honeypot
        # accepts arbitrary usernames, but then `id`, `ls -l`, and
        # `grep user /etc/passwd` must not contradict each other (an easy tell).
        # This resolves the uid from /etc/passwd if the account ships there, or
        # allocates a fresh stable uid and appends a passwd line, then creates
        # the home owned by that uid.
        uid = self._provision_user(fs, self.username, home)
        # Runtime-created files/dirs (echo > f, mkdir, touch) should be owned by
        # the logged-in user, not root. Stamp the fs default owner with the
        # resolved login uid. Fixes `echo x > f; ls -l` showing root as owner.
        try:
            fs.set_owner(uid)
        except Exception:  # noqa: BLE001
            pass
        self.ctx = ShellContext(
            fs=fs,
            cwd=home,
            environ=environ,
            username=self.username,
            hostname=config.hostname,
            is_tty=is_tty,
            term_width=term_width,
            system=config.system,
            session_id=uuid.uuid4().hex,
            login_uid=uid,
            clock=_time.time,
            boot_time=_time.time() - _BOOT_AGE_SECONDS,
            src_ip=src_ip,
            src_port=src_port,
        )
        # Attach per-session dynamic memory when the LLM backend is active. Done
        # here (not in ShellContext defaults) so a non-LLM session stays lean
        # and memory imports don't load unless needed.
        if miss_handler is not None:
            from honeyshell.core.config import MemorySettings
            from honeyshell.memory import Pruner, SessionMemory
            self.ctx.memory = SessionMemory()
            self.ctx.pruner = Pruner(memory_settings or MemorySettings())
        # Wire the URL-content fetcher (curl/wget stdout path) when provided.
        # Kept off the ShellContext defaults so non-LLM sessions stay lean.
        if fetch_content is not None:
            self.ctx.fetch_content = fetch_content
        # Interactive credential prompt (sudo/su/passwd). Wired from the SSH
        # layer, which owns the terminal echo control.
        if read_prompt is not None:
            self.ctx.read_prompt = read_prompt
        # Audit bus for credential-capture events (sudo/su/passwd).
        if event_bus is not None:
            self.ctx.event_bus = event_bus
        self.interp = Interpreter(
            self.ctx, self.stdout, self.stderr, miss_handler=miss_handler
        )

    @staticmethod
    def _provision_user(fs, username: str, home: str) -> int:
        """Ensure uid / home / passwd are mutually consistent for ``username``.

        Returns the uid to expose via ``id``/``whoami``. Behaviour:
        * root -> uid 0, home /root assumed present.
        * user already in /etc/passwd -> reuse that uid, create home if missing.
        * unknown user -> allocate a fresh uid (max existing +1, from 1000),
          append a passwd line, and create the home. This keeps
          ``grep user /etc/passwd`` and ``id`` in agreement instead of the old
          hardcoded uid=1000 for everyone (which also collided with phil).

        All failures are swallowed: provisioning must never break login.
        """
        if username == "root" or home == "/root":
            return 0
        uid = None
        max_uid = 999
        try:
            passwd = fs.readtext("/etc/passwd")
            for ln in passwd.splitlines():
                parts = ln.split(":")
                if len(parts) >= 3 and parts[2].isdigit():
                    u = int(parts[2])
                    if parts[0] == username:
                        uid = u
                    if 1000 <= u < 60000:
                        max_uid = max(max_uid, u)
        except Exception:  # noqa: BLE001
            passwd = None

        if uid is None:
            uid = max_uid + 1
            # Append a plausible passwd entry so the account is discoverable and
            # consistent with `id`. Best-effort; ignore if fs has no passwd.
            try:
                line = (f"{username}:x:{uid}:{uid}::"
                        f"/home/{username}:/bin/bash\n")
                existing = passwd if passwd is not None else ""
                if not existing.endswith("\n") and existing:
                    existing += "\n"
                fs.write_file("/etc/passwd", existing + line)
            except Exception:  # noqa: BLE001
                pass

        # Create the home dir owned by the resolved uid.
        try:
            if home and not fs.exists(home):
                parent = home.rsplit("/", 1)[0] or "/"
                if not fs.exists(parent):
                    fs.makedirs(parent, perm=0o755)
                fs.mkdir(home, uid=uid, gid=uid, perm=0o755)
        except Exception:  # noqa: BLE001
            pass
        return uid

    # -- prompt --

    def prompt(self) -> str:
        # Read identity from ctx (not self.username): `su` switches
        # ctx.username, and the prompt must follow — otherwise `su` leaves the
        # prompt showing the old user, a clear tell.
        user = self.ctx.username
        cwd, home = self.ctx.cwd, self.ctx.home
        if cwd == home:
            disp = "~"
        elif cwd.startswith(home + "/"):
            disp = "~" + cwd[len(home):]
        else:
            disp = cwd
        sym = "#" if user == "root" else "$"
        return f"{user}@{self.config.hostname}:{disp}{sym} "

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
