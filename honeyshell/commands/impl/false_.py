"""false — do nothing, exit 1.

Split out of the former ``basic.py`` starter set; behaviour unchanged. Named
``false_``/``False_`` to avoid the Python keyword; command name is ``false``.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["False_"]


@register("false", "/bin/false")
class False_(Command):
    async def run(self) -> int:
        return 1
