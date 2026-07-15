"""Minimal shell-language handling so piped scripts don't spew errors.

Context
-------
The ``sh``/``bash`` builtin runs a script by feeding each line back through the
interpreter. That works for command lists but not for actual shell *language*:
variable assignments, no-op builtins like ``set -e``, and control-flow keywords
(``if``/``for``/…) were each dispatched as if they were commands, producing a
wall of ``command not found`` for any real installer piped into ``sh``.

This module is the "stage A" stop-the-bleeding layer (agreed scope): it does NOT
implement a shell. It recognises three things a line can be, so the interpreter
can handle them before falling through to command dispatch:

1. **Assignment** — ``NAME=value`` (optionally several, ``A=1 B=2``). The value
   is expanded and stored in ``ctx.environ`` so a later ``$NAME`` resolves. This
   is what makes ``DIR=/opt`` + ``mkdir -p "$DIR"`` behave.
2. **No-op builtin** — ``set``, ``export``, ``unset`` (with real effect on
   environ), ``:``, ``umask``, ``shopt``, ``local``/``declare``/``readonly``,
   ``alias``/``trap``/``hash``/``type``/``enable``. These succeed quietly rather
   than erroring. ``export NAME=val`` and ``unset NAME`` mutate environ.
3. **Control keyword** — ``if then else elif fi for while until do done case
   esac function select { }`` and a trailing-``;`` variant. We can't execute the
   block structure (that's stage B), but emitting nothing beats emitting
   ``if: command not found``. The commands *inside* the block still run on their
   own lines, so an installer's real work (mkdir/echo/…) is still observed.

Deferred (stage B): actually evaluating conditionals/loops, heredocs, command
substitution, arithmetic, and ``${VAR:-default}`` style expansions.
"""

from __future__ import annotations

from honeyshell.commands.context import ShellContext

__all__ = [
    "NOOP_BUILTINS",
    "CONTROL_KEYWORDS",
    "is_assignment",
    "apply_assignments",
    "handle_noop_builtin",
    "is_control_noise",
]

# Builtins we accept as successful no-ops (some with a real environ effect).
NOOP_BUILTINS = {
    "set", "export", "unset", ":", "umask", "shopt", "local", "declare",
    "readonly", "alias", "unalias", "trap", "hash", "type", "enable", "eval",
    "builtin", "command", "source", ".", "wait", "times", "ulimit", "bind",
    "complete", "compgen", "caller", "let", "pushd", "popd", "dirs",
}

# Shell control-flow words that must not be treated as commands. Executing the
# block is out of scope (stage B); we just avoid the "command not found" noise.
CONTROL_KEYWORDS = {
    "if", "then", "else", "elif", "fi", "for", "while", "until", "do", "done",
    "case", "esac", "function", "select", "in", "{", "}", "!", "[[", "]]",
    "time", "coproc", "continue", "break", "return", "then;",
}


def _looks_like_name(s: str) -> bool:
    if not s or (not s[0].isalpha() and s[0] != "_"):
        return False
    return all(c.isalnum() or c == "_" for c in s)


def is_assignment(argv: list[str]) -> bool:
    """True if the (unexpanded) argv is one or more leading ``NAME=…`` words
    with no command following — a pure assignment line."""
    if not argv:
        return False
    saw = False
    for tok in argv:
        name, sep, _ = tok.partition("=")
        if sep == "=" and _looks_like_name(name):
            saw = True
            continue
        return False  # a non-assignment word -> not a pure assignment line
    return saw


def apply_assignments(argv: list[str], ctx: ShellContext, expand) -> int:
    """Store ``NAME=value`` pairs into ``ctx.environ``; values are expanded.

    ``expand`` is the interpreter's per-token expander (so ``A=$B`` works).
    Returns 0 (assignments always "succeed" here).
    """
    for tok in argv:
        name, _, raw_val = tok.partition("=")
        ctx.environ[name] = expand(raw_val)
    return 0


def handle_noop_builtin(argv: list[str], ctx: ShellContext, expand):
    """Handle a no-op builtin. Returns an exit status, or None if ``argv[0]``
    isn't one (so the caller continues to normal dispatch).

    ``export NAME=val`` and ``unset NAME`` have a real effect on environ; the
    rest simply succeed.
    """
    if not argv:
        return None
    cmd = argv[0]
    if cmd not in NOOP_BUILTINS:
        return None

    if cmd == "export":
        for tok in argv[1:]:
            if "=" in tok:
                name, _, raw = tok.partition("=")
                if _looks_like_name(name):
                    ctx.environ[name] = expand(raw)
        return 0
    if cmd == "unset":
        for name in argv[1:]:
            ctx.environ.pop(name, None)
        return 0
    # Everything else: quietly succeed.
    return 0


def is_control_noise(argv: list[str]) -> bool:
    """True if the line is (starts with) a control-flow keyword we should
    swallow instead of dispatching as a command."""
    if not argv:
        return False
    first = argv[0]
    # Bare keyword, or keyword with a trailing ';' the lexer kept attached.
    return first in CONTROL_KEYWORDS or first.rstrip(";") in CONTROL_KEYWORDS
