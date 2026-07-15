"""cd — change the shell's working directory.

Split out of the former ``basic.py`` starter set; behaviour unchanged. Mutates
``ctx.cwd`` (shell state), so it stays a builtin rather than going to the LLM.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError

__all__ = ["Cd"]


@register("cd")
class Cd(Command):
    async def run(self) -> int:
        target = self.args[0] if self.args else self.ctx.home
        try:
            st = self.ctx.fs.stat(target, self.ctx.cwd)
        except FSError as e:
            return self.fail(f"{target}: {e.message}")
        if not st.is_dir:
            return self.fail(f"{target}: Not a directory")
        # A real shell needs execute ('x') permission on a directory to enter
        # it. Without this a normal user could `cd /root` (perm 0700, owned by
        # root) — an obvious "no permission model" tell.
        uid = self.ctx.uid
        gid = getattr(self.ctx, "login_uid", None) or uid
        if not self.ctx.fs.access(target, "x", uid, gid, self.ctx.cwd):
            return self.fail(f"{target}: Permission denied")
        self.ctx.cwd = self.ctx.fs.normalize(target, self.ctx.cwd)
        return 0
