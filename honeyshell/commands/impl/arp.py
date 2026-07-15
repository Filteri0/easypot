"""arp — show the kernel ARP cache.

A small, believable set of neighbours (gateway + a host). Supports the common
``-a`` form. Static: the honeypot has no real ARP table.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Arp"]

# (host_ip, mac)
_NEIGHBOURS = [
    ("10.0.0.1", "52:54:00:00:00:01"),
    ("10.0.0.12", "52:54:00:aa:bb:cc"),
]


@register("arp", "/usr/sbin/arp", "/sbin/arp")
class Arp(Command):
    async def run(self) -> int:
        if any(a == "-a" for a in self.args):
            for ip, mac in _NEIGHBOURS:
                self.line(f"? ({ip}) at {mac} [ether] on eth0")
        else:
            self.line(f"{'Address':<22}{'HWtype':<8}{'HWaddress':<20}"
                      f"{'Flags Mask':<12}Iface")
            for ip, mac in _NEIGHBOURS:
                self.line(f"{ip:<22}{'ether':<8}{mac:<20}{'C':<12}eth0")
        return 0
