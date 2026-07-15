"""wget — simulate a non-interactive HTTP(S)/FTP download.

Design lineage
--------------
Behaviourally modelled on GNU wget's console output (Cowrie's wget mimics the
same lines), but this version never touches the network: it synthesises the
progress output and writes a placeholder file into the VirtualFS via the shared
``_download`` helpers. A builtin (not LLM) because it's deterministic and
VFS-mutating — the download must actually appear in the tree so the next
``ls``/``cat`` is consistent (HANDOFF2 §4-5).

Supported
---------
``-O FILE`` (write to FILE; ``-O -`` streams to stdout), ``-q``/``--quiet``
(suppress the progress output on stderr). Unknown flags are ignored rather than
erroring, closer to real wget for compatibility options.

Output goes to **stderr** (real wget writes progress to stderr; ``wget URL
2>/dev/null`` silences it). NB: ``2>`` redirection is still blocked by the
parser — a pre-existing deferred item across all HANDOFFs, not a bug here.

Deferred
--------
No real transfer, no redirect following, no rate limiting, no ``-c`` resume.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._download import (
    SaveError,
    content_for_stdout,
    normalize_url,
    outfile_from_url,
    placeholder_contents,
    save_to_vfs,
)

__all__ = ["Wget"]

_TIMESTAMP = "2026-01-01 00:00:00"  # fixed clock; VFS has no real mtime yet
_VERSION = "1.25.0"


@register("wget", "/usr/bin/wget", "/bin/wget")
class Wget(Command):
    async def run(self) -> int:
        outfile: str | None = None
        quiet = False
        urls: list[str] = []

        # Minimal getopt: -O takes an argument (possibly the next token),
        # -q/--quiet is a flag, other -x are ignored for compatibility.
        args = self.args
        i = 0
        while i < len(args):
            a = args[i]
            if a == "-O":
                if i + 1 < len(args):
                    outfile = args[i + 1]
                    i += 2
                    continue
                i += 1
                continue
            if a.startswith("-O"):
                outfile = a[2:]
                i += 1
                continue
            if a in ("-q", "--quiet"):
                quiet = True
                i += 1
                continue
            if a.startswith("-"):
                i += 1  # ignore unknown flags
                continue
            urls.append(a)
            i += 1

        if not urls:
            self.errline("wget: missing URL")
            self.errline("Usage: wget [OPTION]... [URL]...")
            self.errline("")
            self.errline("Try `wget --help' for more options.")
            return 1

        rc = 0
        for url in urls:
            rc = await self._fetch(url, outfile, quiet) or rc
        return rc

    async def _fetch(self, url: str, outfile: str | None, quiet: bool) -> int:
        parsed = normalize_url(url)
        if parsed is None:
            self.errline(f"wget: unable to resolve host address ‘{url}’")
            return 1

        # -O - : stream to stdout, don't save. Content is LLM-generated when a
        # fetcher is wired, else the placeholder.
        if outfile == "-":
            data = await content_for_stdout(self.ctx, parsed.raw)
            size = len(data)
            if not quiet:
                self._progress_header(parsed, size, dest="STDOUT")
            self.write(data.decode("utf-8", "replace"))
            if not quiet:
                self.errline(
                    f"{_TIMESTAMP} (10.0 MB/s) - written to stdout [{size}/{size}]"
                )
                self.errline("")
            return 0

        # Save path: keep the deterministic placeholder.
        dest = outfile if outfile else outfile_from_url(parsed.path)
        data = placeholder_contents(parsed.raw)
        size = len(data)

        try:
            save_to_vfs(self.ctx, dest, data)
        except SaveError as e:
            # Header still prints (real wget connects before discovering the
            # bad output path); then the open error.
            if not quiet:
                self.errline(f"--{_TIMESTAMP}--  {parsed.raw}")
                self.errline(
                    f"Connecting to {parsed.host}:{parsed.port}... connected."
                )
                self.errline("HTTP request sent, awaiting response... 200 OK")
            self.errline(f"wget: {e.message}")
            return 1

        if not quiet:
            self._progress_header(parsed, size, dest=dest)
            self._progress_body(dest, size)
        return 0

    def _progress_header(self, parsed, size: int, dest: str) -> None:
        self.errline(f"--{_TIMESTAMP}--  {parsed.raw}")
        self.errline(f"Connecting to {parsed.host}:{parsed.port}... connected.")
        self.errline("HTTP request sent, awaiting response... 200 OK")
        self.errline(f"Length: {size} ({_sizeof(size)}) [application/octet-stream]")
        self.errline(f"Saving to: '{dest}'")
        self.errline("")

    def _progress_body(self, dest: str, size: int) -> None:
        bar = "=" * 40 + ">"
        self.errline(f"{dest} 100%[{bar}] {size}  --.-KB/s    in 0s")
        self.errline("")
        self.errline(
            f"{_TIMESTAMP} (10.0 MB/s) - '{dest}' saved [{size}/{size}]"
        )
        self.errline("")


def _sizeof(num: float) -> str:
    """Human-readable size like GNU wget (bytes/K/M/G/T)."""
    for unit in ("bytes", "K", "M", "G", "T"):
        if num < 1024.0:
            if unit == "bytes":
                return f"{int(num)}{unit}"
            return f"{num:.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}P"
