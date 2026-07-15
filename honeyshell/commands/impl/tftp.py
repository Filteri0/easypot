"""tftp — simulate a TFTP get, writing the fetched file into the VirtualFS.

Design lineage
--------------
Modelled on the BusyBox/GNU tftp client as Cowrie emulates it, but non-network:
the "downloaded" file is a placeholder written to the VFS via the shared
``_download`` helpers. Deterministic + VFS-mutating -> builtin (HANDOFF2 §4-5).

Supported (non-interactive only)
--------------------------------
``tftp -g -r REMOTEFILE HOST``  (get, remote file via -r)
``tftp -c get REMOTEFILE HOST`` (get via -c)
The local filename is the remote file's basename.

Deferred
--------
Interactive mode (the ``tftp>`` prompt) needs a ``read_line`` loop and is left
for a later batch. ``put`` is accepted but is a no-op success. No real transfer.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._download import (
    SaveError,
    outfile_from_url,
    placeholder_contents,
    save_to_vfs,
)

__all__ = ["Tftp"]

_USAGE = "usage: tftp [-h] [-c C C] [-l L] [-g] [-p P] [-r R] [hostname]"


@register("tftp", "/usr/bin/tftp", "/bin/tftp")
class Tftp(Command):
    async def run(self) -> int:
        remote: str | None = None
        host: str | None = None
        mode = "get"  # default; -c put flips to put

        args = self.args
        i = 0
        positionals: list[str] = []
        while i < len(args):
            a = args[i]
            if a == "-r":
                if i + 1 < len(args):
                    remote = args[i + 1]
                    i += 2
                    continue
                i += 1
                continue
            if a == "-c":
                # -c get FILE  /  -c put FILE
                if i + 1 < len(args):
                    mode = args[i + 1]
                if i + 2 < len(args):
                    remote = args[i + 2]
                i += 3
                continue
            if a == "-g":
                mode = "get"
                i += 1
                continue
            if a in ("-p",):
                mode = "put"
                i += 1
                continue
            if a.startswith("-"):
                i += 1  # ignore -l and friends
                continue
            positionals.append(a)
            i += 1

        # Hostname is the remaining positional (Cowrie treats it positionally).
        if positionals:
            host = positionals[0]

        if host is None or remote is None:
            self.errline(_USAGE)
            return 1

        if mode == "put":
            return 0  # uploads succeed silently in this emulation

        local = outfile_from_url(remote) if "/" in remote else remote
        url = f"tftp://{host}/{remote.lstrip('/')}"
        data = placeholder_contents(url)
        try:
            save_to_vfs(self.ctx, local, data)
        except SaveError:
            self.errline(f"tftp: {local}: No such file or directory")
            return 1
        return 0
