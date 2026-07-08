"""asyncssh glue: authentication, process handling, and server bootstrap.

This is the only module that imports asyncssh. Everything shell-related lives
behind :class:`~honeyshell.transport.session.ShellSession`, which this module
merely adapts asyncssh streams onto.
"""

from __future__ import annotations

import functools
import os

import asyncssh

from honeyshell.transport.config import ServerConfig
from honeyshell.transport.session import ShellSession
from honeyshell.transport.terminal import TerminalWriter

__all__ = ["HoneypotSSHServer", "handle_client", "start_server"]


class HoneypotSSHServer(asyncssh.SSHServer):
    """Accepts (and logs) logins per the configured policy."""

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.peer: object = None

    def connection_made(self, conn: asyncssh.SSHServerConnection) -> None:
        self.peer = conn.get_extra_info("peername")

    def begin_auth(self, username: str) -> bool:
        # Return True to require authentication, so we get a chance to log the
        # credentials the attacker tries.
        return True

    def password_auth_supported(self) -> bool:
        return True

    def validate_password(self, username: str, password: str) -> bool:
        ok = self.config.accept(username, password)
        self.config.log_login(username, password, self.peer, ok)
        return ok


class _ProcessReader:
    """Adapts an asyncssh SSHReader to our ``async readline() -> str | None``."""

    def __init__(self, stdin: asyncssh.SSHReader) -> None:
        self._stdin = stdin

    async def readline(self) -> str | None:
        try:
            line = await self._stdin.readline()
        except asyncssh.BreakReceived:
            return "\n"  # treat Ctrl-C as an empty line, keep the session alive
        if line == "":  # EOF
            return None
        return line


async def handle_client(config: ServerConfig, process: asyncssh.SSHServerProcess) -> None:
    """Entry point for each shell/exec request."""
    username = process.get_extra_info("username") or config.default_user
    has_pty = process.get_terminal_type() is not None

    reader = _ProcessReader(process.stdin)
    stdout = TerminalWriter(process.stdout, crlf=has_pty)
    stderr = TerminalWriter(process.stderr, crlf=has_pty)
    session = ShellSession(config, reader, stdout, stderr, username=username)

    status = 0
    try:
        if process.command is not None:      # ssh host "cmd"
            status = await session.run_exec(process.command)
        else:                                # interactive shell
            status = await session.run_interactive()
    except asyncssh.BreakReceived:
        status = 130
    except (asyncssh.ConnectionLost, BrokenPipeError):
        return
    except Exception:  # noqa: BLE001 - a buggy command must not kill the server
        status = 1
    finally:
        try:
            process.exit(status or 0)
        except Exception:  # noqa: BLE001
            pass


def _load_or_make_host_key(path: str | None):
    if path and os.path.exists(path):
        return asyncssh.read_private_key(path)
    key = asyncssh.generate_private_key("ssh-rsa", key_size=2048)
    if path:
        with open(path, "wb") as fh:
            fh.write(key.export_private_key())
        os.chmod(path, 0o600)
    return key


async def start_server(config: ServerConfig) -> asyncssh.SSHAcceptor:
    """Create and start the SSH server. Returns the asyncssh acceptor."""
    host_key = _load_or_make_host_key(config.host_key_path)
    return await asyncssh.create_server(
        lambda: HoneypotSSHServer(config),
        config.host,
        config.port,
        server_host_keys=[host_key],
        process_factory=functools.partial(handle_client, config),
        server_version=config.server_version,
    )
