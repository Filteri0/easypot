"""Command substitution — ``$(...)`` and backticks — as a pre-parse pass.

Why a pre-parse pass
--------------------
The parser uses a POSIX lexer that splits on whitespace, so by the time tokens
exist ``$(mktemp -d)`` has already been shredded into ``$(mktemp`` and ``-d)``.
Bash evaluates command substitution *before* word-splitting, so we must too: we
scan the raw line, run each substitution's inner command, splice its output back
in, and only then hand the line to the parser. This is what makes
``cd $(mktemp -d)`` and ``VERSION=$(uname -r)`` behave.

Scope / deferred
----------------
* Handles ``$(...)`` (with nested parentheses) and legacy backticks.
* Output is trimmed of trailing newlines and internal newlines collapse to
  spaces, matching unquoted bash substitution (we can't see quoting here — same
  known limitation the variable expander documents).
* Not handled: process substitution ``<(...)``, arithmetic ``$((...))`` (left to
  the expander/stage B), and quote-aware splitting.
"""

from __future__ import annotations

from typing import Awaitable, Callable

__all__ = ["substitute_commands", "contains_substitution"]

# An async callable that runs a command line and returns its captured stdout.
Runner = Callable[[str], Awaitable[str]]


def contains_substitution(line: str) -> bool:
    """Cheap check so the common (no-substitution) line skips all the work."""
    return "$(" in line or "`" in line


async def substitute_commands(line: str, runner: Runner) -> str:
    """Return ``line`` with every ``$(...)`` / ``` `...` ``` replaced by output.

    Substitutions are resolved left to right; a nested ``$(a $(b))`` resolves
    inner-first because we recurse on the captured segment before running it.
    """
    if not contains_substitution(line):
        return line
    out = []
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c == "$" and i + 1 < n and line[i + 1] == "(":
            inner, j = _read_paren(line, i + 2)
            if j == -1:  # unbalanced: leave the rest literal
                out.append(line[i:])
                break
            resolved = await substitute_commands(inner, runner)  # inner-first
            out.append(_clean(await runner(resolved)))
            i = j
            continue
        if c == "`":
            inner, j = _read_backtick(line, i + 1)
            if j == -1:
                out.append(line[i:])
                break
            resolved = await substitute_commands(inner, runner)
            out.append(_clean(await runner(resolved)))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _read_paren(s: str, start: int) -> tuple[str, int]:
    """Read until the matching ``)``. Returns (inner, index_after_close).

    Tracks nesting so ``$(echo $(date))`` reads the whole inner expression.
    Returns ("", -1) if unbalanced.
    """
    depth = 1
    i = start
    while i < len(s):
        ch = s[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return s[start:i], i + 1
        i += 1
    return "", -1


def _read_backtick(s: str, start: int) -> tuple[str, int]:
    """Read until the closing backtick. Returns (inner, index_after_close)."""
    i = start
    while i < len(s):
        if s[i] == "`":
            return s[start:i], i + 1
        i += 1
    return "", -1


def _clean(output: str) -> str:
    """Trim trailing newlines and collapse internal newlines to spaces.

    Mirrors unquoted bash command substitution, which strips trailing newlines
    and splits the rest on whitespace (we approximate by turning newlines into
    single spaces so the parser then word-splits normally).
    """
    stripped = output.strip("\n")
    return " ".join(stripped.split("\n"))
