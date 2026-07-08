"""Token expansion: ``$VAR``, ``${VAR}``, ``$?`` and leading ``~``.

Runs *after* the parser has split the line into tokens. Each token is expanded
independently against the :class:`~honeyshell.commands.context.ShellContext`.

Known limitations (documented; rooted in the parser's POSIX lexer)
-----------------------------------------------------------------
The parser uses ``shlex(posix=True)``, which strips quotes and backslash
escapes before the interpreter ever sees a token. Consequently we cannot
distinguish single- from double-quoted text here, so:

* single-quote suppression is NOT honoured — ``'$x'`` expands like ``"$x"``;
* ``\\$`` escaping is NOT honoured.

Fixing either requires the parser to carry per-token quote metadata, which is a
separate refinement. Command substitution ``$(...)`` / backticks is also not
handled yet (it must run before word-splitting, i.e. in a pre-parse pass) and
is the next expansion feature to add.
"""

from __future__ import annotations

from honeyshell.commands.context import ShellContext

__all__ = ["expand_token", "FAKE_PID"]

FAKE_PID = "1417"


def _is_name_start(c: str) -> bool:
    return c.isalpha() or c == "_"


def _is_name_char(c: str) -> bool:
    return c.isalnum() or c == "_"


def _lookup(name: str, ctx: ShellContext, status: int) -> str:
    if name == "?":
        return str(status)
    if name == "$":
        return ctx.environ.get("$", FAKE_PID)
    if name in ("!", "#"):
        return "" if name == "!" else "0"
    return ctx.environ.get(name, "")


def expand_token(tok: str, ctx: ShellContext, status: int = 0) -> str:
    """Expand a single token. Returns the expanded string (may be empty)."""
    if not tok:
        return tok

    # tilde only at the very start of the token
    if tok == "~":
        return ctx.home
    if tok.startswith("~/"):
        tok = ctx.home + tok[1:]

    if "$" not in tok:
        return tok

    out: list[str] = []
    i, n = 0, len(tok)
    while i < n:
        c = tok[i]
        if c != "$":
            out.append(c)
            i += 1
            continue

        nxt = tok[i + 1] if i + 1 < n else ""
        if nxt == "{":
            end = tok.find("}", i + 2)
            if end == -1:  # unmatched brace -> literal '$'
                out.append(c)
                i += 1
                continue
            out.append(_lookup(tok[i + 2 : end], ctx, status))
            i = end + 1
        elif nxt in "?$!#" and nxt != "":
            out.append(_lookup(nxt, ctx, status))
            i += 2
        elif _is_name_start(nxt):
            j = i + 1
            while j < n and _is_name_char(tok[j]):
                j += 1
            out.append(_lookup(tok[i + 1 : j], ctx, status))
            i = j
        else:  # lone '$'
            out.append(c)
            i += 1
    return "".join(out)
