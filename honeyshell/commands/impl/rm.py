"""rm — remove files (and dirs with ``-r``); ``-f`` silences missing-file errors.

Split out of the former ``filesystem.py``; behaviour unchanged. Mutates the
VirtualFS, so it stays a builtin.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fsflags import _split_flags, parent_writable
from honeyshell.fs import FSError, NoSuchFile

__all__ = ["Rm"]


@register("rm", "/bin/rm")
class Rm(Command):
    """Remove files (and dirs with ``-r``). ``-f`` silences missing-file errors."""

    async def run(self) -> int:
        flags, operands = _split_flags(self.args)
        recursive = bool({"r", "R", "recursive"} & flags)
        force = "f" in flags or "force" in flags
        if not operands and not force:
            return self.fail("missing operand")
        rc = 0
        for path in operands:
            try:
                st = self.ctx.fs.stat(path, self.ctx.cwd)
                if st.is_dir and not recursive:
                    rc = self.fail(f"cannot remove '{path}': Is a directory")
                    continue
                # Removing a name needs write on its PARENT directory (Unix
                # deletes the directory entry, not the file). `rm -f` does not
                # bypass permissions — it only silences missing-file errors.
                if not parent_writable(self.ctx, path):
                    if not force:
                        rc = self.fail(
                            f"cannot remove '{path}': Permission denied")
                    continue
                self.ctx.fs.remove(path, self.ctx.cwd, recursive=recursive)
            except NoSuchFile:
                if not force:
                    rc = self.fail(
                        f"cannot remove '{path}': No such file or directory"
                    )
            except FSError as e:
                if not force:
                    rc = self.fail(f"cannot remove '{path}': {e.message}")
        return rc
