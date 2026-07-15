"""ps — report a snapshot of current processes.

The honeypot has no real process table, so we synthesise a small, believable
set of system processes plus a shell/ps for the session user. Supports the two
forms attackers use most: bare ``ps`` (few columns) and ``ps aux`` / ``ps -ef``
(full listing). The set is static — enough to look like a real box without
pretending to track the session's own commands (no job control here).

Deferred: reflecting commands the attacker actually ran (would need a process
model); ``-p``/filtering; per-command CPU/MEM realism.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Ps"]

# (user, pid, ppid, cmd)
_PROCS = [
    ("root", 1, 0, "/sbin/init"),
    ("root", 2, 0, "[kthreadd]"),
    ("root", 411, 1, "/lib/systemd/systemd-journald"),
    ("root", 439, 1, "/lib/systemd/systemd-udevd"),
    ("root", 601, 1, "/usr/sbin/sshd -D"),
    ("root", 623, 1, "/usr/sbin/cron -f"),
    ("www-data", 712, 1, "nginx: worker process"),
]


@register("ps", "/bin/ps")
class Ps(Command):
    async def run(self) -> int:
        flags = "".join(a.lstrip("-") for a in self.args if a.startswith("-"))
        bare_words = [a for a in self.args if not a.startswith("-")]
        full = ("e" in flags and "f" in flags) or "aux" in "".join(bare_words) \
            or "a" in "".join(bare_words)

        user = self.ctx.username
        session = [
            (user, 8021, 601, f"-{('bash')}"),
            (user, 8090, 8021, "ps" + (" " + " ".join(self.args) if self.args
                                       else "")),
        ]
        procs = _PROCS + session

        if full:
            self.line(f"{'USER':<9}{'PID':>5} {'PPID':>5} {'C':>2} STIME TTY "
                      f"         TIME CMD")
            for u, pid, ppid, cmd in procs:
                tty = "?" if ppid in (0, 1) else "pts/0"
                self.line(f"{u:<9}{pid:>5} {ppid:>5} {'0':>2} 00:00 "
                          f"{tty:<8}   00:00:00 {cmd}")
        else:
            self.line("  PID TTY          TIME CMD")
            for u, pid, ppid, cmd in session:
                short = cmd.split()[0].lstrip("-")
                self.line(f"{pid:>5} pts/0    00:00:00 {short}")
        return 0
