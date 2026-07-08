"""The async command base class.

Design lineage
--------------
Borrowed from Cowrie's ``HoneyPotCommand``: every emulated command is a class
with a small, uniform contract (write output, read input, report an exit
status). We keep that shape but make it ``async`` so it composes with
asyncio/asyncssh, and we replace Cowrie's manual ``cmdstack`` with the natural
coroutine call stack — an interactive command simply ``await``\\s
:meth:`read_line` and blocks the shell until its ``run`` returns.

Contract
--------
The interpreter resolves a command token to a ``Command`` subclass, then::

    cmd = SubCls(ctx, argv, stdin, stdout, stderr)
    exit_code = await cmd.run()

* ``argv`` is the command as invoked; ``argv[0]`` is the token the attacker
  typed (``ls`` or ``/bin/ls``), and :pyattr:`args` is everything after it.
* ``run`` returns an ``int`` exit code. Subclasses override ``run`` only.
* Output goes through :meth:`write`/:meth:`line` (stdout) and
  :meth:`error`/:meth:`errline` (stderr); the interpreter/pipeline decides
  where those streams actually go.
"""

from __future__ import annotations

from honeyshell.commands.context import ShellContext
from honeyshell.commands.streams import (
    NullReader,
    Readable,
    StringWriter,
    Writable,
)

__all__ = ["Command"]


class Command:
    #: Canonical name; set automatically by @register if left blank.
    name: str = ""

    def __init__(
        self,
        ctx: ShellContext,
        argv: list[str],
        stdin: Readable | None = None,
        stdout: Writable | None = None,
        stderr: Writable | None = None,
    ) -> None:
        self.ctx = ctx
        self.argv = list(argv)
        self.stdin: Readable = stdin or NullReader()
        self.stdout: Writable = stdout or StringWriter()
        self.stderr: Writable = stderr or StringWriter()
        self.exit_code = 0

    # -- convenience accessors --

    @property
    def prog(self) -> str:
        """The token as invoked (argv[0]), for use in error messages."""
        return self.argv[0] if self.argv else self.name

    @property
    def args(self) -> list[str]:
        """Everything after argv[0]."""
        return self.argv[1:]

    # -- output helpers --

    def write(self, data: str) -> None:
        self.stdout.write(data)

    def line(self, data: str = "") -> None:
        self.stdout.write(data + "\n")

    def error(self, data: str) -> None:
        self.stderr.write(data)

    def errline(self, data: str = "") -> None:
        self.stderr.write(data + "\n")

    def fail(self, message: str, code: int = 1) -> int:
        """Write ``prog: message`` to stderr and return an exit code."""
        self.errline(f"{self.prog}: {message}")
        return code

    # -- input helpers --

    async def read_line(self) -> str | None:
        return await self.stdin.readline()

    async def read_all(self) -> str:
        return await self.stdin.read()

    # -- to override --

    async def run(self) -> int:
        raise NotImplementedError
