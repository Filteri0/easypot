"""id — print user/group identity.

Split out of the former ``sysinfo.py``; behaviour unchanged.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Id"]


@register("id", "/usr/bin/id")
class Id(Command):
    """Print user/group identity."""

    async def run(self) -> int:
        uid = self.ctx.uid
        user = self.ctx.username
        if uid == 0:
            self.line("uid=0(root) gid=0(root) groups=0(root)")
        else:
            self.line(
                f"uid={uid}({user}) gid={uid}({user}) "
                f"groups={uid}({user})"
            )
        return 0
