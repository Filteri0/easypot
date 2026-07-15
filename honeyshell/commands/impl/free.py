"""free — display memory usage.

Reads total memory from the SystemProfile so it matches what other fingerprint
commands report; used/free are a plausible split. Supports ``-h`` (human) and
``-m``/``-g`` unit flags; default is kibibytes like GNU free.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._sysprofile import _profile

__all__ = ["Free"]


@register("free", "/usr/bin/free")
class Free(Command):
    async def run(self) -> int:
        total_mb = _profile(self.ctx).memory_mb
        used_mb = int(total_mb * 0.35)
        free_mb = total_mb - used_mb
        shared_mb = int(total_mb * 0.02)
        buff_mb = int(total_mb * 0.20)
        avail_mb = free_mb + buff_mb

        flags = {c for a in self.args if a.startswith("-") and a != "-"
                 for c in a[1:]}
        if "h" in flags:
            fmt = _human
            unit = ""
        elif "g" in flags:
            fmt = lambda mb: str(round(mb / 1024))  # noqa: E731
            unit = ""
        elif "m" in flags:
            fmt = lambda mb: str(mb)  # noqa: E731
            unit = ""
        else:
            fmt = lambda mb: str(mb * 1024)  # noqa: E731 — KiB default
            unit = ""

        swap_total = total_mb
        swap_used = 0
        self.line(
            f"{'':15}{'total':>11}{'used':>11}{'free':>11}"
            f"{'shared':>11}{'buff/cache':>11}{'available':>11}"
        )
        self.line(
            f"{'Mem:':<15}{fmt(total_mb):>11}{fmt(used_mb):>11}"
            f"{fmt(free_mb):>11}{fmt(shared_mb):>11}{fmt(buff_mb):>11}"
            f"{fmt(avail_mb):>11}"
        )
        self.line(
            f"{'Swap:':<15}{fmt(swap_total):>11}{fmt(swap_used):>11}"
            f"{fmt(swap_total):>11}"
        )
        return 0


def _human(mb: int) -> str:
    if mb >= 1024:
        return f"{mb / 1024:.1f}Gi"
    return f"{mb}Mi"
