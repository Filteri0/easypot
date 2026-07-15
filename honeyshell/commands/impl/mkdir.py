"""mkdir — create directories (``-p`` makes parents, no error if exists).

Split out of the former ``filesystem.py``; behaviour unchanged. A builtin (not
LLM) because it mutates the VirtualFS — the single source of truth — so the next
``ls`` stays consistent with what was just created.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fsflags import _split_flags
from honeyshell.fs import FileExists, NoSuchFile, NotADirectory

__all__ = ["Mkdir"]


@register("mkdir", "/bin/mkdir")
class Mkdir(Command):
    """Create directories. Supports ``-p`` (make parents, no error if exists)."""

    async def run(self) -> int:
        flags, operands = _split_flags(self.args)
        parents = "p" in flags or "parents" in flags
        if not operands:
            return self.fail("missing operand")
        rc = 0
        for path in operands:
            # Need write ('w') on the parent directory to create an entry.
            # Without this a user could `mkdir /root/x` (parent 0700 root) —
            # the exact tell in the demo.
            parent = self.ctx.fs.normalize(path, self.ctx.cwd).rsplit("/", 1)[0] or "/"
            uid = self.ctx.uid
            gid = getattr(self.ctx, "login_uid", None) or uid
            if not self.ctx.fs.access(parent, "w", uid, gid, self.ctx.cwd):
                rc = self.fail(
                    f"cannot create directory '{path}': Permission denied"
                )
                continue
            try:
                if parents:
                    self.ctx.fs.makedirs(path, self.ctx.cwd)
                else:
                    self.ctx.fs.mkdir(
                        path, self.ctx.cwd, uid=self.ctx.uid, gid=self.ctx.uid
                    )
            except FileExists:
                if not parents:
                    rc = self.fail(
                        f"cannot create directory '{path}': File exists"
                    )
            except NotADirectory:
                rc = self.fail(f"cannot create directory '{path}': Not a directory")
            except NoSuchFile:
                rc = self.fail(
                    f"cannot create directory '{path}': No such file or directory"
                )
        return rc
