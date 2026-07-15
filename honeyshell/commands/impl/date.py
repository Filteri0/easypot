"""date — print the current date/time.

Uses the real clock so the honeypot looks alive. Honours a leading ``+FORMAT``
argument by translating the common strftime directives; otherwise prints the
default ``Day Mon DD HH:MM:SS TZ YYYY`` form.
"""

from __future__ import annotations

import time

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Date"]


@register("date", "/bin/date")
class Date(Command):
    async def run(self) -> int:
        fmt = None
        for a in self.args:
            if a.startswith("+"):
                fmt = a[1:]
        # Read the honeypot's emulated clock (not the host's), so `date` agrees
        # with `ls -l` mtimes and uptime. Falls back to real time when a bare
        # context has no clock wired (unit tests).
        now = self.ctx.now() if hasattr(self.ctx, "now") else time.time()
        tm = time.gmtime(now)
        if fmt:
            self.line(time.strftime(fmt, tm))
        else:
            self.line(time.strftime("%a %b %e %H:%M:%S UTC %Y", tm))
        return 0
