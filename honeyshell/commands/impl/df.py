"""df — report filesystem disk space usage.

Static but believable: a root filesystem plus the usual tmpfs mounts, sizes in
1K-blocks by default and human-readable with ``-h``. The honeypot has no real
block device, so a stable, plausible layout is the smallest tell.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Df"]

# (filesystem, size_kb, used_kb, mount)
_MOUNTS = [
    ("/dev/sda1", 41152636, 8891234, "/"),
    ("tmpfs", 4096000, 0, "/dev/shm"),
    ("tmpfs", 819200, 1024, "/run"),
    ("tmpfs", 5120, 0, "/run/lock"),
]


@register("df", "/bin/df")
class Df(Command):
    async def run(self) -> int:
        human = any(a in ("-h", "--human-readable") for a in self.args)
        if human:
            self.line(f"{'Filesystem':<16}{'Size':>7}{'Used':>7}{'Avail':>7}"
                      f"{'Use%':>5} Mounted on")
        else:
            self.line(f"{'Filesystem':<16}{'1K-blocks':>12}{'Used':>11}"
                      f"{'Available':>11}{'Use%':>5} Mounted on")
        for fs_name, size, used, mount in _MOUNTS:
            avail = size - used
            pct = f"{round(used / size * 100) if size else 0}%"
            if human:
                self.line(f"{fs_name:<16}{_h(size):>7}{_h(used):>7}"
                          f"{_h(avail):>7}{pct:>5} {mount}")
            else:
                self.line(f"{fs_name:<16}{size:>12}{used:>11}{avail:>11}"
                          f"{pct:>5} {mount}")
        return 0


def _h(kb: int) -> str:
    n = kb * 1024.0
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024.0:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}P"
