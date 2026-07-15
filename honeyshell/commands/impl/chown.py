"""chown — change file owner and group.

Really mutates the VFS via ``fs.chown``. Accepts ``owner``, ``owner:group`` and
``:group`` forms. Owner/group names are mapped to conventional uids (root->0,
anything else->1000) since the honeypot has a minimal user database. ``-R``
recurses.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fsflags import _split_flags
from honeyshell.fs import FSError, NoSuchFile

__all__ = ["Chown"]


def _name_to_id(name: str) -> int:
    if not name:
        return -1
    if name == "root" or name == "0":
        return 0
    if name.isdigit():
        return int(name)
    return 1000  # conventional non-root id for any named user


@register("chown", "/bin/chown")
class Chown(Command):
    async def run(self) -> int:
        flags, operands = _split_flags(self.args)
        recursive = bool({"R", "recursive"} & flags)
        if len(operands) < 2:
            return self.fail("missing operand")
        spec, paths = operands[0], operands[1:]
        owner, _, group = spec.partition(":")
        uid = _name_to_id(owner) if owner else None
        gid = _name_to_id(group) if group else None
        rc = 0
        for path in paths:
            try:
                self._apply(path, uid, gid, recursive)
            except NoSuchFile:
                rc = self.fail(
                    f"cannot access '{path}': No such file or directory"
                )
            except FSError as e:
                rc = self.fail(f"changing ownership of '{path}': {e.message}")
        return rc

    def _apply(self, path, uid, gid, recursive):
        self.ctx.fs.chown(
            path, self.ctx.cwd,
            uid=uid if uid is not None and uid >= 0 else None,
            gid=gid if gid is not None and gid >= 0 else None,
        )
        if recursive and self.ctx.fs.stat(path, self.ctx.cwd).is_dir:
            for name in self.ctx.fs.listdir(path, self.ctx.cwd):
                self._apply(f"{path}/{name}", uid, gid, recursive)
