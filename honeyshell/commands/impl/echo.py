"""echo — print arguments. Supports ``-n`` (suppress trailing newline).

Split out of the former ``basic.py`` starter set: one command per file so the
built-in surface is easy to scan and edit. Behaviour is unchanged.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Echo"]


@register("echo", "/bin/echo")
class Echo(Command):
    async def run(self) -> int:
        args = self.args
        newline = True
        # consume leading -n flags (echo's only flag we support for now)
        while args and args[0] == "-n":
            newline = False
            args = args[1:]
        text = " ".join(args)
        self.write(text + "\n" if newline else text)
        return 0
