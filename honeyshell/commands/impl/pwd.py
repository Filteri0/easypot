"""pwd — print the current working directory.

Split out of the former ``basic.py`` starter set; behaviour unchanged.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Pwd"]


@register("pwd", "/bin/pwd")
class Pwd(Command):
    async def run(self) -> int:
        self.line(self.ctx.cwd)
        return 0
