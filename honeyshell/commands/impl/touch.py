"""touch — create empty files if absent (timestamp update is a no-op here).

Split out of the former ``filesystem.py``; behaviour unchanged. Mutates the
VirtualFS, so it stays a builtin.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fsflags import _split_flags
from honeyshell.fs import FSError, IsADirectory, NoSuchFile, NotADirectory

__all__ = ["Touch"]


@register("touch", "/bin/touch")
class Touch(Command):
    """Create empty files if absent (timestamp update is a no-op here)."""

    async def run(self) -> int:
        _, operands = _split_flags(self.args)
        if not operands:
            return self.fail("missing file operand")
        rc = 0
        for path in operands:
            try:
                self.ctx.fs.touch(path, self.ctx.cwd)
            except NotADirectory:
                rc = self.fail(f"cannot touch '{path}': Not a directory")
            except NoSuchFile:
                rc = self.fail(
                    f"cannot touch '{path}': No such file or directory"
                )
            except IsADirectory:
                pass  # touching an existing dir is fine
            except FSError as e:
                rc = self.fail(f"cannot touch '{path}': {e.message}")
        return rc
