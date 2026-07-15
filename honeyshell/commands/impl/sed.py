"""sed — stream editor (substitution subset only).

Intentionally limited: only the ``s/pattern/replacement/[g]`` command, which
covers the overwhelming majority of honeypot traffic. Everything else is a
no-op passthrough rather than a wrong answer — a bogus error (like the real
sed's ``-e expression`` complaints) is a worse tell than quietly copying input.

Supports ``-e SCRIPT`` and a bare script argument, ``-n`` is accepted, the
delimiter after ``s`` may be any char (``s|a|b|``), and the ``g`` flag. Reads
file operands or stdin via _FileOrStdin so it works in pipelines.

Deferred: addresses (``/re/s///``), ``-i`` in-place edit, ``d``/``p``/``y``
commands, regex beyond Python's ``re`` (BRE/ERE nuances).
"""

from __future__ import annotations

import re

from honeyshell.commands.registry import register
from honeyshell.commands.impl._fileorstdin import _FileOrStdin

__all__ = ["Sed"]


def _parse_s(script: str):
    """Parse ``s<d>pat<d>rep<d>[flags]``; return (pattern, repl, global_) or None."""
    script = script.strip()
    if not script.startswith("s") or len(script) < 4:
        return None
    delim = script[1]
    parts = _split_unescaped(script[2:], delim)
    if len(parts) < 2:
        return None
    pattern, repl = parts[0], parts[1]
    flags = parts[2] if len(parts) > 2 else ""
    return pattern, repl, ("g" in flags)


def _split_unescaped(s: str, delim: str) -> list[str]:
    """Split on ``delim`` not preceded by a backslash."""
    out, cur, i = [], [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            cur.append(s[i + 1])
            i += 2
            continue
        if c == delim:
            out.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    out.append("".join(cur))
    return out


@register("sed", "/bin/sed")
class Sed(_FileOrStdin):
    async def run(self) -> int:
        script = None
        operands: list[str] = []
        args = self.args
        i = 0
        while i < len(args):
            a = args[i]
            if a == "-e":
                if i + 1 < len(args):
                    script = args[i + 1]
                    i += 2
                    continue
                i += 1
                continue
            if a == "-n":
                i += 1
                continue
            if a.startswith("-") and a != "-":
                i += 1
                continue
            if script is None:
                script = a
            else:
                operands.append(a)
            i += 1

        parsed = _parse_s(script) if script else None

        rc = 0
        async for _, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            for line in text.splitlines():
                if parsed:
                    pattern, repl, global_ = parsed
                    try:
                        out = re.sub(pattern, repl, line,
                                     count=0 if global_ else 1)
                    except re.error:
                        out = line  # bad regex: pass through, don't error
                    self.line(out)
                else:
                    self.line(line)  # unsupported script: passthrough
        return rc
