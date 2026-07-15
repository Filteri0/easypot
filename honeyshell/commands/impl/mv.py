"""mv — move/rename; the last operand is the destination.

Split out of the former ``filesystem.py``; behaviour unchanged. Mutates the
VirtualFS, so it stays a builtin.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fsflags import _split_flags, parent_writable
from honeyshell.fs import FSError, NoSuchFile

__all__ = ["Mv"]


@register("mv", "/bin/mv")
class Mv(Command):
    """Move/rename. Last operand is the destination."""

    async def run(self) -> int:
        _, operands = _split_flags(self.args)
        if len(operands) < 2:
            return self.fail("missing destination file operand" if operands
                             else "missing file operand")
        *srcs, dst = operands
        fs, cwd = self.ctx.fs, self.ctx.cwd
        rc = 0
        for src in srcs:
            try:
                # Moving a name out of its source dir needs write on that dir;
                # creating the name in the destination dir needs write there.
                # Resolve the into-directory case so the parent check targets
                # the real final path (mv f dir/ -> dir/f).
                dst_path = dst
                if fs.exists(dst, cwd) and fs.stat(dst, cwd).is_dir:
                    base = src.rstrip("/").rsplit("/", 1)[-1]
                    dst_path = dst.rstrip("/") + "/" + base
                if not parent_writable(self.ctx, src):
                    rc = self.fail(f"cannot move '{src}': Permission denied")
                    continue
                if not parent_writable(self.ctx, dst_path):
                    rc = self.fail(f"cannot move '{src}' to '{dst_path}': "
                                   "Permission denied")
                    continue
                self.ctx.fs.move(src, dst, self.ctx.cwd)
            except NoSuchFile:
                rc = self.fail(
                    f"cannot stat '{src}': No such file or directory"
                )
            except FSError as e:
                rc = self.fail(f"cannot move '{src}': {e.message}")
        return rc
