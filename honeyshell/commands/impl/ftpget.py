"""ftpget — simulate BusyBox ftpget, writing the fetched file into the VFS.

Design lineage
--------------
Modelled on BusyBox ``ftpget``, non-network: the "downloaded" file is a
placeholder written to the VFS via the shared ``_download`` helpers.
Deterministic + VFS-mutating -> builtin (HANDOFF2 §4-5).

Usage
-----
``ftpget [options] HOST [LOCALFILE] REMOTEFILE``
Two positionals -> HOST REMOTEFILE (local name = remote basename).
Three positionals -> HOST LOCALFILE REMOTEFILE.
Options (-u/-p/-P credentials, -c/-v) are accepted and ignored.

Deferred
--------
No real transfer; credentials are not validated.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._download import (
    SaveError,
    placeholder_contents,
    save_to_vfs,
)

__all__ = ["Ftpget"]

_USAGE = (
    "BusyBox v1.20.2 (2016-06-22 15:12:53 EDT) multi-call binary.\n"
    "\n"
    "Usage: ftpget [OPTIONS] HOST [LOCAL_FILE] REMOTE_FILE"
)


@register("ftpget", "/usr/bin/ftpget", "/bin/ftpget")
class Ftpget(Command):
    async def run(self) -> int:
        # Flags that take a value: -u user, -p pass, -P port.
        args = self.args
        positionals: list[str] = []
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("-u", "-p", "-P"):
                i += 2  # skip the flag and its value
                continue
            if a.startswith("-"):
                i += 1  # -c, -v and unknowns: ignore
                continue
            positionals.append(a)
            i += 1

        if len(positionals) == 2:
            host, remote = positionals
            local = remote.rsplit("/", 1)[-1]
        elif len(positionals) >= 3:
            host, local, remote = positionals[:3]
        else:
            for ln in _USAGE.split("\n"):
                self.errline(ln)
            return 1

        url = f"ftp://{host}/{remote.lstrip('/')}"
        data = placeholder_contents(url)
        try:
            save_to_vfs(self.ctx, local, data)
        except SaveError:
            self.errline(f"ftpget: can't open '{local}': No such file or directory")
            return 1
        return 0
