"""Filesystem-mutating builtins: mkdir, rmdir, rm, touch, mv, cp.

Why these are builtins (not LLM)
--------------------------------
The paper's hybrid design (§3.4) keeps rule-following, deterministic commands on
the cheap emulated path and sends only novel/interactive work to the model. More
importantly for a shell honeypot, these commands *change state*: if ``mkdir x``
were answered by the LLM, the VFS wouldn't actually gain ``x`` and the next
``ls`` would expose the lie. So they run here and mutate the single source of
truth — the VirtualFS — exactly like a real system, keeping the session
self-consistent across turns.

Scope
-----
Common flags real attackers use are supported (``mkdir -p``, ``rm -r/-f``,
``cp -r``); exotic flags are ignored rather than erroring, which is closer to
GNU behaviour for unknown-but-harmless options than a hard failure. Permission
checks are not enforced (the VFS stores perms but doesn't police them yet), so
as root everything succeeds — matching a honeypot that wants to keep attackers
engaged.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import (
    DirectoryNotEmpty,
    FileExists,
    FSError,
    IsADirectory,
    NoSuchFile,
    NotADirectory,
)


def _split_flags(args: list[str]) -> tuple[set[str], list[str]]:
    """Partition argv tail into a set of flag chars and positional operands.

    ``-rf`` becomes {'r','f'}; ``--`` stops flag parsing; a bare ``-`` is an
    operand. Long options (``--recursive``) are recorded by their full text.
    """
    flags: set[str] = set()
    operands: list[str] = []
    no_more = False
    for a in args:
        if no_more or not a.startswith("-") or a == "-":
            operands.append(a)
        elif a == "--":
            no_more = True
        elif a.startswith("--"):
            flags.add(a[2:])
        else:
            flags.update(a[1:])
    return flags, operands


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


@register("mv", "/bin/mv")
class Mv(Command):
    """Move/rename. Last operand is the destination."""

    async def run(self) -> int:
        _, operands = _split_flags(self.args)
        if len(operands) < 2:
            return self.fail("missing destination file operand" if operands
                             else "missing file operand")
        *srcs, dst = operands
        rc = 0
        for src in srcs:
            try:
                self.ctx.fs.move(src, dst, self.ctx.cwd)
            except NoSuchFile:
                rc = self.fail(
                    f"cannot stat '{src}': No such file or directory"
                )
            except FSError as e:
                rc = self.fail(f"cannot move '{src}': {e.message}")
        return rc


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
        # If dst is an existing directory, copy *into* it under src's basename.
        dst_path = dst
        if fs.exists(dst, cwd) and fs.stat(dst, cwd).is_dir:
            base = src.rstrip("/").rsplit("/", 1)[-1]
            dst_path = dst.rstrip("/") + "/" + base
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
