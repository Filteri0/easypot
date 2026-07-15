"""uname — print system information (-s/-n/-r/-m/-o/-a and combos).

Split out of the former ``sysinfo.py``; behaviour unchanged. Deterministic query
answered from the honeypot's configured SystemProfile so fingerprinting stays
consistent with the advertised machine — hence a builtin, not LLM.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._sysprofile import _profile

__all__ = ["Uname"]


@register("uname", "/bin/uname")
class Uname(Command):
    """Print system information. Supports -s/-n/-r/-m/-o/-a (and combos)."""

    _KERNEL_NAME = "Linux"

    async def run(self) -> int:
        p = _profile(self.ctx)
        flags = "".join(a[1:] for a in self.args if a.startswith("-") and a != "-")
        long_opts = [a for a in self.args if a.startswith("--")]

        if "a" in flags or "--all" in long_opts:
            # -a order: kernel-name nodename kernel-release kernel-version
            #           machine operating-system
            self.line(
                f"{self._KERNEL_NAME} {p.hostname} {p.kernel} "
                f"#1 SMP Debian {p.kernel} {p.architecture} GNU/Linux"
            )
            return 0

        parts: list[str] = []
        if not flags and not long_opts:
            flags = "s"  # default: kernel name
        if "s" in flags:
            parts.append(self._KERNEL_NAME)
        if "n" in flags:
            parts.append(p.hostname)
        if "r" in flags:
            parts.append(p.kernel)
        if "v" in flags:
            parts.append(f"#1 SMP Debian {p.kernel}")
        if "m" in flags or "p" in flags or "i" in flags:
            parts.append(p.architecture)
        if "o" in flags:
            parts.append("GNU/Linux")
        self.line(" ".join(parts) if parts else self._KERNEL_NAME)
        return 0
