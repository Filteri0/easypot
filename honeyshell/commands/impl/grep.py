"""grep — print lines matching a pattern (plain substring; -i/-v/-n/-c).

Split out of the former ``textutil.py``; behaviour unchanged. Regex is
intentionally not supported yet — plain substring covers the bulk of honeypot
traffic and avoids surprising ReDoS behaviour. The pattern is the first non-flag
operand; the rest are files (or stdin if none). Reads via the shared
``_FileOrStdin`` base so it composes in pipelines.
"""

from __future__ import annotations

from honeyshell.commands.registry import register
from honeyshell.commands.impl._fileorstdin import _FileOrStdin

__all__ = ["Grep"]


@register("grep", "/bin/grep")
class Grep(_FileOrStdin):
    """Print lines matching a pattern (plain substring; -i/-v/-n/-c)."""

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
