"""exit / logout — terminate the session.

Split out of the former ``basic.py`` starter set; behaviour unchanged. One
class registered under both names (``exit`` and ``logout``), matching the
original ``@register("exit", "logout")``.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Exit"]


@register("exit", "logout")
class Exit(Command):
    async def run(self) -> int:
        self.ctx.should_exit = True
        if self.args:
            try:
                return int(self.args[0]) & 0xFF
            except ValueError:
                self.errline(f"{self.prog}: {self.args[0]}: numeric argument required")
                return 2
        return 0
