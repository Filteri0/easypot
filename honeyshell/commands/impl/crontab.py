"""crontab — maintain the per-user cron table (persistence vector).

Attackers use crontab to persist. We store a per-user table as a file in the
VFS (``/var/spool/cron/crontabs/<user>``) so it survives within the session and
a later ``crontab -l`` shows what was installed — the state consistency that
makes the trap convincing, and a record of the persistence attempt.

Modes:
* ``crontab -l``        list the current table (or "no crontab for X").
* ``crontab -r``        remove the table.
* ``crontab -``         read a new table from stdin (piped install).
* ``crontab <file>``    install the table from a VFS file.

Deferred: ``-e`` interactive editor (needs an editor sub-session); real cron
scheduling (nothing actually runs).
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError

__all__ = ["Crontab"]

_SPOOL = "/var/spool/cron/crontabs"


@register("crontab", "/usr/bin/crontab")
class Crontab(Command):
    async def run(self) -> int:
        user = self.ctx.username
        path = f"{_SPOOL}/{user}"
        args = self.args

        if "-l" in args:
            return self._list(path, user)
        if "-r" in args:
            return self._remove(path)
        if "-e" in args:
            # No interactive editor yet; behave like a successful no-op edit.
            self.errline(f"no crontab for {user} - using an empty one")
            return 0
        if args and args[0] == "-":
            data = await self.read_all()
            return self._install(path, data)
        if args:
            return self._install_from_file(path, args[0])
        # Bare crontab with no stdin: usage.
        self.errline("usage: crontab [-l | -r | -e | file]")
        return 1

    def _ensure_spool(self) -> None:
        self.ctx.fs.makedirs(_SPOOL, "/")

    def _list(self, path: str, user: str) -> int:
        try:
            self.write(self.ctx.fs.readtext(path, "/"))
            return 0
        except FSError:
            self.errline(f"no crontab for {user}")
            return 1

    def _remove(self, path: str) -> int:
        try:
            self.ctx.fs.remove(path, "/")
        except FSError:
            pass
        return 0

    def _install(self, path: str, data: str) -> int:
        self._ensure_spool()
        self.ctx.fs.write_file(path, data.encode(), "/",
                               uid=self.ctx.uid, gid=self.ctx.uid)
        return 0

    def _install_from_file(self, path: str, src: str) -> int:
        try:
            data = self.ctx.fs.readtext(src, self.ctx.cwd)
        except FSError:
            self.errline(f'crontab: {src}: No such file or directory')
            return 1
        return self._install(path, data)
