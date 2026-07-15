"""top — a one-shot process/resource snapshot.

Why a builtin (not the LLM path): top's header is a tight, structured readout
of uptime, load, task counts and mem — all of which we already model elsewhere
(boot_time, /proc/meminfo, the ps process set). An LLM would happily invent
inconsistent numbers; deriving them from the same sources keeps `top`, `uptime`,
`free` and `ps` mutually consistent.

Real top runs an interactive full-screen loop that refreshes until 'q'. We
never do that (it would hang a non-PTY session and there's no curses here);
instead we always render a single frame and return — the same output `top -bn1`
(batch mode, one iteration) produces, which is also what scripts scrape. This
is the honest-simplest behaviour: interactive callers get one screen, scripts
get exactly what they expect.
"""

from __future__ import annotations

import time as _time

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._sysprofile import _profile

__all__ = ["Top"]

# Reuse the same synthetic process set ps exposes, so the two agree. Kept as a
# small local list (user, pid, cmd, %cpu, %mem) rather than importing ps's
# private table — top shows different columns and its own session rows.
_PROCS = [
    ("root", 1, "systemd", 0.0, 0.1),
    ("root", 411, "systemd-journal", 0.0, 0.3),
    ("root", 601, "sshd", 0.0, 0.1),
    ("root", 623, "cron", 0.0, 0.0),
    ("postgres", 690, "postgres", 0.3, 2.1),
    ("redis", 705, "redis-server", 0.2, 0.8),
]


@register("top", "/usr/bin/top")
class Top(Command):
    async def run(self) -> int:
        prof = _profile(self.ctx)
        now = self.ctx.now() if hasattr(self.ctx, "now") else _time.time()
        clock = _time.strftime("%H:%M:%S", _time.gmtime(now))

        # uptime span from the emulated boot time (same source as `uptime`).
        boot = getattr(self.ctx, "boot_time", None)
        if boot is not None and now > boot:
            secs = int(now - boot)
            days = secs // 86400
            hh = (secs % 86400) // 3600
            mm = (secs % 3600) // 60
            span = (f"{days} day{'s' if days != 1 else ''}, {hh:2d}:{mm:02d}"
                    if days else f"{hh:2d}:{mm:02d}")
        else:
            span = "7 days,  3:14"

        total_mb = getattr(prof, "memory_mb", 8192)
        total_kb = total_mb * 1024
        # Mirror /proc/meminfo's free/used split so `free` and `top` agree.
        free_kb = 5432100
        used_kb = total_kb - free_kb
        buff_kb = 123456 + 1345678

        user = self.ctx.username
        sess = [
            (user, 8021, "bash", 0.0, 0.0),
            (user, 8090, "top", 0.3, 0.1),
        ]
        procs = _PROCS + sess
        running = 1
        sleeping = len(procs) - running

        self.line(f"top - {clock} up {span},  1 user,  "
                  f"load average: 0.08, 0.03, 0.01")
        self.line(f"Tasks: {len(procs) + 80:3d} total,   {running} running, "
                  f"{sleeping + 80:3d} sleeping,   0 stopped,   0 zombie")
        self.line("%Cpu(s):  0.7 us,  0.3 sy,  0.0 ni, 98.9 id,  0.1 wa,  "
                  "0.0 hi,  0.0 si,  0.0 st")
        self.line(f"MiB Mem :{total_kb/1024:9.1f} total,{free_kb/1024:9.1f} "
                  f"free,{used_kb/1024:9.1f} used,{buff_kb/1024:9.1f} "
                  f"buff/cache")
        self.line(f"MiB Swap:{2097148/1024:9.1f} total,{2097148/1024:9.1f} "
                  f"free,{0.0:9.1f} used.{6931200/1024:9.1f} avail Mem")
        self.line("")
        self.line("    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  "
                  "%MEM     TIME+ COMMAND")
        for u, pid, cmd, cpu, mem in sorted(
                procs, key=lambda p: p[3], reverse=True):
            self.line(f"{pid:>7} {u:<8}  20   0  {'182340':>7} {'12044':>6} "
                      f"{'8020':>6} S {cpu:>5.1f} {mem:>5.1f}   0:00.02 "
                      f"{cmd}")
        return 0
