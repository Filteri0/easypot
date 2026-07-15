"""wc — count lines/words/bytes (-l/-w/-c select; default all three).

Split out of the former ``textutil.py``; behaviour unchanged. Reads file
operands or stdin (via the shared ``_FileOrStdin`` base) so it composes in
pipelines.
"""

from __future__ import annotations

from honeyshell.commands.registry import register
from honeyshell.commands.impl._fileorstdin import _FileOrStdin

__all__ = ["Wc"]


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
