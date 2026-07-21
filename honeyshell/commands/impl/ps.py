"""ps — report a snapshot of current processes.

The honeypot has no real process table, so we synthesise a small, believable
set of system processes plus a shell/ps for the session user.

We distinguish the two forms attackers actually use, because **their headers
and columns differ** and getting that wrong is a fingerprint:

* ``ps aux`` (BSD)  -> ``USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND``
* ``ps -ef`` (SysV) -> ``UID PID PPID C STIME TTY TIME CMD``

The probe suite caught this: the previous implementation emitted the ``-ef``
header for ``ps aux`` too, so ``ps aux | head -5`` was missing the ``COMMAND``
column an attacker greps for. ``ps aux`` is one of the most common recon
commands there is, so the mismatch was a cheap, high-visibility tell.

Deferred: reflecting commands the attacker actually ran (would need a process
model); ``-p``/filtering.
"""

from __future__ import annotations

import time as _time

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Ps"]

# (user, pid, ppid, vsz, rss, stat, cputime, cmd) — VSZ/RSS in KiB.
#
# ``cputime`` matters: a long-lived box's init/journald have *accumulated* CPU
# time, so a table where every process shows 0:00 is a tell (the probe suite
# checks for exactly this). Values scale with how busy each daemon really is.
_PROCS = [
    ("root", 1, 0, 167404, 11876, "Ss", "0:04", "/sbin/init"),
    ("root", 2, 0, 0, 0, "S", "0:00", "[kthreadd]"),
    ("root", 411, 1, 46752, 8564, "Ss", "0:12", "/lib/systemd/systemd-journald"),
    ("root", 439, 1, 22932, 5412, "Ss", "0:01", "/lib/systemd/systemd-udevd"),
    ("root", 601, 1, 15852, 9284, "Ss", "0:02", "/usr/sbin/sshd -D"),
    ("root", 623, 1, 8352, 3208, "Ss", "0:00", "/usr/sbin/cron -f"),
    ("www-data", 712, 1, 57344, 14920, "S", "0:07", "nginx: worker process"),
]


@register("ps", "/bin/ps")
class Ps(Command):
    async def run(self) -> int:
        flags = "".join(a.lstrip("-") for a in self.args if a.startswith("-"))
        bare = "".join(a for a in self.args if not a.startswith("-"))

        # BSD style: `ps aux` / `ps ax` (no leading dash). SysV: `ps -ef`.
        bsd = "a" in bare and ("u" in bare or "x" in bare)
        sysv = "e" in flags and "f" in flags
        full = bsd or sysv or "a" in bare

        user = self.ctx.username
        session = [
            (user, 8021, 601, 21536, 5188, "Ss", "0:00", "-bash"),
            (user, 8090, 8021, 11072, 3364, "R+", "0:00",
             "ps" + (" " + " ".join(self.args) if self.args else "")),
        ]
        procs = _PROCS + session

        # START/STIME come from the emulated boot time so they agree with
        # `uptime`/`who` instead of every process showing 00:00 (all-identical
        # times are themselves a tell the probe suite checks for).
        boot = self.ctx.boot_time or (self.ctx.now() - 4271)
        start = _time.strftime("%H:%M", _time.gmtime(boot))

        if bsd or (full and not sysv):
            self.line(f"{'USER':<10}{'PID':>5} {'%CPU':>5} {'%MEM':>5} "
                      f"{'VSZ':>7} {'RSS':>6} {'TTY':<8} {'STAT':<5}"
                      f"{'START':>5} {'TIME':>6} COMMAND")
            for u, pid, ppid, vsz, rss, stat, cput, cmd in procs:
                tty = "?" if ppid in (0, 1) else "pts/0"
                self.line(f"{u:<10}{pid:>5} {'0.0':>5} {'0.1':>5} "
                          f"{vsz:>7} {rss:>6} {tty:<8} {stat:<5}"
                          f"{start:>5} {cput:>6} {cmd}")
        elif sysv:
            self.line(f"{'UID':<10}{'PID':>5} {'PPID':>7} {'C':>2} STIME TTY "
                      f"         TIME CMD")
            for u, pid, ppid, vsz, rss, stat, cput, cmd in procs:
                tty = "?" if ppid in (0, 1) else "pts/0"
                self.line(f"{u:<10}{pid:>5} {ppid:>7} {'0':>2} {start} "
                          f"{tty:<8} 00:{cput.split(':')[0]:0>2}:{cput.split(':')[1]} {cmd}")
        else:
            self.line("  PID TTY          TIME CMD")
            for u, pid, ppid, vsz, rss, stat, cput, cmd in session:
                short = cmd.split()[0].lstrip("-")
                self.line(f"{pid:>5} pts/0    00:00:00 {short}")
        return 0
