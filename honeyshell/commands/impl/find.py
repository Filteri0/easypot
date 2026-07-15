"""find — search the directory tree.

Walks the VFS recursively from each start path. Supports the options attackers
actually use for recon/staging: ``-name PATTERN`` (glob on basename), ``-type
f|d|l``, and ``-maxdepth N``. Prints matching paths. Unmatched/unknown
predicates are ignored rather than erroring.

Deferred: ``-exec`` (would run commands per match — a big surface), ``-mtime``/
size predicates, ``-o``/``-not`` boolean logic.
"""

from __future__ import annotations

import fnmatch

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError

__all__ = ["Find"]


@register("find", "/usr/bin/find")
class Find(Command):
    async def run(self) -> int:
        starts: list[str] = []
        name_glob = None
        type_filter = None
        maxdepth = None

        args = self.args
        i = 0
        while i < len(args):
            a = args[i]
            if a == "-name" and i + 1 < len(args):
                name_glob = args[i + 1]
                i += 2
                continue
            if a == "-type" and i + 1 < len(args):
                type_filter = args[i + 1]
                i += 2
                continue
            if a == "-maxdepth" and i + 1 < len(args):
                try:
                    maxdepth = int(args[i + 1])
                except ValueError:
                    maxdepth = None
                i += 2
                continue
            if a.startswith("-"):
                i += 2 if i + 1 < len(args) and not args[i + 1].startswith("-") \
                    else 1
                continue
            starts.append(a)
            i += 1

        if not starts:
            starts = ["."]

        rc = 0
        for start in starts:
            try:
                self._walk(start, name_glob, type_filter, maxdepth, 0)
            except FSError:
                self.errline(
                    f"find: '{start}': No such file or directory"
                )
                rc = 1
        return rc

    def _walk(self, path, name_glob, type_filter, maxdepth, depth) -> None:
        st = self.ctx.fs.stat(path, self.ctx.cwd)
        if self._matches(path, st, name_glob, type_filter):
            self.line(path)
        if st.is_dir and (maxdepth is None or depth < maxdepth):
            for name in self.ctx.fs.listdir(path, self.ctx.cwd):
                child = path.rstrip("/") + "/" + name if path != "/" \
                    else "/" + name
                try:
                    self._walk(child, name_glob, type_filter, maxdepth,
                               depth + 1)
                except FSError:
                    continue

    @staticmethod
    def _matches(path, st, name_glob, type_filter) -> bool:
        if name_glob is not None:
            base = path.rstrip("/").rsplit("/", 1)[-1] or "/"
            if not fnmatch.fnmatch(base, name_glob):
                return False
        if type_filter is not None:
            if type_filter == "f" and (st.is_dir or st.is_link):
                return False
            if type_filter == "d" and not st.is_dir:
                return False
            if type_filter == "l" and not st.is_link:
                return False
        return True
