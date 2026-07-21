"""Execution context handed to every command.

This is the mutable shell state a command may read or change: the virtual
filesystem, current working directory, environment, and identity. The
interpreter (a later module) owns and supplies a ``ShellContext``; keeping it
in its own module avoids import cycles between ``base`` and the interpreter.

A command mutates state simply by assigning to the context (e.g. ``cd`` sets
``ctx.cwd``). Because the context is shared for the whole session, this is how
builtins that affect the shell (cd/export/...) take effect — mirroring bash,
where such commands are builtins that run in the shell process itself rather
than as child processes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Awaitable, Callable, Optional

from honeyshell.core.config import SystemProfile
from honeyshell.fs import VirtualFS

if TYPE_CHECKING:
    from honeyshell.memory import Pruner, SessionMemory
    from honeyshell.commands.streams import Writable
    from honeyshell.core.event_bus import EventBus


@dataclass
class ShellContext:
    fs: VirtualFS
    cwd: str = "/"
    environ: dict[str, str] = field(default_factory=dict)
    username: str = "root"
    hostname: str = "svr04"
    #: Correlation id for this SSH connection. Stamped onto every audit event
    #: emitted during the session so logs/JSONL can be grouped per-connection.
    #: None outside a live session (bare unit-test contexts).
    session_id: Optional[str] = None
    #: Set by the `exit`/`logout` builtin to ask the session loop to end.
    should_exit: bool = False
    #: True when the session is attached to a PTY. Commands like ``ls`` use
    #: this to decide between human-facing column layout (tty) and one
    #: entry per line (pipes / exec), matching how GNU coreutils behave.
    is_tty: bool = False
    #: Terminal width in columns; only meaningful when ``is_tty`` is True.
    #: Injected by the session from the PTY window size (falls back to 80).
    term_width: int = 80
    #: The emulated machine profile (kernel, arch, CPU, ...). Read by system
    #: commands like ``uname``/``hostname`` so their output matches the honeypot
    #: config. Optional: when None, those commands fall back to sane defaults.
    system: Optional[SystemProfile] = None
    #: Per-session dynamic memory (SR/H/FL) for the LLM backend. Attached by the
    #: session; the LLM command records interactions here and the prompt builder
    #: reads SR/H back out. None when the LLM backend is disabled.
    memory: Optional["SessionMemory"] = None
    #: Memory pruner (Weaken-Factor decay + eviction). Attached alongside
    #: ``memory``; the LLM command calls ``pruner.step(memory)`` each turn.
    pruner: Optional["Pruner"] = None
    #: Re-entrant "run one command line" hook, wired by the Interpreter to its
    #: own ``execute``. This is the narrow seam the ``sh``/``bash`` builtin uses
    #: to run ``-c`` strings, piped-in scripts, or a script file through the
    #: *same* interpreter (shared VFS/cwd/memory and the same LLM miss_handler),
    #: mirroring Cowrie's ``execute_commands`` spawning a sub-shell. Only shell
    #: builtins touch it; every other command ignores it. Optional ``stdout``
    #: redirects the sub-run's output (so ``curl x | sh`` surfaces the script's
    #: output on sh's stdout). None outside a live interpreter (e.g. unit tests
    #: that construct a bare context).
    run_line: Optional[
        Callable[..., Awaitable[int]]
    ] = None
    #: Optional "fetch a URL's body" hook for the download builtins (curl/wget).
    #: When wired (i.e. the LLM backend is enabled), curl/wget on the *stdout*
    #: path (``curl URL`` / ``wget URL -O -`` / ``... | sh``) call this to get
    #: LLM-generated content instead of the static placeholder, so a real URL
    #: yields believable output. Returns the body as bytes, or None when it
    #: can't produce one (no LLM, model down) — the command then falls back to
    #: the placeholder. The *save* path keeps using the placeholder regardless
    #: (nobody cats a downloaded binary; keeps cost down and state consistent).
    fetch_content: Optional[
        Callable[[str], Awaitable[Optional[bytes]]]
    ] = None
    #: Nesting depth of the sh/bash builtin, used to stop runaway recursion
    #: (e.g. an LLM-generated ``install.sh`` that itself pipes into sh, or a
    #: self-referential script). The Sh builtin increments this around a
    #: sub-run and refuses to descend past a small limit — belt-and-braces on
    #: top of Python's own recursion guard, and it also caps the fan-out of LLM
    #: calls a single piped script can trigger.
    shell_depth: int = 0
    #: Interactive line-read hook: ``read_prompt(prompt, hide) -> str | None``.
    #: Writes ``prompt`` and reads one line from the live terminal — the
    #: attacker's real keystrokes, not piped stdin. ``hide=True`` disables
    #: terminal echo (for password entry). Returns the line, or None on EOF /
    #: interrupt. Wired by the session to the SSH line editor; None outside a
    #: live interactive session (piped/exec mode), where interactive commands
    #: must degrade gracefully. Used by sudo/su/passwd to prompt for — and let
    #: the honeypot record — credentials.
    read_prompt: Optional[
        Callable[..., Awaitable[Optional[str]]]
    ] = None
    #: Audit event bus. When wired, commands emit structured events onto it —
    #: currently sudo/su/passwd publish a LoginEvent recording the credentials
    #: an attacker typed (prime honeypot intelligence). Optional so non-audited
    #: or unit-test contexts run without it; commands must null-check before
    #: emitting.
    event_bus: Optional["EventBus"] = None

    #: The honeypot's emulated wall clock. Every time-producing command
    #: (date/uptime/ls mtime cutoff) and every runtime file mtime must read
    #: from here, so `date`, `ls -l`, `/proc/uptime` and freshly-created files
    #: all agree. Without a single source, `date` shows the real 2026 while the
    #: shipped fs shows 2024 — a two-year gap an attacker spots with `date`.
    #: Defaults to real time; the session pins it once at login so a session
    #: sees a stable, self-consistent clock.
    clock: "Callable[[], float]" = field(default=None)  # type: ignore[assignment]
    #: Emulated boot time (epoch). uptime/who derive from it. Set by session.
    boot_time: Optional[float] = None
    #: The resolved login uid (from /etc/passwd or freshly allocated by the
    #: session). ``id``/``ls`` read this so uid is consistent with passwd,
    #: instead of the old hardcoded 1000-for-everyone. None -> derive from name.
    login_uid: Optional[int] = None
    #: The attacker's source address (from the SSH peername), so `netstat`/`who`
    #: /`w` can show the attacker's *own* connection instead of a hardcoded
    #: stranger IP — an attacker expects to see their session in the list.
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    #: Accumulated emulated time skew (seconds) added on top of ``clock``.
    #: ``sleep`` advances this instead of really blocking: a honeypot that
    #: returns instantly leaves the wall clock unmoved, so the classic sandbox
    #: probe ``date +%s; sleep 2; date +%s`` (ATT&CK T1497) reads back two
    #: identical timestamps — a dead giveaway that time is faked. Advancing the
    #: offset keeps the session's clock self-consistent across commands while
    #: still returning immediately (never block: blocking is both a timing tell
    #: and a way for an attacker to tie up the session).
    time_offset: float = 0.0

    def now(self) -> float:
        """Current emulated time (epoch seconds), including ``time_offset``."""
        import time as _t
        return (self.clock or _t.time)() + self.time_offset

    @property
    def uid(self) -> int:
        """Effective uid: 0 for root, else the resolved login uid (from passwd
        or session-allocated), falling back to 1000 for bare test contexts."""
        if self.username == "root":
            return 0
        return self.login_uid if self.login_uid is not None else 1000

    @property
    def home(self) -> str:
        return self.environ.get("HOME") or (
            "/root" if self.username == "root" else f"/home/{self.username}"
        )
