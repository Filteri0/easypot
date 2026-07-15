"""lspci — list PCI devices.

Static, believable virtualised hardware. If the SystemProfile advertises a GPU
(a crypto-miner lure per the paper §3.3.2), it's shown as a VGA device so the
recon matches the advertised machine.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._sysprofile import _profile

__all__ = ["Lspci"]

_BASE = [
    "00:00.0 Host bridge: Intel Corporation 440FX - 82441FX PMC [Natoma] (rev 02)",
    "00:01.0 ISA bridge: Intel Corporation 82371SB PIIX3 ISA [Natoma/Triton II]",
    "00:01.1 IDE interface: Intel Corporation 82371SB PIIX3 IDE [Natoma/Triton II]",
    "00:02.0 VGA compatible controller: Cirrus Logic GD 5446",
    "00:03.0 Ethernet controller: Red Hat, Inc. Virtio network device",
    "00:04.0 SCSI storage controller: Red Hat, Inc. Virtio block device",
]


@register("lspci", "/usr/bin/lspci", "/sbin/lspci")
class Lspci(Command):
    async def run(self) -> int:
        for line in _BASE:
            self.line(line)
        gpu = _profile(self.ctx).gpu
        if gpu:
            self.line(f"01:00.0 VGA compatible controller: {gpu}")
        return 0
