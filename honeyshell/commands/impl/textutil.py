"""Text-processing builtins: head, tail, wc, grep.

All read either file operands or, when given none, standard input — so they
compose in pipelines (``cat x | grep y | wc -l``). Only the common flags are
implemented; the goal is believable coverage of what attackers actually type,
not full GNU parity.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError


def _int_flag(args: list[str], flag: str, default: int) -> tuple[int, list[str]]:
    """Extract ``-N`` count (e.g. ``-n 20`` or ``-n20``) plus a bare ``-20``.

    Returns (count, remaining_operands). Non-numeric or absent -> default.
    """
    count = default
    operands: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == flag:  # "-n" "20"
            if i + 1 < len(args) and args[i + 1].lstrip("-").isdigit():
                count = int(args[i + 1])
                i += 2
                continue
            i += 1
            continue
        if a.startswith(flag) and a[len(flag):].lstrip("-").isdigit():  # "-n20"
            count = int(a[len(flag):])
            i += 1
            continue
        if a.startswith("-") and a != "-" and a[1:].isdigit():  # "-20"
            count = int(a[1:])
            i += 1
            continue
        operands.append(a)
        i += 1
    return count, operands


class _FileOrStdin(Command):
    """Helper base: yield (label, text) for each operand or for stdin."""

    async def _inputs(self, operands: list[str]):
        if not operands:
            yield None, await self.read_all()
            return
        for path in operands:
            try:
                yield path, self.ctx.fs.readtext(path, self.ctx.cwd)
            except FSError as e:
                self.errline(f"{self.prog}: {path}: {e.message}")
                yield path, None


@register("head", "/usr/bin/head")
class Head(_FileOrStdin):
    """Print the first N lines (default 10) of each input."""

    async def run(self) -> int:
        n, operands = _int_flag(self.args, "-n", 10)
        rc = 0
        multi = len(operands) > 1
        first = True
        async for label, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            if multi and label is not None:
                self.write(("" if first else "\n") + f"==> {label} <==\n")
            first = False
            lines = text.splitlines(keepends=True)
            self.write("".join(lines[:max(0, n)]))
        return rc


@register("tail", "/usr/bin/tail")
class Tail(_FileOrStdin):
    """Print the last N lines (default 10) of each input."""

    async def run(self) -> int:
        n, operands = _int_flag(self.args, "-n", 10)
        rc = 0
        multi = len(operands) > 1
        first = True
        async for label, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            if multi and label is not None:
                self.write(("" if first else "\n") + f"==> {label} <==\n")
            first = False
            lines = text.splitlines(keepends=True)
            self.write("".join(lines[-max(0, n):] if n else []))
        return rc


@register("wc", "/usr/bin/wc")
class Wc(_FileOrStdin):
    """Count lines/words/bytes. -l/-w/-c select; default is all three."""

    async def run(self) -> int:
        flags = {c for a in self.args if a.startswith("-") and a != "-"
                 for c in a[1:]}
        operands = [a for a in self.args if not a.startswith("-") or a == "-"]
        show_l = "l" in flags or not flags
        show_w = "w" in flags or not flags
        show_c = "c" in flags or not flags

        rc = 0
        total = [0, 0, 0]
        n_inputs = 0
        async for label, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            n_inputs += 1
            counts = [len(text.splitlines()), len(text.split()),
                      len(text.encode())]
            for i in range(3):
                total[i] += counts[i]
            self.line(self._fmt(counts, show_l, show_w, show_c, label))
        if len(operands) > 1:
            self.line(self._fmt(total, show_l, show_w, show_c, "total"))
        return rc

    @staticmethod
    def _fmt(counts, l, w, c, label):
        cols = []
        if l:
            cols.append(f"{counts[0]:7d}")
        if w:
            cols.append(f"{counts[1]:7d}")
        if c:
            cols.append(f"{counts[2]:7d}")
        line = "".join(cols)
        return f"{line} {label}" if label else line


@register("grep", "/bin/grep")
class Grep(_FileOrStdin):
    """Print lines matching a pattern (plain substring; -i/-v/-n/-c).

    Regex is intentionally not supported yet — plain substring covers the bulk
    of honeypot traffic and avoids surprising ReDoS behaviour. The pattern is
    the first non-flag operand; the rest are files (or stdin if none).
    """

    async def run(self) -> int:
        flags = {c for a in self.args if a.startswith("-") and a != "-"
                 for c in a[1:]}
        rest = [a for a in self.args if not a.startswith("-") or a == "-"]
        if not rest:
            return self.fail("usage: grep PATTERN [FILE...]", code=2)
        pattern, files = rest[0], rest[1:]
        ignore = "i" in flags
        invert = "v" in flags
        number = "n" in flags
        count_only = "c" in flags
        needle = pattern.lower() if ignore else pattern

        rc = 1  # grep returns 1 when no lines matched
        multi = len(files) > 1
        async for label, text in self._inputs(files):
            if text is None:
                continue
            matched = 0
            for idx, line in enumerate(text.splitlines(), 1):
                hay = line.lower() if ignore else line
                hit = needle in hay
                if hit != invert:
                    matched += 1
                    if not count_only:
                        prefix = ""
                        if multi and label is not None:
                            prefix += f"{label}:"
                        if number:
                            prefix += f"{idx}:"
                        self.line(prefix + line)
            if count_only:
                pre = f"{label}:" if multi and label is not None else ""
                self.line(f"{pre}{matched}")
            if matched:
                rc = 0
        return rc
