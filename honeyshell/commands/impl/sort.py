"""sort — sort lines of text.

Reads file operands or stdin via the shared _FileOrStdin base so it composes in
pipelines (``cat x | sort | uniq``). Supports ``-r`` (reverse), ``-n``
(numeric), ``-u`` (unique), ``-f`` (fold case). Multiple inputs are concatenated
then sorted, like GNU sort.
"""

from __future__ import annotations

from honeyshell.commands.registry import register
from honeyshell.commands.impl._fileorstdin import _FileOrStdin

__all__ = ["Sort"]


@register("sort", "/usr/bin/sort")
class Sort(_FileOrStdin):
    async def run(self) -> int:
        flags = {c for a in self.args if a.startswith("-") and a != "-"
                 for c in a[1:]}
        operands = [a for a in self.args if not a.startswith("-") or a == "-"]
        reverse = "r" in flags
        numeric = "n" in flags
        unique = "u" in flags
        fold = "f" in flags

        lines: list[str] = []
        rc = 0
        async for _, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            lines.extend(text.splitlines())

        def key(s: str):
            k = s.lower() if fold else s
            if numeric:
                try:
                    return (0, float(s.split()[0]) if s.split() else 0.0)
                except ValueError:
                    return (0, 0.0)
            return (1, k) if numeric else k

        lines.sort(key=key, reverse=reverse)
        if unique:
            seen = set()
            deduped = []
            for ln in lines:
                sig = ln.lower() if fold else ln
                if sig not in seen:
                    seen.add(sig)
                    deduped.append(ln)
            lines = deduped
        for ln in lines:
            self.line(ln)
        return rc
