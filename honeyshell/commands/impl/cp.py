"""cp — copy files (and trees with ``-r``); the last operand is the destination.

Split out of the former ``filesystem.py``; behaviour unchanged. Implemented via
VFS read + write so the copy is an independent node, not an alias. Recursive
copy walks the source directory. Mutates the VirtualFS, so it stays a builtin.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fsflags import (
    _split_flags,
    parent_writable,
    path_readable,
)
from honeyshell.fs import FSError, NoSuchFile

__all__ = ["Cp"]


@register("cp", "/bin/cp")
class Cp(Command):
    """Copy files (and trees with ``-r``). Last operand is the destination.

    Implemented via VFS read + write so the copy is an independent node, not an
    alias. Recursive copy walks the source directory.
    """

    async def run(self) -> int:
        flags, operands = _split_flags(self.args)
        recursive = bool({"r", "R", "recursive"} & flags)
        if len(operands) < 2:
            return self.fail("missing destination file operand" if operands
                             else "missing file operand")
        *srcs, dst = operands
        rc = 0
        for src in srcs:
            try:
                rc = self._copy_one(src, dst, recursive) or rc
            except NoSuchFile:
                rc = self.fail(f"cannot stat '{src}': No such file or directory")
            except FSError as e:
                rc = self.fail(f"cannot copy '{src}': {e.message}")
        return rc

    def _copy_one(self, src: str, dst: str, recursive: bool) -> int:
        fs, cwd = self.ctx.fs, self.ctx.cwd
        st = fs.stat(src, cwd)
        # Reading the source needs read permission on it.
        if not path_readable(self.ctx, src):
            return self.fail(f"cannot open '{src}' for reading: "
                             "Permission denied")
        # If dst is an existing directory, copy *into* it under src's basename.
        dst_path = dst
        if fs.exists(dst, cwd) and fs.stat(dst, cwd).is_dir:
            base = src.rstrip("/").rsplit("/", 1)[-1]
            dst_path = dst.rstrip("/") + "/" + base
        # Writing the destination needs write on its parent directory.
        if not parent_writable(self.ctx, dst_path):
            return self.fail(f"cannot create regular file '{dst_path}': "
                             "Permission denied")
        if st.is_dir:
            if not recursive:
                return self.fail(f"-r not specified; omitting directory '{src}'")
            fs.makedirs(dst_path, cwd)
            for name in fs.listdir(src, cwd):
                self._copy_one(f"{src}/{name}", dst_path, recursive)
            return 0
        data = fs.readbytes(src, cwd)
        fs.write_file(dst_path, data, cwd, uid=self.ctx.uid, gid=self.ctx.uid)
        return 0
