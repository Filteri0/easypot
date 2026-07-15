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
from honeyshell.transport.session import INTERRUPT, ShellSession
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
    """Adapts an asyncssh SSHReader to our ``async readline() -> str | None``.

    Two Ctrl-C paths exist and are handled separately:

    * The common one — the client sends the ``\\x03`` character — is intercepted
      by the line-editor key handler in ``_try_register_tab_completion`` (prints
      ``^C``, clears the buffer, redraws the prompt) and never reaches here.
    * A client that instead sends an SSH *break signal* raises
      ``BreakReceived`` on ``readline``. As a fallback we surface the
      :data:`INTERRUPT` sentinel so the interactive loop abandons the current
      input and redraws exactly one fresh prompt (no storm, session stays up).
    """

    def __init__(self, stdin: asyncssh.SSHReader) -> None:
        self._stdin = stdin

    async def readline(self):
        try:
            line = await self._stdin.readline()
        except asyncssh.BreakReceived:
            return INTERRUPT
        if line == "":  # EOF
            return None
        return line


async def handle_client(
    config: ServerConfig,
    process: asyncssh.SSHServerProcess,
    resolver=None,
    memory_settings=None,
    content_client=None,
    event_bus=None,
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

    # Per-connection content fetcher for curl/wget's stdout path (LLM-generated
    # URL bodies). Built per connection so its URL cache is session-scoped
    # (option A): the same URL is consistent within a session, not across them.
    fetch_content = None
    if content_client is not None:
        from honeyshell.backends import ContentFetcher
        fetch_content = ContentFetcher(client=content_client)

    stdout = TerminalWriter(process.stdout, crlf=has_pty)
    # On a PTY, a real shell writes stdout and stderr to the same terminal, so
    # ordering is naturally correct. asyncssh exposes them as separate channels
    # and the client may interleave them out of order (errors appearing after
    # the *next* prompt). Merge stderr into stdout for interactive sessions;
    # keep them split for exec mode where a caller may capture them separately.
    stderr = stdout if has_pty else TerminalWriter(process.stderr, crlf=has_pty)
    reader = _ProcessReader(process.stdin)

    # Interactive credential prompt for sudo/su/passwd. Writes the prompt,
    # reads one line from the live terminal, and — when hide=True and a line
    # editor is present — disables echo so a typed password isn't shown, then
    # restores it. Degrades safely if the editor can't toggle echo (older
    # asyncssh / no pty): the prompt still works, just without hiding.
    channel = getattr(process, "channel", None)

    async def read_prompt(prompt: str, hide: bool = False):
        stdout.write(prompt)
        set_echo = getattr(channel, "set_echo", None)
        toggled = False
        if hide and callable(set_echo):
            try:
                set_echo(False)
                toggled = True
            except Exception:  # noqa: BLE001 — echo control unsupported: proceed
                toggled = False
        try:
            line = await process.stdin.readline()
        except asyncssh.BreakReceived:
            line = ""
        finally:
            if toggled:
                try:
                    set_echo(True)
                except Exception:  # noqa: BLE001
                    pass
        if hide:
            # The client's echo was off (or we asked for it off), so the user's
            # Enter didn't move the cursor down — emit the newline ourselves.
            stdout.write("\n")
        if line == "":
            return None
        return line.rstrip("\r\n")

    peer = process.get_extra_info("peername")
    src_ip = peer[0] if isinstance(peer, tuple) else None
    src_port = peer[1] if isinstance(peer, tuple) and len(peer) > 1 else None

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
        fetch_content=fetch_content,
        read_prompt=read_prompt,
        event_bus=event_bus,
        src_ip=src_ip,
        src_port=src_port,
    )

    # Tab-completion: register a handler on the line editor (PTY only). The
    # editor is asyncssh's SSHLineEditorChannel wrapper on process.channel when
    # a pty was requested. Completing command names (from the registry) and
    # paths (from this session's VFS) removes an easy honeypot tell — a real
    # shell completes, a dead one doesn't. Best-effort: any failure to hook the
    # editor is swallowed so the session still works without completion.
    if has_pty:
        _try_register_tab_completion(process, session)

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


