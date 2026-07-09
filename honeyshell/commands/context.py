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
from typing import TYPE_CHECKING, Optional

from honeyshell.core.config import SystemProfile
from honeyshell.fs import VirtualFS

if TYPE_CHECKING:
    from honeyshell.memory import Pruner, SessionMemory


@dataclass
class ShellContext:
    fs: VirtualFS
    cwd: str = "/"
    environ: dict[str, str] = field(default_factory=dict)
    username: str = "root"
    hostname: str = "svr04"
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

    @property
    def uid(self) -> int:
        """Effective uid: 0 for root, else a conventional non-root uid."""
        return 0 if self.username == "root" else 1000

    @property
    def home(self) -> str:
        return self.environ.get("HOME") or (
            "/root" if self.username == "root" else f"/home/{self.username}"
        )
