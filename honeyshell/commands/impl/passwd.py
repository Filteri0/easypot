"""passwd — change a user's password (honeypot-style).

Walks the real interaction: prompt for the current password (unless root), then
the new password twice, all with echo off. Every entry is recorded (that's the
intelligence), the confirmations are checked for a mismatch like real passwd,
and the change "succeeds" without storing anything.

Deferred: PAM complexity checks; actually persisting a shadow entry.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._credentials import record_credential

__all__ = ["Passwd"]


@register("passwd", "/usr/bin/passwd")
class Passwd(Command):
    async def run(self) -> int:
        target = self.args[0] if self.args else self.ctx.username
        if self.ctx.read_prompt is None:
            self.errline("passwd: password unchanged")
            return 1

        # Non-root changing their own password must give the current one.
        if self.ctx.username != "root":
            cur = await self.ctx.read_prompt("Current password: ", True)
            if cur is None:
                return 1
            record_credential(self.ctx, self.ctx.username, cur)

        new1 = await self.ctx.read_prompt("New password: ", True)
        new2 = await self.ctx.read_prompt("Retype new password: ", True)
        if new1 is None or new2 is None:
            self.errline("passwd: password unchanged")
            return 1
        # Record the attempted new password (intelligence).
        record_credential(self.ctx, target, new1, success=False)
        if new1 != new2:
            self.errline("Sorry, passwords do not match.")
            self.errline("passwd: Authentication token manipulation error")
            self.errline("passwd: password unchanged")
            return 1
        self.line("passwd: password updated successfully")
        return 0
