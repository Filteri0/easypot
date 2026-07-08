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


class ShellSession:
    def __init__(
        self,
        config: ServerConfig,
        reader: Readable,
        stdout: Writable,
        stderr: Writable | None = None,
        *,
        username: str | None = None,
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
        self.ctx = ShellContext(
            fs=load_json(config.fs_path),
            cwd=home,
            environ=environ,
            username=self.username,
            hostname=config.hostname,
        )
        self.interp = Interpreter(self.ctx, self.stdout, self.stderr)

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
            line = line.rstrip("\r\n")
            await self.interp.execute(line)
            if self.ctx.should_exit:
                self.stdout.write("logout\n")
                break
        return self.interp.last_status

    async def run_exec(self, command: str) -> int:
        """Non-interactive single command (``ssh host "cmd"``)."""
        await self.interp.execute(command)
        return self.interp.last_status
