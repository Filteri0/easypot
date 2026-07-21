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

        # Flag-only forms that do NOT run a command. Previously these fell
        # through to "run the flag as a command", so `sudo -l` produced
        # `bash: -l: command not found` — a blatant tell, since `sudo -l` is
        # a standard privilege-enumeration step (ATT&CK T1069) and every real
        # box answers it. Caught by the fidelity probe suite (Q30).
        if args[0] in ("-l", "-ll", "--list"):
            return await self._list_privileges()
        if args[0] in ("-V", "--version"):
            self.line("Sudo version 1.9.13p3")
            self.line("Sudoers policy plugin version 1.9.13p3")
            self.line("Sudoers file grammar version 48")
            self.line("Sudoers I/O plugin version 1.9.13p3")
            return 0
        if args[0] in ("-h", "--help"):
            self.line("usage: sudo -h | -K | -k | -V")
            self.line("usage: sudo -v [-ABkNnS] [-g group] [-h host] "
                      "[-p prompt] [-u user]")
            self.line("usage: sudo -l [-ABkNnS] [-g group] [-h host] "
                      "[-p prompt] [-U user] [-u user] [command [arg ...]]")
            return 0
        if args[0] in ("-k", "-K"):
            return 0  # invalidate timestamp: silent success, like real sudo

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

    async def _list_privileges(self) -> int:
        """Emulate ``sudo -l`` — the sudoers summary attackers enumerate.

        Non-root must authenticate first (real sudo prompts unless NOPASSWD),
        which doubles as another credential-capture opportunity.
        """
        user = self.ctx.username
        host = self.ctx.fs.hostname if hasattr(self.ctx.fs, "hostname") else "svr04"
        if user != "root":
            if not await self._authenticate():
                return 1
        self.line(f"Matching Defaults entries for {user} on {host}:")
        self.line("    env_reset, mail_badpass, "
                  "secure_path=/usr/local/sbin\\:/usr/local/bin\\:/usr/sbin\\:"
                  "/usr/bin\\:/sbin\\:/bin")
        self.line("")
        self.line(f"User {user} may run the following commands on {host}:")
        self.line("    (ALL : ALL) ALL")
        return 0

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
