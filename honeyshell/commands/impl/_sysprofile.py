"""Shared SystemProfile accessor for system-info builtins.

Extracted from the former ``sysinfo.py`` where ``_profile`` was shared by uname
and hostname. Underscore-prefixed so ``discover()`` imports it harmlessly (it
registers nothing). Behaviour unchanged.
"""

from __future__ import annotations

from honeyshell.commands.context import ShellContext
from honeyshell.core.config import SystemProfile

__all__ = ["_profile"]


def _profile(ctx: ShellContext) -> SystemProfile:
    """The configured profile, or a default one so commands still work."""
    return ctx.system or SystemProfile(hostname=ctx.hostname)
