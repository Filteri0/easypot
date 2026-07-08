"""I/O stream abstractions for commands.

Commands never touch the SSH channel directly. They write to a ``Writable``
and read from a ``Readable``. This indirection is what makes pipelines and
redirection possible later: the interpreter simply wires one command's
``stdout`` to the next command's ``stdin``, or to a file buffer, without the
command knowing or caring.

For unit tests (and as the building blocks the pipeline module will reuse),
this module provides concrete in-memory implementations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Writable(Protocol):
    def write(self, data: str) -> None: ...


@runtime_checkable
class Readable(Protocol):
    async def readline(self) -> str | None:
        """Return the next line (including trailing newline), or None at EOF."""
        ...

    async def read(self) -> str:
        """Return all remaining input as a single string."""
        ...


class StringWriter:
    """Collects everything written into an in-memory buffer."""

    def __init__(self) -> None:
        self._parts: list[str] = []

    def write(self, data: str) -> None:
        self._parts.append(data)

    def getvalue(self) -> str:
        return "".join(self._parts)


class StringReader:
    """Serves a fixed string line-by-line, then reports EOF."""

    def __init__(self, text: str = "") -> None:
        self._text = text
        self._pos = 0

    async def readline(self) -> str | None:
        if self._pos >= len(self._text):
            return None
        nl = self._text.find("\n", self._pos)
        if nl == -1:
            line = self._text[self._pos :]
            self._pos = len(self._text)
        else:
            line = self._text[self._pos : nl + 1]
            self._pos = nl + 1
        return line

    async def read(self) -> str:
        rest = self._text[self._pos :]
        self._pos = len(self._text)
        return rest


class NullReader:
    """An always-empty stdin (immediate EOF)."""

    async def readline(self) -> str | None:
        return None

    async def read(self) -> str:
        return ""
