"""uptime — show how long the system has been running.

Cowrie-inspired, but derived from the emulated clock so it stays consistent
with ``date`` and file mtimes. The uptime span is computed from the session's
``boot_time`` (set at login); time-of-day comes from ``ctx.now()``. If neither
is wired (bare unit-test context), falls back to a plausible constant.
"""

from __future__ import annotations

import time

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Uptime"]


@register("uptime", "/usr/bin/uptime")
class Uptime(Command):
    async def run(self) -> int:
        now = self.ctx.now() if hasattr(self.ctx, "now") else time.time()
        clock = time.strftime("%H:%M:%S", time.gmtime(now))
        boot = getattr(self.ctx, "boot_time", None)
        if boot is not None and now > boot:
            secs = int(now - boot)
            days = secs // 86400
            hours = (secs % 86400) // 3600
            mins = (secs % 3600) // 60
            if days > 0:
                span = f"{days} day{'s' if days != 1 else ''}, {hours:2d}:{mins:02d}"
            else:
                span = f"{hours:2d}:{mins:02d}"
        else:
            span = "7 days,  3:14"
        self.line(
            f" {clock} up {span},  1 user,  "
            f"load average: 0.08, 0.03, 0.01"
        )
        return 0
