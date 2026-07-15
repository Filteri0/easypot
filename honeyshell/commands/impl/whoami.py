"""whoami — print the effective username.

Split out of the former ``basic.py`` starter set; behaviour unchanged.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Whoami"]


@register("whoami", "/usr/bin/whoami")
class Whoami(Command):
    async def run(self) -> int:
        self.line(self.ctx.username)
        return 0
