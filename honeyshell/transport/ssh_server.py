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


async def handle_client(
    config: ServerConfig,
    process: asyncssh.SSHServerProcess,
    resolver=None,
    memory_settings=None,
) -> None:
    """Entry point for each shell/exec request.

    ``resolver`` is a shared :class:`~honeyshell.backends.ChainResolver` built
    once at bootstrap when ``config.llm_enable`` is set; here we wrap it in a
    per-connection factory (carrying this session's id) that the interpreter
    calls on a registry miss.
    """
    username = process.get_extra_info("username") or config.default_user
    has_pty = process.get_terminal_type() is not None

    # Terminal width from the PTY window (cols, rows, ...); default 80 when
    # unavailable. Used by `ls` for column layout.
    term_width = 80
    if has_pty:
        try:
            size = process.get_terminal_size()
            if size and size[0]:
                term_width = size[0]
        except Exception:  # noqa: BLE001
            pass

    # Per-connection LLM factory (None when the backend is disabled).
    miss_handler = None
    if resolver is not None:
        from honeyshell.backends import make_llm_command_factory
        peer = process.get_extra_info("peername")
        session_id = f"{peer[0]}:{peer[1]}" if isinstance(peer, tuple) else None
        miss_handler = make_llm_command_factory(resolver, session_id=session_id)

    reader = _ProcessReader(process.stdin)
    stdout = TerminalWriter(process.stdout, crlf=has_pty)
    # On a PTY, a real shell writes stdout and stderr to the same terminal, so
    # ordering is naturally correct. asyncssh exposes them as separate channels
    # and the client may interleave them out of order (errors appearing after
    # the *next* prompt). Merge stderr into stdout for interactive sessions;
    # keep them split for exec mode where a caller may capture them separately.
    stderr = stdout if has_pty else TerminalWriter(process.stderr, crlf=has_pty)
    session = ShellSession(
        config,
        reader,
        stdout,
        stderr,
        username=username,
        is_tty=has_pty,
        term_width=term_width,
        miss_handler=miss_handler,
        memory_settings=memory_settings,
    )

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

    # Build one shared LLM resolver at bootstrap when enabled. Sharing means the
    # response cache (paper §3.4) is warm across connections — repeated attacker
    # commands hit cache instead of re-querying the model. Backends are imported
    # lazily so a non-LLM deployment never needs httpx installed.
    resolver = None
    memory_settings = None
    if config.llm_enable:
        from honeyshell.backends import ChainResolver, OllamaClient
        from honeyshell.core.config import HoneypotConfig

        hp = HoneypotConfig()
        # Share the server's single SystemProfile so the model's advertised
        # machine matches what the uname/hostname builtins report.
        if config.system is not None:
            hp.system = config.system
        hp.llm.model = config.llm_model
        memory_settings = hp.memory
        client = OllamaClient(model=config.llm_model, base_url=config.llm_base_url)
        resolver = ChainResolver(client=client, config=hp)

        # Startup self-check so misconfiguration is visible immediately rather
        # than silently degrading every unknown command to "command not found".
        import logging as _logging
        _log = _logging.getLogger("honeyshell")

        # Distinguish "httpx missing" from "server down" — they need different
        # fixes and both otherwise present as a silent fallback.
        httpx_ok = True
        try:
            import httpx  # noqa: F401
        except ImportError:
            httpx_ok = False

        if not httpx_ok:
            _log.warning(
                "LLM enabled but httpx is NOT installed in this venv. "
                "Run: pip install httpx  (unknown commands will fall back to "
                "'command not found' until then)."
            )
        else:
            try:
                ok = await client.is_available()
            except Exception as exc:  # noqa: BLE001
                ok = False
                _log.warning("LLM self-check raised: %s", exc)
            if ok:
                _log.info(
                    "LLM backend ready: model=%s url=%s", config.llm_model,
                    config.llm_base_url,
                )
            else:
                _log.warning(
                    "LLM enabled but Ollama NOT reachable at %s. Unknown "
                    "commands fall back to 'command not found'. Check: "
                    "`ollama serve` running and `ollama pull %s`.",
                    config.llm_base_url, config.llm_model,
                )

    return await asyncssh.create_server(
        lambda: HoneypotSSHServer(config),
        config.host,
        config.port,
        server_host_keys=[host_key],
        process_factory=functools.partial(
            handle_client, config, resolver=resolver,
            memory_settings=memory_settings,
        ),
        server_version=config.server_version,
    )
