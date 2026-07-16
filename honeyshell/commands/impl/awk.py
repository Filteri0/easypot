"""awk — pattern scanning and field extraction (common subset).

Design lineage (HANDOFF §28, §32; "做法 B")
-------------------------------------------
``awk`` is the single largest coverage gap in real replayed traffic (2497
misses, the #1 top_miss). Almost every real invocation is the field-extraction
idiom piped in from another command::

    cat /proc/cpuinfo | grep name | awk '{print $4}'
    awk '{print $2 ,$3, $4, $5, $6, $7}'
    ifconfig | awk '{print $2}'

These are deterministic and belong in a builtin (per the §4 hit/miss split):
faking them is trivial and keeps output consistent across a session. What we
deliberately do NOT emulate — patterns (``/re/{...}``), ``BEGIN``/``END``,
arithmetic, ``NR``/``NF`` logic, string functions, assignments, multiple
statements — is rare and better *generated* by the LLM than hand-rolled. For
those the command raises :class:`DeferToLLM`, which the interpreter records as a
genuine miss (hit=False) and routes to the model. This keeps the miss-rate
metric honest (HANDOFF §21/§32): a deferred complex awk counts as a miss, not a
hit, even though a class is registered.

Supported program grammar (everything else defers)
--------------------------------------------------
* A single action block ``{ print ARGS }`` (surrounding/inner whitespace and a
  trailing ``;`` tolerated). No leading pattern, no ``BEGIN``/``END``.
* ARGS: comma-separated items, each either a field reference (``$1`` .. ``$N``,
  ``$0`` whole line, ``$NF`` last field) or a double/single-quoted string
  literal. Bare ``print`` with no args means ``print $0``.
* ``-F SEP`` / ``-FSEP`` sets the field separator (default: runs of
  whitespace, matching awk's default splitting — not a single space).
* Output field separator (OFS) is a single space (awk default); a trailing
  ``;`` in the record is not emulated.

Field semantics match awk: with the default separator, leading/trailing
whitespace is ignored and fields split on whitespace runs. With an explicit
``-F`` the line is split on that literal separator (every occurrence).

Reads file operands or stdin via :class:`_FileOrStdin`, so it composes in
pipelines. Out-of-range ``$N`` yields empty (awk behaviour), never an error.
"""

from __future__ import annotations

import re

from honeyshell.commands.base import DeferToLLM
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fileorstdin import _FileOrStdin

__all__ = ["Awk"]

# A field ref: $0, $1.., or $NF.
_FIELD_RE = re.compile(r"^\$(?:NF|\d+)$")
# The only program shape we handle: optional space, {, print, args, optional
# ;, }. We capture the args between "print" and the closing brace.
_PRINT_RE = re.compile(r"^\{\s*print\b(?P<args>.*?)\s*;?\s*\}$", re.DOTALL)


def _split_print_args(raw: str) -> list[str] | None:
    """Split a print argument list on top-level commas.

    Commas inside quoted string literals don't separate args. Returns the list
    of trimmed argument tokens, or None if the syntax is something we don't
    model (which triggers a defer). An empty/whitespace ``raw`` -> ``["$0"]``
    (bare ``print``).
    """
    raw = raw.strip()
    if not raw:
        return ["$0"]
    args: list[str] = []
    cur = ""
    quote = None
    for ch in raw:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            cur += ch
            continue
        if ch == ",":
            args.append(cur.strip())
            cur = ""
            continue
        cur += ch
    if quote:  # unterminated string literal -> not our grammar
        return None
    args.append(cur.strip())
    return [a for a in args]


def _is_supported_arg(arg: str) -> bool:
    """A print arg we can emulate: a field ref or a quoted string literal."""
    if _FIELD_RE.match(arg):
        return True
    if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in ("'", '"'):
        return True
    return False


@register("awk", "/usr/bin/awk")
@register("gawk", "/usr/bin/gawk")
class Awk(_FileOrStdin):
    async def run(self) -> int:
        sep = None  # None => default whitespace splitting
        program = None
        operands: list[str] = []

        args = self.args
        i = 0
        while i < len(args):
            a = args[i]
            if a == "-F":
                sep = args[i + 1] if i + 1 < len(args) else ""
                i += 2
                continue
            if a.startswith("-F"):
                sep = a[2:]
                i += 1
                continue
            if a.startswith("-") and a != "-":
                # -v, -f progfile, --posix, … : not modelled -> defer.
                raise DeferToLLM
            # First non-flag operand is the program; the rest are files.
            if program is None:
                program = a
                i += 1
                continue
            operands.append(a)
            i += 1

        if program is None:
            # ``awk`` with no program is a usage error in real awk, but that is
            # a rare/degenerate case; hand it to the model rather than guess.
            raise DeferToLLM

        # Decide up front — BEFORE writing any output — whether this program is
        # within our supported grammar. If not, defer cleanly (no partial
        # output, so the interpreter's re-route to the LLM is not double-printed).
        m = _PRINT_RE.match(program.strip())
        if m is None:
            raise DeferToLLM
        parsed = _split_print_args(m.group("args"))
        if parsed is None or not all(_is_supported_arg(a) for a in parsed):
            raise DeferToLLM

        self._parsed_args = parsed
        self._sep = sep

        rc = 0
        async for _, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            for line in text.splitlines():
                self.line(self._render(line, parsed, sep))
        return rc

    def _render(self, line: str, parsed: list[str], sep: str | None) -> str:
        fields = self._fields(line, sep)
        out: list[str] = []
        for arg in parsed:
            if _FIELD_RE.match(arg):
                out.append(self._field_value(arg, line, fields))
            else:  # quoted string literal
                out.append(arg[1:-1])
        return " ".join(out)  # OFS = single space

    @staticmethod
    def _fields(line: str, sep: str | None) -> list[str]:
        if sep is None or sep == "":
            # Default: split on whitespace runs, ignoring leading/trailing.
            return line.split()
        return line.split(sep)

    @staticmethod
    def _field_value(ref: str, line: str, fields: list[str]) -> str:
        if ref == "$0":
            return line
        if ref == "$NF":
            return fields[-1] if fields else ""
        idx = int(ref[1:])
        if idx == 0:
            return line
        return fields[idx - 1] if 1 <= idx <= len(fields) else ""

    async def fallback(self) -> int:
        """No-LLM degrade: echo whole lines (like ``print $0``).

        When a complex awk deferred but there is no model to generate output,
        emitting each input line verbatim is the least suspicious behaviour —
        many attacker awk one-liners are ``print``-shaped and whole-line output
        is a plausible (if imperfect) result, far better than a fabricated
        error that fingerprints the honeypot. Only reached in no-LLM
        deployments; with an LLM the miss_handler runs instead.
        """
        # Re-parse just far enough to find file operands: skip flags, treat the
        # first bare token as the program, the rest as files.
        operands: list[str] = []
        seen_program = False
        i = 0
        args = self.args
        while i < len(args):
            a = args[i]
            if a == "-F":
                i += 2
                continue
            if a.startswith("-") and a != "-":
                i += 1
                continue
            if not seen_program:
                seen_program = True
                i += 1
                continue
            operands.append(a)
            i += 1
        rc = 0
        async for _, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            for line in text.splitlines():
                self.line(line)
        return rc
