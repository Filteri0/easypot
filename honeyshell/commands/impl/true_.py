"""true — do nothing, exit 0.

Split out of the former ``basic.py`` starter set; behaviour unchanged. The
module is named ``true_`` (and the class ``True_``) because ``true`` is a
Python keyword; the registered command name is still ``true``.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["True_"]


@register("true", "/bin/true")
class True_(Command):
    async def run(self) -> int:
        return 0
