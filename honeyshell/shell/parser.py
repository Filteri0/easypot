"""Structural parser for shell command lines.

This module turns a raw command-line string into a structured tree that the
interpreter (a later module) can walk. It is deliberately *stateless* and
*pure*: it performs no variable expansion, no command substitution, and no
filesystem access. Those concerns require session state and belong to the
interpreter — keeping them out here makes the parser trivially unit-testable.

Scope (M2)
----------
Supported:
    * word tokenisation with POSIX quoting/escaping (via ``shlex``)
    * pipelines            ``a | b | c``
    * job separators       ``;``   ``&&``   ``||``
    * background jobs      ``a &``
    * file redirection     ``>``   ``>>``   ``<``

Deliberately deferred (documented, handled in later modules):
    * expansion of ``$VAR`` / ``${VAR}`` / ``$(...)`` / backticks
      -> interpreter, because it needs the session environment.
    * fd-qualified redirects ``2>``, ``2>&1``, ``&>``
      -> a redirection-refinement pass; ``shlex`` discards the whitespace
         information needed to bind a leading fd digit to the operator. For
         now the operator fragment (e.g. ``>&``) is an *unrecognised
         operator-only token* and therefore raises ``ParseError`` — the
         interpreter renders this as a bash-style syntax error. Because such
         redirects are extremely common in attacker traffic, adding real
         support for them is the highest-priority follow-up refinement.
    * subshell / grouping ``( )`` ``{ }``
      -> parens are intentionally *not* treated as operators so that
         ``$(...)`` survives intact as an opaque token for the interpreter.

Grammar produced
----------------
    CommandLine := Job*
    Job         := Pipeline , connector      (connector: ';' '&&' '||' '&' None)
    Pipeline    := SimpleCommand ( '|' SimpleCommand )*  , background
    SimpleCommand := argv[] , redirects[]
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field

__all__ = [
    "CommandLine",
    "Job",
    "ParseError",
    "Pipeline",
    "Redirect",
    "SimpleCommand",
    "parse",
]


class ParseError(Exception):
    """Raised on a structural syntax error, mirroring bash's behaviour.

    The interpreter is expected to catch this and render a bash-like
    ``syntax error near unexpected token`` message to the attacker rather
    than letting it crash the session.
    """


# --- Operator token sets -------------------------------------------------

_REDIR: frozenset[str] = frozenset({">", ">>", "<"})
_CONNECTORS: frozenset[str] = frozenset({";", "&&", "||"})
_ALL_OPS: frozenset[str] = _REDIR | _CONNECTORS | frozenset({"|", "&"})

# Punctuation that shlex should split out as standalone operator tokens.
# Parens are intentionally excluded so command substitution ``$(...)`` stays
# glued together as one word token for the interpreter's expansion stage.
_PUNCTUATION = "&|;<>"

_REDIR_MODE = {">": "w", ">>": "a", "<": "r"}


def _is_operator_like(tok: str) -> bool:
    """True if ``tok`` consists solely of operator punctuation characters.

    Such a token is either a supported operator or a malformed one (``;;``,
    ``>&``, ``|||`` ...). Note: a *quoted* operator string (e.g. ``echo ">&"``)
    also lands here because ``shlex`` strips the quotes — a rare edge we accept
    for M2 in exchange for a simple, single-rule policy.
    """
    return bool(tok) and all(ch in _PUNCTUATION for ch in tok)


# --- AST nodes -----------------------------------------------------------


@dataclass
class Redirect:
    """A single redirection attached to a command, e.g. ``> out.txt``."""

    op: str  # one of '>', '>>', '<'
    target: str

    @property
    def mode(self) -> str:
        """File open mode implied by the operator: 'w', 'a' or 'r'."""
        return _REDIR_MODE[self.op]


@dataclass
class SimpleCommand:
    """A single command: an argv plus its redirections."""

    argv: list[str] = field(default_factory=list)
    redirects: list[Redirect] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.argv or self.redirects)


@dataclass
class Pipeline:
    """One or more commands connected by ``|``, optionally backgrounded."""

    commands: list[SimpleCommand] = field(default_factory=list)
    background: bool = False


@dataclass
class Job:
    """A pipeline together with the connector that *follows* it.

    ``connector`` is ``';'``, ``'&&'``, ``'||'`` or ``'&'`` when another job
    follows, and ``None`` for the final job on the line.
    """

    pipeline: Pipeline
    connector: str | None = None


@dataclass
class CommandLine:
    """The parsed representation of a whole command-line string."""

    jobs: list[Job] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.jobs)


# --- Tokeniser -----------------------------------------------------------


def _tokenize(line: str) -> list[str]:
    lexer = shlex.shlex(line, posix=True, punctuation_chars=_PUNCTUATION)
    lexer.whitespace_split = True
    lexer.commenters = ""  # do not strip '#..' — keep attacker input verbatim
    try:
        return list(lexer)
    except ValueError as exc:  # unbalanced quote / dangling escape
        raise ParseError(str(exc)) from exc


# --- Parser --------------------------------------------------------------


class _Parser:
    """Single-use recursive-descent-ish walker over the token stream."""

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.i = 0
        self.line = CommandLine()
        self.cur = SimpleCommand()
        self.pipe: list[SimpleCommand] = []
        self.need_pipe_rhs = False  # True right after a '|', until an rhs cmd

    # -- helpers --

    def _flush_command(self) -> bool:
        """Push the current command into the pipeline if it is non-empty."""
        if self.cur:
            self.pipe.append(self.cur)
            self.cur = SimpleCommand()
            self.need_pipe_rhs = False
            return True
        return False

    def _flush_pipeline(self, connector: str | None, background: bool) -> None:
        if not self.pipe:
            tok = connector or "&"
            raise ParseError(
                f"syntax error near unexpected token `{tok}'"
            )
        self.line.jobs.append(Job(Pipeline(self.pipe, background), connector))
        self.pipe = []

    def _terminate(self, connector: str | None, background: bool) -> None:
        self._flush_command()
        if self.need_pipe_rhs:
            raise ParseError("syntax error near unexpected token `|'")
        self._flush_pipeline(connector, background)

    def _redirect(self, op: str) -> None:
        nxt = self.i + 1
        if nxt >= len(self.tokens):
            raise ParseError("syntax error near unexpected token `newline'")
        target = self.tokens[nxt]
        if target in _ALL_OPS:
            raise ParseError(f"syntax error near unexpected token `{target}'")
        self.cur.redirects.append(Redirect(op, target))
        self.i += 2

    # -- main loop --

    def parse(self) -> CommandLine:
        n = len(self.tokens)
        while self.i < n:
            tok = self.tokens[self.i]

            if tok in _REDIR:
                self._redirect(tok)
                continue

            if tok == "|":
                if not self._flush_command():
                    raise ParseError("syntax error near unexpected token `|'")
                self.need_pipe_rhs = True
                self.i += 1
                continue

            if tok in _CONNECTORS:
                self._terminate(tok, background=False)
                self.i += 1
                continue

            if tok == "&":
                self._terminate("&", background=True)
                self.i += 1
                continue

            # An operator-only token we did not recognise above is malformed
            # (';;', '|||') or a deferred fd-redirect fragment ('>&', '&>').
            if _is_operator_like(tok):
                raise ParseError(
                    f"syntax error near unexpected token `{tok}'"
                )

            # ordinary word
            self.cur.argv.append(tok)
            self.i += 1

        # end of input: flush any trailing command/pipeline
        self._flush_command()
        if self.need_pipe_rhs:
            raise ParseError("syntax error near unexpected token `newline'")
        if self.pipe:
            self.line.jobs.append(Job(Pipeline(self.pipe, False), None))

        self._check_trailing()
        return self.line

    def _check_trailing(self) -> None:
        # bash accepts a trailing ';' or '&' but errors on trailing '&&'/'||'.
        if self.line.jobs and self.line.jobs[-1].connector in ("&&", "||"):
            raise ParseError("syntax error near unexpected token `newline'")


def parse(line: str) -> CommandLine:
    """Parse ``line`` into a :class:`CommandLine`.

    Returns an empty ``CommandLine`` for blank input. Raises
    :class:`ParseError` on structural syntax errors or unbalanced quotes.
    """
    return _Parser(_tokenize(line)).parse()
