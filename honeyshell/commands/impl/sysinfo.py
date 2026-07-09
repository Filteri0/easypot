"""System-info builtins: uname, id, hostname, env.

Deterministic queries whose answers come from the honeypot's configured
:class:`~honeyshell.core.config.SystemProfile` (injected on the context) and the
session identity. Keeping them builtin means their output stays consistent with
the advertised machine profile instead of being re-invented by the model each
turn — attackers frequently fingerprint a box with exactly these commands.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.context import ShellContext
from honeyshell.commands.registry import register
from honeyshell.core.config import SystemProfile


def _profile(ctx: ShellContext) -> SystemProfile:
    """The configured profile, or a default one so commands still work."""
    return ctx.system or SystemProfile(hostname=ctx.hostname)


@register("uname", "/bin/uname")
class Uname(Command):
    """Print system information. Supports -s/-n/-r/-m/-o/-a (and combos)."""

    _KERNEL_NAME = "Linux"

    async def run(self) -> int:
        p = _profile(self.ctx)
        flags = "".join(a[1:] for a in self.args if a.startswith("-") and a != "-")
        long_opts = [a for a in self.args if a.startswith("--")]

        if "a" in flags or "--all" in long_opts:
            # -a order: kernel-name nodename kernel-release kernel-version
            #           machine operating-system
            self.line(
                f"{self._KERNEL_NAME} {p.hostname} {p.kernel} "
                f"#1 SMP Debian {p.kernel} {p.architecture} GNU/Linux"
            )
            return 0

        parts: list[str] = []
        if not flags and not long_opts:
            flags = "s"  # default: kernel name
        if "s" in flags:
            parts.append(self._KERNEL_NAME)
        if "n" in flags:
            parts.append(p.hostname)
        if "r" in flags:
            parts.append(p.kernel)
        if "v" in flags:
            parts.append(f"#1 SMP Debian {p.kernel}")
        if "m" in flags or "p" in flags or "i" in flags:
            parts.append(p.architecture)
        if "o" in flags:
            parts.append("GNU/Linux")
        self.line(" ".join(parts) if parts else self._KERNEL_NAME)
        return 0


@register("id", "/usr/bin/id")
class Id(Command):
    """Print user/group identity."""

    async def run(self) -> int:
        uid = self.ctx.uid
        user = self.ctx.username
        if uid == 0:
            self.line("uid=0(root) gid=0(root) groups=0(root)")
        else:
            self.line(
                f"uid={uid}({user}) gid={uid}({user}) "
                f"groups={uid}({user})"
            )
        return 0


@register("hostname", "/bin/hostname")
class Hostname(Command):
    """Print the system hostname (from the configured profile)."""

    async def run(self) -> int:
        self.line(_profile(self.ctx).hostname)
        return 0


@register("env", "/usr/bin/env")
class Env(Command):
    """Print the environment. (Running a command via env is not supported.)"""

    async def run(self) -> int:
        for k, v in self.ctx.environ.items():
            self.line(f"{k}={v}")
        return 0
