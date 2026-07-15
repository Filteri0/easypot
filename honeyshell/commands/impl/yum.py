"""yum / dnf — the RHEL-family package managers, which this Debian host lacks.

Why a builtin that just fails: left to the LLM miss-path, qwen tends to be
"helpfully" wrong — e.g. ``yum isn't installed, using apt-get instead...`` —
an explanatory, human tone no real shell ever uses. A real Debian box has
neither yum nor dnf, so the only correct response is the cold
``bash: yum: command not found`` (exit 127). Hard-wiring that removes the AI
tell and costs nothing.

Registered for both ``yum`` and ``dnf``. We deliberately register NO canonical
``/usr/bin`` path (unlike other builtins) so ``which yum`` still reports it as
absent — consistent with a box that genuinely doesn't ship them.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Yum"]


@register("yum", "dnf")
class Yum(Command):
    #: Read by `which`: this command is emulated only to fail, so `which yum`
    #: must still report it absent (the host genuinely ships neither).
    absent_from_path = True

    async def run(self) -> int:
        # bash prints this to stderr and returns 127. `self.prog` is the name
        # as invoked (yum or dnf), so both read naturally.
        self.errline(f"bash: {self.prog}: command not found")
        return 127
