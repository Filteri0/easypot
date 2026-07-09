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

from honeyshell.fs import VirtualFS


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

    @property
    def home(self) -> str:
        return self.environ.get("HOME") or (
            "/root" if self.username == "root" else f"/home/{self.username}"
        )
