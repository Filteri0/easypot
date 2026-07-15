"""su — switch user.

Prompts for a password (echo off), records it, then accepts and switches the
session identity by changing ``ctx.username`` (which drives uid/home). Switching
to root from root needs no password (real behaviour). Supports ``su``,
``su <user>``, and ``su -c "cmd" <user>`` (run one command as the target user).

Deferred: spawning a full interactive sub-shell for bare ``su`` (would need a
nested REPL); login vs non-login environment differences beyond user/home.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._credentials import record_credential

__all__ = ["Su"]


@register("su", "/bin/su")
class Su(Command):
    async def run(self) -> int:
        args = list(self.args)
        command = None
        # Pull out "-c CMD": CMD is the single following token (the parser has
        # already collapsed a quoted "echo hi" into one token). The target user,
        # if any, is a remaining positional.
        if "-c" in args:
            idx = args.index("-c")
            if idx + 1 < len(args):
                command = args[idx + 1]
                args = args[:idx] + args[idx + 2:]
            else:
                args = args[:idx]
        # Drop a leading login flag "-" / "-l".
        args = [a for a in args if a not in ("-", "-l", "--login")]
        target = args[0] if args else "root"

        # Authenticate unless already root (root -> anyone is free).
        if self.ctx.username != "root":
            if not await self._authenticate(target):
                self.errline("su: Authentication failure")
                return 1

        prev_user = self.ctx.username
        if command is not None:
            # Run one command as the target, then restore identity.
            self.ctx.username = target
            try:
                if self.ctx.run_line is None:
                    return 0
                return await self.ctx.run_line(
                    command, stdout=self.stdout, stderr=self.stderr
                )
            finally:
                self.ctx.username = prev_user
        else:
            # Bare su: switch the session identity (no nested shell here).
            self._switch_identity(target)
            return 0

    def _switch_identity(self, target: str) -> None:
        """Switch the session identity: username, cwd -> target home, and keep
        uid/fs-owner consistent so later `id` and file creation match."""
        self.ctx.username = target
        # Resolve target uid from /etc/passwd so `id` is correct after su.
        uid = 0 if target == "root" else self._passwd_uid(target)
        self.ctx.login_uid = uid
        try:
            self.ctx.fs.set_owner(uid)
        except Exception:  # noqa: BLE001
            pass
        self.ctx.cwd = self.ctx.home

    def _passwd_uid(self, user: str) -> int:
        try:
            for ln in self.ctx.fs.readtext("/etc/passwd").splitlines():
                p = ln.split(":")
                if len(p) >= 3 and p[0] == user and p[2].isdigit():
                    return int(p[2])
        except Exception:  # noqa: BLE001
            pass
        return 1000

    async def _authenticate(self, target: str) -> bool:
        if self.ctx.read_prompt is None:
            return False
        pw = await self.ctx.read_prompt("Password: ", True)
        if pw is None:
            return False
        record_credential(self.ctx, target, pw)
        return True  # accept any password
