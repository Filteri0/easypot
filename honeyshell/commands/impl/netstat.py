"""netstat — show network connections and listening ports.

Listening sockets are derived from the SystemProfile's ``open_ports`` so the
output agrees with the advertised services (a real box's netstat matches what's
actually listening). A couple of established connections are added for realism.
Supports the common ``-t``/``-u``/``-l``/``-n``/``-a``/``-p`` flag soup;
unknown flags are ignored.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._sysprofile import _profile

__all__ = ["Netstat"]

# A couple of believable established connections (proto, local, remote).
_ESTABLISHED = [
    ("tcp", "10.0.0.24:22", "10.0.0.9:52344"),
]


@register("netstat", "/bin/netstat", "/usr/bin/netstat")
class Netstat(Command):
    async def run(self) -> int:
        p = _profile(self.ctx)
        flags = {c for a in self.args if a.startswith("-") and a != "-"
                 for c in a[1:]}
        # Default to showing listening + established when no selector given.
        show_all = "a" in flags or not (flags - {"n", "p", "t", "u"})

        self.line("Active Internet connections (servers and established)")
        self.line(f"{'Proto':<6}{'Recv-Q':>7}{'Send-Q':>7} "
                  f"{'Local Address':<22}{'Foreign Address':<22}State")
        for port in p.open_ports:
            self.line(f"{'tcp':<6}{0:>7}{0:>7} "
                      f"{'0.0.0.0:' + str(port):<22}{'0.0.0.0:*':<22}LISTEN")
        if show_all:
            # Show the attacker's OWN ssh connection — they expect to see it.
            # Fall back to a plausible pair only if the peer is unknown.
            src_ip = getattr(self.ctx, "src_ip", None)
            src_port = getattr(self.ctx, "src_port", None)
            local_ip = "10.0.0.24"
            if src_ip:
                remote = f"{src_ip}:{src_port or 52344}"
                local = f"{local_ip}:22"
                self.line(f"{'tcp':<6}{0:>7}{0:>7} "
                          f"{local:<22}{remote:<22}ESTABLISHED")
            else:
                for proto, local, remote in _ESTABLISHED:
                    self.line(f"{proto:<6}{0:>7}{0:>7} "
                              f"{local:<22}{remote:<22}ESTABLISHED")
        return 0
