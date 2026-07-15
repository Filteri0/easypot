"""head — print the first N lines (default 10) of each input.

Split out of the former ``textutil.py``; behaviour unchanged. Reads file
operands or stdin (via the shared ``_FileOrStdin`` base) so it composes in
pipelines.
"""

from __future__ import annotations

from honeyshell.commands.registry import register
from honeyshell.commands.impl._fileorstdin import _FileOrStdin, _int_flag

__all__ = ["Head"]


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
