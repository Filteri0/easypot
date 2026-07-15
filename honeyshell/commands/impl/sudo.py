"""sudo — run a command as another user (root), honeypot-style.

Behaviour tuned to look real without locking attackers out:

* As root already: run straight away (real sudo doesn't re-prompt root).
* As a normal user: prompt once for the password (``[sudo] password for X:``),
  with terminal echo disabled, **record whatever is typed** (intelligence),
  then accept it and run the command. A real box would validate; accepting lets
  us observe what the attacker does with elevated rights, while the recorded
  password is the payoff.

The command after ``sudo`` is executed via the same interpreter (like sh's
sub-run) so it really happens (and really mutates the VFS). ``exit`` inside it
is contained.

Deferred: real sudoers policy; ``-u user`` other than root; NOPASSWD nuance.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._credentials import record_credential

__all__ = ["Sudo"]


@register("sudo", "/usr/bin/sudo")
class Sudo(Command):
    async def run(self) -> int:
        args = list(self.args)
        # Strip a leading "-u user" (we only emulate elevation to root).
        if args and args[0] == "-u":
            args = args[2:] if len(args) >= 2 else []
        if not args:
            self.errline("usage: sudo command")
            return 1

        # Non-root must authenticate; root runs directly.
        if self.ctx.username != "root":
            if not await self._authenticate():
                return 1

        command = " ".join(args)
        if self.ctx.run_line is None:
            # No interpreter (unit context): can't actually run it.
            return 0
        return await self.ctx.run_line(
            command, stdout=self.stdout, stderr=self.stderr
        )

    async def _authenticate(self) -> bool:
        if self.ctx.read_prompt is None:
            # Non-interactive (exec/pipe): sudo can't prompt. Emulate the
            # common non-interactive failure rather than silently elevating.
            self.errline("sudo: a password is required")
            return False
        pw = await self.ctx.read_prompt(
            f"[sudo] password for {self.ctx.username}: ", True
        )
        if pw is None:
            self.errline("sudo: no password was provided")
            return False
        record_credential(self.ctx, self.ctx.username, pw)
        return True  # accept any password (honeypot: let them in to observe)
