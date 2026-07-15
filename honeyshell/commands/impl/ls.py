"""ls — list directory contents.

Split out of the former ``basic.py`` starter set; behaviour unchanged. The two
module-level helpers ``_mode_string`` and ``_columnate`` were private to ``ls``
in the old file, so they travel here with it.

Supported: ``-a`` (show dotfiles), ``-l`` (long format), ``-1`` (one per line).
Long format renders a realistic ``drwxr-xr-x`` mode string, owner, size and name
— the detail attackers use to size up a box. Short output mirrors GNU coreutils:
column-major on a tty, one entry per line off a tty (pipes/exec) so downstream
tools parse it reliably.
"""

from __future__ import annotations

import time as _time
from datetime import datetime, timezone

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError

__all__ = ["Ls"]


@register("ls", "/bin/ls")
class Ls(Command):
    async def run(self) -> int:
        show_all = False
        long_fmt = False
        one_per_line = False
        dir_self = False  # -d: list directory itself, not its contents
        operands: list[str] = []
        no_more = False
        for a in self.args:
            if no_more:
                operands.append(a)
            elif a == "--":
                # End of options; everything after is an operand (GNU getopt).
                no_more = True
            elif a.startswith("--"):
                # Long option. We recognise none of ls's long forms yet, so any
                # ``--foo`` is unrecognised. Reporting it as a long option (not
                # splitting it into '-','-','f'... which produced the bogus
                # ``invalid option -- '-'``) matches GNU coreutils exactly.
                self.errline(f"{self.prog}: unrecognized option '{a}'")
                self.errline(
                    f"Try '{self.prog} --help' for more information."
                )
                return 2
            elif a.startswith("-") and a != "-":
                for ch in a[1:]:
                    if ch == "a":
                        show_all = True
                    elif ch == "l":
                        long_fmt = True
                    elif ch == "1":
                        one_per_line = True
                    elif ch == "d":
                        dir_self = True
                    else:
                        self.errline(f"{self.prog}: invalid option -- '{ch}'")
                        self.errline(
                            f"Try '{self.prog} --help' for more information."
                        )
                        return 2
            else:
                operands.append(a)
        if not operands:
            operands = ["."]

        rc = 0
        multi = len(operands) > 1
        blocks: list[str] = []
        for path in operands:
            try:
                st = self.ctx.fs.stat(path, self.ctx.cwd)
            except FSError as e:
                rc = self.fail(f"cannot access '{path}': {e.message}")
                continue
            if dir_self or not st.is_dir:
                # -d, or a file operand: show the entry itself, not contents.
                if long_fmt:
                    blocks.append(self._long_line(st, path))
                else:
                    blocks.append(path)
                continue
            # Directory listing needs read permission on the directory itself
            # (real ls: "cannot open directory ... Permission denied" for a
            # dir a non-root user lacks r on). access() is the same single
            # judge cat/head/... use; root bypasses.
            uid = self.ctx.uid
            gid = getattr(self.ctx, "login_uid", None)
            gid = gid if gid is not None else uid
            if not self.ctx.fs.access(path, "r", uid, gid, self.ctx.cwd):
                rc = self.fail(
                    f"cannot open directory '{path}': Permission denied")
                continue
            names = self.ctx.fs.listdir(path, self.ctx.cwd)
            if show_all:
                names = [".", ".."] + names
            else:
                names = [n for n in names if not n.startswith(".")]
            if long_fmt:
                body = self._long_block(path, names, show_all)
            else:
                body = self._layout(names, one_per_line)
            blocks.append((f"{path}:\n" if multi else "") + body)
        out = "\n\n".join(b for b in blocks if b != "")
        if out:
            self.line(out)
        return rc

    def _layout(self, names: list[str], one_per_line: bool = False) -> str:
        """Format entry names: column-major grid on a tty, else one per line."""
        if not names:
            return ""
        if one_per_line or not self.ctx.is_tty:
            return "\n".join(names)
        return _columnate(names, self.ctx.term_width)

    def _long_block(self, path: str, names: list[str], show_all: bool) -> str:
        """Render ``ls -l`` lines for a directory's entries."""
        stats = []
        for name in names:
            if name in (".", ".."):
                try:
                    target = path if name == "." else path.rstrip("/") + "/.."
                    st = self.ctx.fs.stat(target, self.ctx.cwd)
                except FSError:
                    continue
            else:
                try:
                    st = self.ctx.fs.stat(f"{path}/{name}", self.ctx.cwd,
                                          follow=False)
                except FSError:
                    continue
            stats.append((name, st))
        # `total` is the sum of 512-byte disk blocks (rounded up per file),
        # reported in 1K units — i.e. what real `ls -l` prints, not a file
        # count. Directories conventionally occupy at least one 4K block.
        blocks_1k = 0
        for _, st in stats:
            sz = st.size if st.size else (4096 if st.is_dir else 0)
            blocks_1k += ((sz + 4095) // 4096) * 4  # 4K alloc -> 4x 1K units
        lines = [f"total {max(blocks_1k, 0)}"]
        for name, st in stats:
            lines.append(self._long_line(st, name, path))
        return "\n".join(lines)

    def _uid_name(self, uid: int) -> str:
        """Resolve a uid to a login name via /etc/passwd (cached per command),
        so `ls -l` shows `deploy` not `1005`. Falls back to the number."""
        cache = getattr(self, "_uid_cache", None)
        if cache is None:
            cache = {}
            try:
                passwd = self.ctx.fs.readtext("/etc/passwd")
                for ln in passwd.splitlines():
                    parts = ln.split(":")
                    if len(parts) >= 3 and parts[2].isdigit():
                        cache[int(parts[2])] = parts[0]
            except Exception:  # noqa: BLE001 — no passwd -> numeric fallback
                pass
            self._uid_cache = cache
        return cache.get(uid, str(uid))

    def _link_count(self, st, name: str, parent_path: str) -> int:
        """Real link count: files -> 1; a dir -> 2 (self + parent) plus one for
        each subdirectory. A hardcoded 1 for directories is a tell."""
        if not st.is_dir:
            return 1
        try:
            full = name if name in (".", "..") else f"{parent_path}/{name}"
            subdirs = 0
            for child in self.ctx.fs.listdir(full, self.ctx.cwd):
                try:
                    cst = self.ctx.fs.stat(f"{full}/{child}", self.ctx.cwd,
                                           follow=False)
                    if cst.is_dir:
                        subdirs += 1
                except FSError:
                    pass
            return 2 + subdirs
        except FSError:
            return 2

    def _long_line(self, st, name: str, parent_path: str = "") -> str:
        """One ``ls -l`` row: mode links owner group size mtime name."""
        mode = _mode_string(st)
        owner = "root" if st.uid == 0 else self._uid_name(st.uid)
        group = "root" if st.gid == 0 else self._uid_name(st.gid)
        display = name
        if st.is_link and st.target:
            display = f"{name} -> {st.target}"
        ref = self.ctx.now() if hasattr(self.ctx, "now") else None
        nlink = self._link_count(st, name, parent_path)
        return (f"{mode} {nlink} {owner:<5} {group:<5} {st.size:>6} "
                f"{_fmt_time(st.mtime, ref)} {display}")


# Reference "now" for the recent/old cutoff in ``ls -l``. Fixed (not wall-clock)
# so output is reproducible and testable; sits just after the fs mtime spread
# (see build_sample_fs, mid-2024). The honeypot is time-shifted anyway, so a
# fixed reference is more consistent than drifting with the real date.
_SIX_MONTHS = 15552000  # 180 days in seconds


def _ref_now() -> float:
    """Reference 'now' for the recent/old cutoff. Wall-clock so that files
    created during the session (stamped with real now) show a clock time,
    while the shipped 2024 tree shows the year — exactly what a real host does
    for old files. Using a fixed reference here would misclassify freshly
    written files as 'old' and print a year for something created seconds ago,
    itself a tell."""
    return _time.time()


def _fmt_time(mtime: float, ref_now: float | None = None) -> str:
    """Format an mtime the way GNU ``ls -l`` does.

    Recent (< ~6 months old, and not in the future): ``"%b %e %H:%M"``.
    Otherwise: ``"%b %e  %Y"`` — GNU shows the year instead of the clock for
    files older than six months. ``%e`` is space-padded day (two columns), so
    both forms line up in the listing.
    """
    dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
    day = f"{dt.day:>2}"  # space-padded, mimics %e
    if ref_now is None:
        ref_now = _ref_now()
    if 0 <= (ref_now - mtime) < _SIX_MONTHS:
        return f"{dt.strftime('%b')} {day} {dt.strftime('%H:%M')}"
    return f"{dt.strftime('%b')} {day}  {dt.strftime('%Y')}"


def _mode_string(st) -> str:
    """Build a 10-char mode string like ``drwxr-xr-x`` from an FSStat."""
    if st.is_dir:
        kind = "d"
    elif st.is_link:
        kind = "l"
    else:
        kind = "-"
    perm = st.perm
    bits = ""
    for shift in (6, 3, 0):
        triad = (perm >> shift) & 0o7
        bits += "r" if triad & 0b100 else "-"
        bits += "w" if triad & 0b010 else "-"
        bits += "x" if triad & 0b001 else "-"
    return kind + bits


def _columnate(names: list[str], width: int, gap: int = 2) -> str:
    """Pack ``names`` into GNU-``ls``-style column-major columns.

    Names run *down* each column before wrapping to the next (column-major
    fill), columns are padded to the widest name they contain plus ``gap``
    spaces. We pick the largest column count whose padded rows still fit in
    ``width``; a single over-wide name degrades to one entry per line.
    """
    longest = max(len(n) for n in names)
    # Upper bound on columns that could possibly fit.
    max_cols = max(1, min(len(names), (width + gap) // (longest + gap)))

    for ncols in range(max_cols, 0, -1):
        nrows = -(-len(names) // ncols)  # ceil division
        # Column-major: column c holds names[c*nrows : (c+1)*nrows].
        col_widths = []
        for c in range(ncols):
            col = names[c * nrows:(c + 1) * nrows]
            col_widths.append(max((len(n) for n in col), default=0))
        total = sum(w + gap for w in col_widths) - gap
        if total <= width or ncols == 1:
            rows = []
            for r in range(nrows):
                cells = []
                for c in range(ncols):
                    idx = c * nrows + r
                    if idx >= len(names):
                        continue
                    name = names[idx]
                    # No trailing pad on the last cell of a row.
                    is_last = (c == ncols - 1) or (c * nrows + nrows + r >= len(names))
                    cells.append(name if is_last else name.ljust(col_widths[c] + gap))
                rows.append("".join(cells).rstrip())
            return "\n".join(rows)
    return "\n".join(names)