def _try_register_tab_completion(
    process: asyncssh.SSHServerProcess, session: ShellSession
) -> None:
    """Hook Tab (completion) and Ctrl-C (line reset) on the asyncssh editor.

    asyncssh wraps a pty channel in ``SSHLineEditorChannel``, exposing
    ``register_key(key, handler)`` where the handler gets ``(line, pos)`` and
    returns ``(new_line, new_pos)`` (or ``True``/``False``). We delegate Tab's
    completion decision to the transport-agnostic ``completion.complete`` so it
    stays unit-testable; we only bridge asyncssh <-> that function here.

    **Ctrl-C**: by default asyncssh binds ``\\x03`` to a "send break" action that
    signals the session but leaves the half-typed line in the editor buffer —
    so the next input concatenates onto the junk ("partial" + "whoami"). We
    override ``\\x03`` to instead print ``^C`` and reset the editor line to empty
    (returning ``('', 0)``), then redraw the shell prompt. This matches bash and
    fixes both the buffer-carryover bug and the earlier prompt storm.

    Best-effort: if the editor isn't present (older asyncssh, no pty, missing
    ``register_key``) we silently skip — line-editing niceties must never be a
    correctness requirement.
    """
    from honeyshell.commands import registry
    from honeyshell.transport import completion

    channel = getattr(process, "channel", None)
    register = getattr(channel, "register_key", None)
    if register is None:
        return

    def _command_names() -> list[str]:
        # registry maps both bare names and full paths (e.g. "ls" and
        # "/bin/ls"); for command completion offer only the bare basenames so
        # Tab yields "ls", not "/bin/ls".
        return sorted({k for k in registry.all_commands() if "/" not in k})

    def _tab_handler(line: str, pos: int):
        try:
            return completion.complete(
                line, pos,
                command_names=_command_names(),
                fs=session.ctx.fs,
                cwd=session.ctx.cwd,
            )
        except Exception:  # noqa: BLE001 - a completion bug must not kill input
            return line, pos

    def _ctrlc_handler(line: str, pos: int):
        # Print "^C", drop the current line, and redraw the prompt — bash-like.
        # Writing straight to stdout is safe: the editor is between keystrokes.
        try:
            process.stdout.write("^C\r\n")
            process.stdout.write(session.prompt())
        except Exception:  # noqa: BLE001
            pass
        return "", 0  # editor clears its buffer and repositions the cursor

    try:
        register("\t", _tab_handler)
        register("\x03", _ctrlc_handler)
    except Exception:  # noqa: BLE001 - editor not ready / unsupported: skip
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
    content_client = None
    # One audit bus per server, shared across connections. A LoggingSink is
    # attached so events (currently credential captures from sudo/su/passwd)
    # surface in the logs; richer sinks (JSONL/SIEM) can subscribe later without
    # touching the emitters. This is the first real wiring of the event bus into
    # transport — login/command events remain deferred.
    from honeyshell.core.event_bus import EventBus, LoggingSink
    event_bus = EventBus()
    event_bus.subscribe(LoggingSink())
    # Structured JSONL feed for the collector, when configured. Each honeypot
    # writes to its own file on a shared volume; the collector tails them.
    if config.audit_jsonl_path:
        from honeyshell.core.event_bus import JSONLSink
        event_bus.subscribe(JSONLSink(path=config.audit_jsonl_path))
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
        # A second client with json_format OFF for the curl/wget content path:
        # we want a raw script/HTML body, not the JSON the command-simulation
        # path parses. Same model/URL; only the output constraint differs.
        content_client = OllamaClient(
            model=config.llm_model,
            base_url=config.llm_base_url,
            json_format=False,
        )

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
            content_client=content_client,
            event_bus=event_bus,
        ),
        server_version=config.server_version,
    )
