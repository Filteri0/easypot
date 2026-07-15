"""rmdir — remove empty directories.

Split out of the former ``filesystem.py``; behaviour unchanged. Mutates the
VirtualFS, so it stays a builtin.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fsflags import _split_flags
from honeyshell.fs import DirectoryNotEmpty, FSError, NoSuchFile

__all__ = ["Rmdir"]


@register("rmdir", "/bin/rmdir")
class Rmdir(Command):
    """Remove empty directories."""

    async def run(self) -> int:
        _, operands = _split_flags(self.args)
        if not operands:
            return self.fail("missing operand")
        rc = 0
        for path in operands:
            try:
                st = self.ctx.fs.stat(path, self.ctx.cwd)
                if not st.is_dir:
                    rc = self.fail(f"failed to remove '{path}': Not a directory")
                    continue
                self.ctx.fs.remove(path, self.ctx.cwd, recursive=False)
            except DirectoryNotEmpty:
                rc = self.fail(f"failed to remove '{path}': Directory not empty")
            except NoSuchFile:
                rc = self.fail(
                    f"failed to remove '{path}': No such file or directory"
                )
            except FSError as e:
                rc = self.fail(f"failed to remove '{path}': {e.message}")
        return rc
