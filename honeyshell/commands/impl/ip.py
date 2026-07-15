"""ip — show/manipulate routing, devices, addresses (read-only subset).

Handles the read-only forms attackers use for recon: ``ip addr`` / ``ip a``
(interface addresses) and ``ip route`` (default gateway). Other subcommands
return nothing rather than erroring, which is closer to harmless than a hard
failure for a honeypot. Static, consistent with ifconfig.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._netinfo import ETH_IP as _ETH_IP
from honeyshell.commands.impl._netinfo import ETH_MAC as _ETH_MAC
from honeyshell.commands.impl._netinfo import GATEWAY as _GATEWAY

__all__ = ["Ip"]


@register("ip", "/sbin/ip", "/usr/sbin/ip")
class Ip(Command):
    async def run(self) -> int:
        sub = self.args[0] if self.args else ""
        if sub in ("addr", "a", "address"):
            self._addr()
        elif sub in ("route", "r"):
            self._route()
        elif sub in ("link", "l"):
            self._link()
        # unknown subcommand: stay quiet (harmless for a honeypot)
        return 0

    def _addr(self) -> None:
        self.line("1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue "
                  "state UNKNOWN group default qlen 1000")
        self.line("    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00")
        self.line("    inet 127.0.0.1/8 scope host lo")
        self.line("2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc "
                  "fq_codel state UP group default qlen 1000")
        self.line(f"    link/ether {_ETH_MAC} brd ff:ff:ff:ff:ff:ff")
        self.line(f"    inet {_ETH_IP}/24 brd 10.0.0.255 scope global eth0")

    def _route(self) -> None:
        self.line(f"default via {_GATEWAY} dev eth0 proto dhcp metric 100")
        self.line(f"10.0.0.0/24 dev eth0 proto kernel scope link "
                  f"src {_ETH_IP} metric 100")

    def _link(self) -> None:
        self.line("1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue "
                  "state UNKNOWN mode DEFAULT group default qlen 1000")
        self.line("    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00")
        self.line("2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc "
                  "fq_codel state UP mode DEFAULT group default qlen 1000")
        self.line(f"    link/ether {_ETH_MAC} brd ff:ff:ff:ff:ff:ff")
