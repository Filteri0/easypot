"""ifconfig — show network interface configuration.

Static but believable: a primary ethernet interface with a private IP plus the
loopback. The honeypot has no real NICs, so a stable, plausible layout is the
smallest tell. The IP is deterministic so it agrees across calls.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._netinfo import ETH_IP as _ETH_IP
from honeyshell.commands.impl._netinfo import ETH_MAC as _ETH_MAC

__all__ = ["Ifconfig"]


@register("ifconfig", "/sbin/ifconfig", "/usr/sbin/ifconfig")
class Ifconfig(Command):
    async def run(self) -> int:
        self.line(
            "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500"
        )
        self.line(
            f"        inet {_ETH_IP}  netmask 255.255.255.0  "
            f"broadcast 10.0.0.255"
        )
        self.line(f"        ether {_ETH_MAC}  txqueuelen 1000  (Ethernet)")
        self.line("        RX packets 158432  bytes 210394821 (200.6 MiB)")
        self.line("        TX packets 98211  bytes 12834004 (12.2 MiB)")
        self.line("")
        self.line("lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536")
        self.line("        inet 127.0.0.1  netmask 255.0.0.0")
        self.line("        loop  txqueuelen 1000  (Local Loopback)")
        self.line("        RX packets 240  bytes 20112 (19.6 KiB)")
        self.line("        TX packets 240  bytes 20112 (19.6 KiB)")
        return 0
