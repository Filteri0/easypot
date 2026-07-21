"""sleep — pause for a number of seconds.

We do NOT actually sleep: a honeypot blocking for the requested duration would
let an attacker tie up the session (and is a timing tell). We validate the
operand like GNU sleep (reporting bad intervals) and return immediately.

We *do* advance the session's emulated clock (``ctx.time_offset``) by the
requested duration. Returning instantly without moving the clock makes the
classic sandbox-evasion probe (ATT&CK T1497)::

    date +%s; sleep 2; date +%s

print two *identical* timestamps, which no real system would — an attacker uses
exactly this to fingerprint honeypots. Advancing the offset keeps time
self-consistent across commands while still never blocking.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Sleep"]

#: Suffix multipliers, per GNU sleep: seconds/minutes/hours/days.
_UNITS = {"s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}


@register("sleep", "/bin/sleep")
class Sleep(Command):
    async def run(self) -> int:
        if not self.args:
            return self.fail("missing operand")
        # GNU sleep accepts multiple operands and sleeps for their sum.
        total = 0.0
        for val in self.args:
            suffix = val[-1:] if val[-1:] in _UNITS else ""
            num = val[:-1] if suffix else val
            try:
                seconds = float(num)
            except ValueError:
                return self.fail(f"invalid time interval '{val}'")
            if seconds < 0:
                return self.fail(f"invalid time interval '{val}'")
            total += seconds * _UNITS.get(suffix, 1.0)
        # Advance emulated time rather than blocking (see module docstring).
        self.ctx.time_offset += total
        return 0
