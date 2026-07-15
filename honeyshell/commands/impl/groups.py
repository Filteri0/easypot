"""groups — print the groups the current user belongs to.

Believable membership: root is in the usual admin groups; a normal user gets a
conventional set. Consistent with the id builtin's identity model.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Groups"]


@register("groups", "/usr/bin/groups")
class Groups(Command):
    async def run(self) -> int:
        user = self.args[0] if self.args else self.ctx.username
        if user == "root":
            self.line("root")
        else:
            self.line(f"{user} adm cdrom sudo dip plugdev")
        return 0
