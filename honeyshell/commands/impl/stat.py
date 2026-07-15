"""stat — display file or filesystem status.

A commonly-used recon tool; its absence ("stat: command not found") is itself a
tell. Emulates the default GNU ``stat`` layout using VirtualFS metadata and the
emulated clock, so timestamps agree with ``ls -l``/``date``. Sub-second and the
three distinct atime/mtime/ctime values are approximated from the node's single
mtime (the VFS keeps one timestamp), which matches how a lightly-used file
looks in practice.
"""

from __future__ import annotations

import time

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError

__all__ = ["Stat"]


def _fmt(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S.000000000 +0000", time.gmtime(ts))


@register("stat", "/usr/bin/stat")
class Stat(Command):
    async def run(self) -> int:
        operands = [a for a in self.args if not a.startswith("-")]
        if not operands:
            self.errline("stat: missing operand")
            self.errline("Try 'stat --help' for more information.")
            return 1
        rc = 0
        for path in operands:
            try:
                st = self.ctx.fs.stat(path, self.ctx.cwd, follow=False)
            except FSError:
                self.errline(
                    f"stat: cannot statx '{path}': No such file or directory"
                )
                rc = 1
                continue
            self._emit(path, st)
        return rc

    def _emit(self, path: str, st) -> None:
        if st.is_dir:
            kind, ftype = "directory", "d"
        elif st.is_link:
            kind, ftype = "symbolic link", "l"
        else:
            kind, ftype = "regular file", "-"
        perm = st.perm & 0o777
        # rwx string
        bits = ""
        for shift in (6, 3, 0):
            v = (perm >> shift) & 7
            bits += ("r" if v & 4 else "-") + ("w" if v & 2 else "-") \
                + ("x" if v & 1 else "-")
        owner = "root" if st.uid == 0 else self._name(st.uid)
        group = "root" if st.gid == 0 else self._name(st.gid)
        size = st.size
        blocks = ((size + 511) // 512) if size else (8 if st.is_dir else 0)
        # The VFS stores a single mtime. Real files usually show three close but
        # distinct stamps: ctime == mtime (metadata changed when written),
        # atime a little later (last read). Derive plausible values from mtime
        # so `stat` doesn't print three identical timestamps (a tell).
        m = st.mtime
        modify = _fmt(m)
        change = _fmt(m)          # ctime tracks mtime for a write
        access = _fmt(m + 137)    # atime: a couple of minutes later
        self.line(f"  File: {path}"
                  + (f" -> {st.target}" if st.is_link and st.target else ""))
        self.line(f"  Size: {size:<15} Blocks: {blocks:<10} IO Block: 4096   "
                  f"{kind}")
        self.line(f"Device: 802h/2050d\tInode: {abs(hash(path)) % 9000000 + 100000}"
                  f"\tLinks: {2 if st.is_dir else 1}")
        self.line(f"Access: (0{perm:03o}/{ftype}{bits})  "
                  f"Uid: ({st.uid:5d}/{owner:>8})   "
                  f"Gid: ({st.gid:5d}/{group:>8})")
        self.line(f"Access: {access}")
        self.line(f"Modify: {modify}")
        self.line(f"Change: {change}")
        self.line(" Birth: -")

    def _name(self, uid: int) -> str:
        cache = getattr(self, "_uc", None)
        if cache is None:
            cache = {}
            try:
                for ln in self.ctx.fs.readtext("/etc/passwd").splitlines():
                    p = ln.split(":")
                    if len(p) >= 3 and p[2].isdigit():
                        cache[int(p[2])] = p[0]
            except Exception:  # noqa: BLE001
                pass
            self._uc = cache
        return cache.get(uid, str(uid))
