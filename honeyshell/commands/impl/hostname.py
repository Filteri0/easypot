"""hostname — print the system hostname (from the configured profile).

Split out of the former ``sysinfo.py``; behaviour unchanged.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._sysprofile import _profile

__all__ = ["Hostname"]


@register("hostname", "/bin/hostname")
class Hostname(Command):
    """Print the system hostname (from the configured profile)."""

    async def run(self) -> int:
        self.line(_profile(self.ctx).hostname)
        return 0
