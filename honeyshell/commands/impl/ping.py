"""ping — send ICMP echo requests (simulated).

Why a builtin: ping's output shape is rigid and its per-reply timings must look
internally consistent (rtt min/avg/max within the per-line times). An LLM tends
to produce contradictory numbers; a small deterministic generator is both
cheaper and more convincing. A real box always has ping — its absence is a tell.

The honeypot never touches the network, so this is pure theatre: we synthesise
successful replies to whatever host was given. Like the existing `sleep`, we do
NOT actually wait between packets (no real 1s spacing) — blocking the session
buys nothing and risks hanging non-interactive callers. ``-c N`` bounds the
count (default 4); without it we still emit a small fixed number rather than
looping forever, since we can't interpret a Ctrl-C mid-command here.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Ping"]

# Deterministic per-sequence rtt values (ms) so summary min/avg/max are exact.
_RTTS = [11.4, 10.9, 11.7, 10.8, 11.2, 11.0, 12.1, 10.5]


@register("ping", "/bin/ping", "/usr/bin/ping")
class Ping(Command):
    async def run(self) -> int:
        count = 4
        host = None
        args = self.args
        i = 0
        while i < len(args):
            a = args[i]
            if a == "-c" and i + 1 < len(args):
                try:
                    count = max(1, int(args[i + 1]))
                except ValueError:
                    pass
                i += 2
                continue
            if a.startswith("-c") and len(a) > 2:
                try:
                    count = max(1, int(a[2:]))
                except ValueError:
                    pass
                i += 1
                continue
            if a.startswith("-"):
                i += 1  # ignore other flags (-i, -W, -s, ...)
                continue
            if host is None:
                host = a
            i += 1

        if host is None:
            self.errline("ping: usage error: Destination address required")
            return 2

        # Cap simulated packets so we never emit an unbounded stream.
        count = min(count, 20)
        # A plausible resolved address for a hostname (deterministic).
        dst = host if _looks_like_ip(host) else "93.184.216.34"

        self.line(f"PING {host} ({dst}) 56(84) bytes of data.")
        rtts = [_RTTS[i % len(_RTTS)] for i in range(count)]
        for seq, rtt in enumerate(rtts, start=1):
            self.line(f"64 bytes from {dst}: icmp_seq={seq} ttl=115 "
                      f"time={rtt:.1f} ms")
        self.line("")
        self.line(f"--- {host} ping statistics ---")
        self.line(f"{count} packets transmitted, {count} received, "
                  f"0% packet loss, time {count * 1000 - 999}ms")
        mn, mx = min(rtts), max(rtts)
        avg = sum(rtts) / len(rtts)
        mdev = (sum((r - avg) ** 2 for r in rtts) / len(rtts)) ** 0.5
        self.line(f"rtt min/avg/max/mdev = "
                  f"{mn:.3f}/{avg:.3f}/{mx:.3f}/{mdev:.3f} ms")
        return 0


def _looks_like_ip(s: str) -> bool:
    parts = s.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255
                                   for p in parts)
