"""cut — remove sections from each line.

Supports the two common forms: ``-f LIST`` with ``-d DELIM`` (fields) and
``-c LIST`` (characters). LIST is a comma/range spec like ``1,3`` or ``2-4`` or
``2-``. Reads file operands or stdin via _FileOrStdin so it works in pipelines
(``cat /etc/passwd | cut -d: -f1``).

Deferred: ``--complement``, ``-b`` byte mode (treated as ``-c``), output delim.
"""

from __future__ import annotations

from honeyshell.commands.registry import register
from honeyshell.commands.impl._fileorstdin import _FileOrStdin

__all__ = ["Cut"]


def _parse_list(spec: str) -> list[tuple[int, int]]:
    """Parse ``1,3,5-7`` into inclusive 1-based (start, end) ranges.

    An open end like ``3-`` yields (3, -1) meaning "to end of line".
    """
    ranges = []
    for part in spec.split(","):
        if "-" in part:
            a, _, b = part.partition("-")
            start = int(a) if a else 1
            end = int(b) if b else -1
            ranges.append((start, end))
        elif part:
            ranges.append((int(part), int(part)))
    return ranges


def _select(items: list[str], ranges: list[tuple[int, int]]) -> list[str]:
    out = []
    n = len(items)
    for start, end in ranges:
        real_end = n if end == -1 else min(end, n)
        for i in range(start, real_end + 1):
            if 1 <= i <= n:
                out.append(items[i - 1])
    return out


@register("cut", "/usr/bin/cut")
class Cut(_FileOrStdin):
    async def run(self) -> int:
        delim = "\t"
        list_spec = None
        mode = None  # 'f' or 'c'
        operands: list[str] = []

        args = self.args
        i = 0
        while i < len(args):
            a = args[i]
            if a.startswith("-d"):
                delim = a[2:] if len(a) > 2 else (args[i + 1] if i + 1 < len(args) else "\t")
                i += 1 if len(a) > 2 else 2
                continue
            if a.startswith("-f"):
                mode = "f"
                list_spec = a[2:] if len(a) > 2 else (args[i + 1] if i + 1 < len(args) else "")
                i += 1 if len(a) > 2 else 2
                continue
            if a.startswith("-c"):
                mode = "c"
                list_spec = a[2:] if len(a) > 2 else (args[i + 1] if i + 1 < len(args) else "")
                i += 1 if len(a) > 2 else 2
                continue
            if a.startswith("-") and a != "-":
                i += 1
                continue
            operands.append(a)
            i += 1

        if not mode or not list_spec:
            return self.fail("you must specify a list of bytes, characters, "
                             "or fields", code=1)
        ranges = _parse_list(list_spec)

        rc = 0
        async for _, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            for line in text.splitlines():
                if mode == "f":
                    # Lines without the delimiter are passed through (GNU).
                    if delim not in line:
                        self.line(line)
                        continue
                    fields = line.split(delim)
                    self.line(delim.join(_select(fields, ranges)))
                else:  # characters
                    chars = list(line)
                    self.line("".join(_select(chars, ranges)))
        return rc
