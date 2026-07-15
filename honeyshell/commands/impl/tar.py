"""tar — archive utility (honeypot subset).

Attackers use tar to unpack payloads and to stage/exfil files. The honeypot has
no real archives, so we emulate the *observable* behaviour and keep the VFS
consistent:

* ``-x`` (extract): we can't know an archive's true contents (it was never
  really downloaded), so we materialise a small, believable extracted tree
  under the current dir and, with ``-v``, list what we "extracted". A later
  ``ls`` then agrees files appeared — the state consistency that avoids a tell.
* ``-c`` (create): writes an archive file into the VFS (placeholder contents)
  so ``-cf out.tar ...`` leaves ``out.tar`` behind.
* ``-t`` (list): prints a plausible member listing.

Flags: combined form ``-xzf`` / ``xzf`` and separate ``-x -z -f a.tar``. The
compression letters (z/j/J) are accepted and ignored.

Deferred: real (de)compression, true member fidelity, ``-C dir``, preserving
modes/owners from the archive.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError

__all__ = ["Tar"]

# A believable extracted layout for `tar -x` when we can't know the real one.
_FAKE_MEMBERS = [
    ("dir", "package"),
    ("file", "package/install.sh"),
    ("file", "package/README"),
    ("file", "package/bin/app"),
]


@register("tar", "/bin/tar", "/usr/bin/tar")
class Tar(Command):
    async def run(self) -> int:
        mode = None          # 'x', 'c', or 't'
        verbose = False
        archive = None

        # Collect flag letters (from -xzf, xzf, or -x -z -f forms) and note that
        # 'f' consumes the next positional as the archive name.
        letters = ""
        positionals: list[str] = []
        expect_file = False
        for a in self.args:
            if expect_file:
                archive = a
                expect_file = False
                continue
            if a.startswith("-") or (a and a[0] in "xctzjJvf" and archive is None
                                     and not positionals):
                stripped = a.lstrip("-")
                if all(c in "xctzjJvf" for c in stripped) and stripped:
                    letters += stripped
                    if "f" in stripped:
                        expect_file = True
                    continue
            positionals.append(a)

        if "x" in letters:
            mode = "x"
        elif "c" in letters:
            mode = "c"
        elif "t" in letters:
            mode = "t"
        verbose = "v" in letters

        if mode is None:
            self.errline("tar: You must specify one of the '-Acdtrux', "
                         "'--delete' or '--test-label' options")
            return 2

        if mode == "x":
            return self._extract(verbose)
        if mode == "t":
            return self._list(verbose)
        return self._create(archive, positionals, verbose)

    def _extract(self, verbose: bool) -> int:
        for kind, rel in _FAKE_MEMBERS:
            path = rel
            try:
                if kind == "dir":
                    self.ctx.fs.makedirs(path, self.ctx.cwd)
                else:
                    parent = path.rsplit("/", 1)[0] if "/" in path else "."
                    if parent != ".":
                        self.ctx.fs.makedirs(parent, self.ctx.cwd)
                    self.ctx.fs.write_file(
                        path, b"", self.ctx.cwd,
                        uid=self.ctx.uid, gid=self.ctx.uid,
                    )
            except FSError:
                pass
            if verbose:
                self.line(rel + ("/" if kind == "dir" else ""))
        return 0

    def _list(self, verbose: bool) -> int:
        for kind, rel in _FAKE_MEMBERS:
            self.line(rel + ("/" if kind == "dir" else ""))
        return 0

    def _create(self, archive, members, verbose) -> int:
        if archive:
            try:
                self.ctx.fs.write_file(
                    archive, b"# tar archive (emulated)\n", self.ctx.cwd,
                    uid=self.ctx.uid, gid=self.ctx.uid,
                )
            except FSError as e:
                self.errline(f"tar: {archive}: Cannot open: {e.message}")
                return 2
        if verbose:
            for m in members:
                self.line(m)
        return 0
