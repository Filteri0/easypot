"""Shared credential-capture helper for sudo/su/passwd.

The whole point of making these commands interactive is intelligence: the
passwords an attacker types are valuable. This helper records a captured
credential onto the audit bus as a LoginEvent (the same event type the login
path uses), or silently no-ops when no bus is wired (unit tests, exec mode).

Underscore-prefixed so ``discover()`` imports it without registering a command.
"""

from __future__ import annotations

from honeyshell.commands.context import ShellContext

__all__ = ["record_credential"]


def record_credential(ctx: ShellContext, username: str, password: str,
                      *, success: bool = True) -> None:
    """Emit a LoginEvent for a captured credential, if a bus is wired."""
    bus = ctx.event_bus
    if bus is None:
        return
    # Imported lazily so command modules stay light and core stays optional.
    from honeyshell.core.events import LoginEvent
    bus.emit(LoginEvent(username=username, password=password, success=success))
