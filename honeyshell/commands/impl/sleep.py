"""sleep — pause for a number of seconds.

We do NOT actually sleep: a honeypot blocking for the requested duration would
let an attacker tie up the session (and is a timing tell). We validate the
operand like GNU sleep (reporting bad intervals) and return immediately.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Sleep"]


@register("sleep", "/bin/sleep")
class Sleep(Command):
    async def run(self) -> int:
        if not self.args:
            return self.fail("missing operand")
        # Accept forms like 5, 5s, 0.5, 2m — validate the numeric part.
        val = self.args[0]
        num = val.rstrip("smhd") if val[-1:] in "smhd" else val
        try:
            float(num)
        except ValueError:
            return self.fail(f"invalid time interval '{val}'")
        return 0  # return immediately; do not actually block
