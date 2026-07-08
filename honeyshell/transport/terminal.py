"""Terminal output adapter.

On a PTY, a bare ``\\n`` leaves the cursor in the same column ("staircase"
output); real terminals expect ``\\r\\n``. :class:`TerminalWriter` wraps any
``write(str)`` sink and performs that translation, so command code can keep
emitting plain ``\\n``. Translation is toggleable: off for exec mode / tests
(where we want deterministic ``\\n``), on for interactive PTY sessions.
"""

from __future__ import annotations

from honeyshell.commands.streams import Writable


class TerminalWriter:
    def __init__(self, out: Writable, crlf: bool = True) -> None:
        self._out = out
        self._crlf = crlf

    def write(self, data: str) -> None:
        if self._crlf and data:
            # normalise any existing CRLF first, then expand, so we never
            # produce a doubled \r.
            data = data.replace("\r\n", "\n").replace("\n", "\r\n")
        self._out.write(data)
