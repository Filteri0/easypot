"""Command framework: base class, execution context, I/O streams, registry.

Note: importing this package does NOT import the concrete commands. Call
``registry.discover()`` (or ``honeyshell.commands.discover()``) once at startup
to populate the registry from ``commands.impl``.
"""

from honeyshell.commands.base import Command
from honeyshell.commands.context import ShellContext
from honeyshell.commands.registry import (
    all_commands,
    clear,
    discover,
    register,
    resolve,
)
from honeyshell.commands.streams import (
    NullReader,
    Readable,
    StringReader,
    StringWriter,
    Writable,
)

__all__ = [
    "Command",
    "ShellContext",
    "register",
    "resolve",
    "all_commands",
    "clear",
    "discover",
    "Readable",
    "Writable",
    "StringReader",
    "StringWriter",
    "NullReader",
]
