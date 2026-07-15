"""env — print the environment.

Split out of the former ``sysinfo.py``; behaviour unchanged. (Running a command
via env is not supported.)
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Env"]


@register("env", "/usr/bin/env")
class Env(Command):
    """Print the environment. (Running a command via env is not supported.)"""

    async def run(self) -> int:
        for k, v in self.ctx.environ.items():
            self.line(f"{k}={v}")
        return 0
