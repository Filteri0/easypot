"""Transport layer: SSH front-end (asyncssh) + shell session loop.

``ShellSession``, ``ServerConfig`` and ``TerminalWriter`` are import-safe
without asyncssh. The asyncssh-dependent pieces are imported lazily so that the
core can be used (and tested) even when asyncssh is not installed.
"""

from honeyshell.transport.config import ServerConfig
from honeyshell.transport.session import INTERRUPT, ShellSession
from honeyshell.transport.terminal import TerminalWriter

__all__ = ["ServerConfig", "ShellSession", "TerminalWriter", "INTERRUPT"]


def __getattr__(name: str):
    # Lazily expose the asyncssh-backed API without hard-importing asyncssh.
    if name in ("start_server", "handle_client", "HoneypotSSHServer"):
        from honeyshell.transport import ssh_server

        return getattr(ssh_server, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
