"""Command registry and discovery.

Borrowed from Cowrie's pattern where each command module fills a ``commands``
dict mapping names (and full paths) to classes, and the protocol scans them at
startup. Here we invert it slightly into a decorator + a discovery pass:

    @register("ls", "/bin/ls")
    class Ls(Command):
        ...

:func:`resolve` looks up the token, falling back to its basename so that both
``ls`` and ``/bin/ls`` map to the same class. This registry is also the exact
seam where a future ``LLMResolver`` slots in: the interpreter asks the registry
first and, on a miss, can hand the token to the LLM backend instead of
printing "command not found".
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Callable

from honeyshell.commands.base import Command

__all__ = [
    "register",
    "resolve",
    "all_commands",
    "clear",
    "discover",
]

_REGISTRY: dict[str, type[Command]] = {}


def register(*names: str) -> Callable[[type[Command]], type[Command]]:
    """Class decorator registering a command under one or more names/paths."""
    if not names:
        raise ValueError("register() requires at least one name")

    def deco(cls: type[Command]) -> type[Command]:
        if not cls.name:
            cls.name = names[0]
        for n in names:
            _REGISTRY[n] = cls
        return cls

    return deco


def resolve(token: str) -> type[Command] | None:
    """Return the command class for ``token``, or None if unknown.

    Tries the exact token first, then its basename (so ``/usr/bin/whoami``
    resolves via the registered ``whoami``).
    """
    cls = _REGISTRY.get(token)
    if cls is not None:
        return cls
    base = token.rsplit("/", 1)[-1]
    return _REGISTRY.get(base)


def all_commands() -> dict[str, type[Command]]:
    """A copy of the full name -> class mapping."""
    return dict(_REGISTRY)


def clear() -> None:
    """Empty the registry (used in tests)."""
    _REGISTRY.clear()


def discover() -> None:
    """Import every module under ``commands.impl`` so their @register runs.

    Idempotent: re-importing already-loaded modules is cheap and simply
    re-registers the same classes.
    """
    from honeyshell.commands import impl

    for mod in pkgutil.iter_modules(impl.__path__):
        importlib.import_module(f"honeyshell.commands.impl.{mod.name}")
