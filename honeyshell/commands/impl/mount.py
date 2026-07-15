"""mount — list mounted filesystems (read-only).

Why a builtin: the mount table must agree with `df` and `cat /proc/mounts`.
Rather than hardcode a second copy, `mount` (no args) reads the same
`/proc/mounts` fixture and reformats each line into mount's
``SRC on TARGET type FSTYPE (opts)`` presentation — one source of truth, no
drift. A real box always has `mount`; its absence was a clear tell.

Deferred: actually mounting/unmounting (a honeypot never should); `-t`/`-l`
filtering; per-mount statistics. Any `mount <args>` that looks like a real
mount attempt is accepted silently (returns 0) rather than erroring, which is
closer to harmless for a decoy than a hard failure.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError

__all__ = ["Mount"]

# Fallback table (used only if /proc/mounts is somehow absent) — kept aligned
# with build_sample_fs._MOUNTS so behaviour is identical either way.
_FALLBACK = (
    "sysfs /sys sysfs rw,nosuid,nodev,noexec,relatime 0 0\n"
    "proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0\n"
    "/dev/sda1 / ext4 rw,relatime,errors=remount-ro 0 0\n"
    "tmpfs /dev/shm tmpfs rw,nosuid,nodev 0 0\n"
    "tmpfs /run tmpfs rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755 "
    "0 0\n"
)


@register("mount", "/usr/bin/mount", "/bin/mount")
class Mount(Command):
    async def run(self) -> int:
        # `mount <device> <dir>` etc.: accept silently (no real mounting).
        if any(not a.startswith("-") for a in self.args):
            return 0

        try:
            raw = self.ctx.fs.readtext("/proc/mounts", self.ctx.cwd)
        except FSError:
            raw = _FALLBACK

        for ln in raw.splitlines():
            parts = ln.split()
            if len(parts) < 4:
                continue
            src, target, fstype, opts = parts[0], parts[1], parts[2], parts[3]
            self.line(f"{src} on {target} type {fstype} ({opts})")
        return 0
