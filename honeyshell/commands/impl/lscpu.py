"""lscpu — display CPU architecture information.

Reads the CPU model, core count and architecture from the SystemProfile so it
agrees with uname/free and the model's advertised machine.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._sysprofile import _profile

__all__ = ["Lscpu"]


@register("lscpu", "/usr/bin/lscpu")
class Lscpu(Command):
    async def run(self) -> int:
        p = _profile(self.ctx)
        cores = p.cpu_count
        rows = [
            ("Architecture:", p.architecture),
            ("CPU op-mode(s):", "32-bit, 64-bit"),
            ("Byte Order:", "Little Endian"),
            ("CPU(s):", str(cores)),
            ("On-line CPU(s) list:", f"0-{cores - 1}" if cores > 1 else "0"),
            ("Thread(s) per core:", "1"),
            ("Core(s) per socket:", str(cores)),
            ("Socket(s):", "1"),
            ("Vendor ID:", "GenuineIntel"),
            ("Model name:", p.cpu_model),
            ("CPU MHz:", "2400.000"),
            ("Hypervisor vendor:", "KVM"),
            ("Virtualization type:", "full"),
        ]
        width = max(len(k) for k, _ in rows)
        for k, v in rows:
            self.line(f"{k:<{width + 2}}{v}")
        return 0
