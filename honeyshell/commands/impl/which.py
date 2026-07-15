"""which — locate a command by registry first, then the emulated $PATH.

Resolution order (mirrors how a real ``which`` walks $PATH, adapted to our
two-layer model):

1. **Registry.** Built-in emulated commands (the 55 that actually run) resolve
   to their canonical path, e.g. ``which ls`` -> ``/bin/ls``. This keeps the
   cheap deterministic layer authoritative for commands we truly implement.
2. **Emulated $PATH in the VFS.** For everything else, walk the standard PATH
   dirs and return the first one that holds a matching executable file. This is
   what lets ``which python3`` / ``which git`` succeed: those ship as
   metadata-only binaries in ``/usr/bin`` (see build_sample_fs §2), so tool
   presence stays consistent with the LLM's "assume any tool is installed"
   behaviour instead of contradicting it (§2 two-layer fix).
3. **Not found.** No output, exit 1 — exactly what an attacker probing for
   tooling expects (GNU ``which`` semantics).

Design note: which reads ``ctx.fs`` directly (a Command already holds ``ctx``),
so no new ctx seam is needed — the VFS is the single source of truth for what's
"installed", and the tree, not this command, decides which tools exist.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register, resolve

__all__ = ["Which"]

# Canonical paths for registered builtins (registry has no path metadata for
# bare-name registrations, so we map the common ones; others fall back to
# /usr/bin/<name>).
_COMMON_PATHS = {
    "ls": "/bin/ls", "cat": "/bin/cat", "echo": "/bin/echo",
    "pwd": "/bin/pwd", "cp": "/bin/cp", "mv": "/bin/mv", "rm": "/bin/rm",
    "mkdir": "/bin/mkdir", "touch": "/bin/touch", "grep": "/bin/grep",
    "sh": "/bin/sh", "bash": "/bin/bash", "wget": "/usr/bin/wget",
    "curl": "/usr/bin/curl", "whoami": "/usr/bin/whoami",
    "uname": "/bin/uname", "id": "/usr/bin/id",
}

# Standard $PATH search order for the VFS lookup (first match wins, like PATH).
_PATH_DIRS = (
    "/usr/local/sbin", "/usr/local/bin",
    "/usr/sbin", "/usr/bin", "/sbin", "/bin",
)


@register("which", "/usr/bin/which")
class Which(Command):
    async def run(self) -> int:
        if not self.args:
            return 1
        rc = 0
        for name in self.args:
            path = self._locate(name)
            if path is not None:
                self.line(path)
            else:
                rc = 1  # not found: no output, non-zero exit (GNU which)
        return rc

    def _locate(self, name: str) -> str | None:
        """Registry path, else first PATH dir in the VFS holding ``name``."""
        # A name with a slash is a path, not a PATH search — check it directly.
        if "/" in name:
            return name if self._is_exec(name) else None
        if resolve(name) is not None:
            # Some builtins model commands the host does NOT actually ship (the
            # RHEL package managers on this Debian box): they exist only to emit
            # "command not found". `which` must still report them absent, or it
            # contradicts itself (`which yum` -> a path, `yum` -> not found).
            cls = resolve(name)
            if getattr(cls, "absent_from_path", False):
                return None
            return _COMMON_PATHS.get(name, f"/usr/bin/{name}")
        fs = getattr(self.ctx, "fs", None)
        if fs is not None:
            for d in _PATH_DIRS:
                candidate = f"{d}/{name}"
                if self._is_exec(candidate):
                    return candidate
        return None

    def _is_exec(self, path: str) -> bool:
        fs = getattr(self.ctx, "fs", None)
        if fs is None:
            return False
        try:
            return fs.is_file(path)
        except Exception:  # noqa: BLE001 — a broken lookup is just "not found"
            return False
