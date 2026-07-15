"""curl — simulate a data transfer, printing to stdout by default.

Design lineage
--------------
Behaviourally modelled on curl. The defining difference from wget: curl writes
the body to **stdout** unless told to save (``-o FILE`` / ``-O``). This matches
what attack scripts actually do (``curl -s URL | sh``). Like wget here, it never
touches the network — the body is a placeholder and any saved file lands in the
VirtualFS via the shared ``_download`` helpers. Deterministic + VFS-mutating,
so a builtin (HANDOFF2 §4-5).

Supported
---------
``-o FILE`` (write to FILE), ``-O`` (save under the URL's basename), ``-s``/
``--silent`` (no progress meter — we're already quiet, so this mainly affects
error visibility). Unknown flags are ignored.

Deferred
--------
No real transfer, no redirect following (``-L``), no progress meter rendering.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._download import (
    SaveError,
    content_for_stdout,
    head_response,
    normalize_url,
    outfile_from_url,
    placeholder_contents,
    save_to_vfs,
)

__all__ = ["Curl"]


@register("curl", "/usr/bin/curl", "/bin/curl")
class Curl(Command):
    async def run(self) -> int:
        outfile: str | None = None
        use_remote_name = False
        silent = False
        head_only = False
        urls: list[str] = []

        args = self.args
        i = 0
        while i < len(args):
            a = args[i]
            if a == "-o":
                if i + 1 < len(args):
                    outfile = args[i + 1]
                    i += 2
                    continue
                i += 1
                continue
            if a.startswith("-o") and len(a) > 2:
                outfile = a[2:]
                i += 1
                continue
            if a in ("-O", "--remote-name"):
                use_remote_name = True
                i += 1
                continue
            if a in ("-s", "--silent"):
                silent = True
                i += 1
                continue
            if a in ("-I", "--head"):
                head_only = True
                i += 1
                continue
            if a.startswith("-"):
                i += 1  # ignore unknown flags (incl. -L, -k, -A ...)
                continue
            urls.append(a)
            i += 1

        if not urls:
            self.errline("curl: try 'curl --help' or 'curl --manual' for more information")
            return 2

        rc = 0
        for url in urls:
            rc = await self._fetch(
                url, outfile, use_remote_name, silent, head_only) or rc
        return rc

    async def _fetch(self, url: str, outfile: str | None,
                     use_remote_name: bool, silent: bool,
                     head_only: bool = False) -> int:
        parsed = normalize_url(url)
        if parsed is None:
            if not silent:
                self.errline(f"curl: (6) Could not resolve host: {url}")
            return 6

        # -I / --head: print response headers only, no body, no file written.
        # This must short-circuit before the save/stdout body logic, matching
        # real curl (a HEAD request never downloads a body).
        if head_only:
            self.write(head_response(parsed, self.ctx))
            return 0

        # Decide destination: -o FILE, or -O (URL basename), else stdout.
        dest: str | None = None
        if outfile is not None:
            dest = outfile
        elif use_remote_name:
            dest = outfile_from_url(parsed.path)

        if dest is None:
            # Default curl behaviour: body to stdout — LLM-generated when a
            # fetcher is wired, else the placeholder.
            data = await content_for_stdout(self.ctx, parsed.raw)
            self.write(data.decode("utf-8", "replace"))
            return 0

        # Save path: keep the deterministic placeholder.
        data = placeholder_contents(parsed.raw)
        try:
            save_to_vfs(self.ctx, dest, data)
        except SaveError:
            # curl phrases this differently from wget.
            if not silent:
                self.errline(f"Warning: Failed to open the file {dest}: No such file or")
                self.errline("Warning: directory")
                self.errline("curl: (23) Failure writing output to destination")
            return 23
        return 0
