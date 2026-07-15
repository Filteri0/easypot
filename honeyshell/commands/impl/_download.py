"""Shared helpers for the download builtins (wget/curl/tftp/ftpget).

Design lineage
--------------
Cowrie's wget/curl actually fetch the URL over the network and store a forensic
artifact. This honeypot does **not** touch the network: like the LLM path's
``fetch-payload`` demo, a download is *simulated* — we synthesise believable
console output and write a placeholder file into the VirtualFS so the session
stays self-consistent (``ls``/``cat`` afterwards agree that the file exists).

This mirrors the paper's hybrid design (§3.4): deterministic, VFS-mutating,
frequently-seen commands stay on the cheap builtin path rather than the model,
and — crucially — they mutate the single source of truth (the VFS) so state is
coherent across turns (HANDOFF2 §4-5).

Underscore-prefixed so the registry's ``discover()`` imports it harmlessly
(it registers no command).

Deferred
--------
No real transfer, no redirect following, no rate limiting. Content is a fixed
placeholder (option A, agreed with the user), not the real payload.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from honeyshell.commands.context import ShellContext
from honeyshell.fs import FSError

__all__ = [
    "ParsedURL",
    "normalize_url",
    "outfile_from_url",
    "placeholder_contents",
    "content_for_stdout",
    "save_to_vfs",
    "SaveError",
    "head_response",
]


@dataclass
class ParsedURL:
    """The pieces of a URL a download command cares about."""

    scheme: str
    host: str
    port: int
    path: str
    raw: str  # the (possibly http://-prefixed) URL as a string


_DEFAULT_PORTS = {"http": 80, "https": 443, "ftp": 21, "tftp": 69}


def normalize_url(url: str, default_scheme: str = "http") -> ParsedURL | None:
    """Parse ``url``, prefixing ``http://`` when no scheme is present.

    Returns None when the URL has no usable host (caller prints the usage
    error). Mirrors wget: ``example.com/x`` becomes ``http://example.com/x``.
    """
    raw = url if "://" in url else f"{default_scheme}://{url}"
    u = urlparse(raw)
    if not u.hostname:
        return None
    scheme = (u.scheme or default_scheme).lower()
    port = u.port if u.port is not None else _DEFAULT_PORTS.get(scheme, 80)
    return ParsedURL(scheme=scheme, host=u.hostname, port=port,
                     path=u.path, raw=raw)


def outfile_from_url(path: str) -> str:
    """Derive wget's default output filename from a URL path.

    The last path segment, or ``index.html`` when the path is empty or has no
    ``/`` (matching GNU wget's behaviour).
    """
    name = path.split("/")[-1]
    if not name.strip() or "/" not in path:
        return "index.html"
    return name


def placeholder_contents(url: str) -> bytes:
    """The stand-in payload written into the VFS for a simulated download.

    Option A: a short, believable placeholder rather than the real payload
    (we never fetch it). Deterministic so the file's size lines up with what
    the progress meter prints — keeping ``ls -l`` and the download output
    self-consistent.
    """
    return f"# downloaded from {url}\n".encode()


async def content_for_stdout(ctx: ShellContext, url: str) -> bytes:
    """Body for the *stdout* path (``curl URL`` / ``wget -O -`` / ``| sh``).

    Prefer LLM-generated content via ``ctx.fetch_content`` so a real URL yields
    believable output; fall back to the placeholder when no fetcher is wired or
    the model can't produce one. The *save* path deliberately does NOT use this
    — it keeps the placeholder (see module docstring).
    """
    if ctx.fetch_content is not None:
        try:
            data = await ctx.fetch_content(url)
        except Exception:  # noqa: BLE001 — a broken fetcher must not crash us
            data = None
        if data:
            # Ensure a trailing newline so the next shell prompt starts on its
            # own line (a real body often ends in \n; models frequently omit
            # it, which would glue the prompt onto the last line of output).
            if not data.endswith(b"\n"):
                data += b"\n"
            return data
    return placeholder_contents(url)


class SaveError(Exception):
    """Raised when the destination can't be written (e.g. missing directory).

    Carries a human-readable ``message`` the command formats into its own
    error style (wget vs curl word their errors differently).
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def save_to_vfs(ctx: ShellContext, outfile: str, data: bytes) -> int:
    """Write ``data`` to ``outfile`` in the VFS; return the byte count.

    Validates the parent directory exists (raises :class:`SaveError` with a
    ``No such file or directory`` message otherwise), then writes the file as
    the session user. This is the C_i-write-back step: the download really
    changes the VirtualFS, so subsequent ``ls``/``cat`` see the new file.
    """
    norm = ctx.fs.normalize(outfile, ctx.cwd)
    parent = norm.rsplit("/", 1)[0] or "/"
    if not ctx.fs.exists(parent, ctx.cwd) or not ctx.fs.stat(parent, ctx.cwd).is_dir:
        raise SaveError(f"{outfile}: Cannot open: No such file or directory")
    try:
        ctx.fs.write_file(norm, data, ctx.cwd, uid=ctx.uid, gid=ctx.uid)
    except FSError as e:
        raise SaveError(f"{outfile}: {e.message}") from e
    return len(data)


def head_response(parsed: "ParsedURL", ctx: ShellContext) -> str:
    """Synthesise the response headers curl prints for ``-I`` / ``--head``.

    curl -I issues an HTTP HEAD and prints the status line + response headers,
    no body. We never touch the network, so we emit a believable, deterministic
    header block. The ``Date`` header reads the emulated clock (``ctx.now()``)
    so it agrees with ``date`` / file mtimes instead of leaking real wall-clock.
    Lines are CR-terminated the way curl renders wire headers.
    """
    import time as _t
    now = ctx.now() if hasattr(ctx, "now") else _t.time()
    date = _t.strftime("%a, %d %b %Y %H:%M:%S GMT", _t.gmtime(now))
    server = "nginx" if parsed.port in (80, 443) else "nginx"
    lines = [
        "HTTP/1.1 200 OK",
        f"Server: {server}",
        f"Date: {date}",
        "Content-Type: text/html; charset=UTF-8",
        "Content-Length: 1256",
        "Connection: keep-alive",
        "Last-Modified: Mon, 12 Jun 2023 09:41:07 GMT",
        "ETag: \"64870ab3-4e8\"",
        "Accept-Ranges: bytes",
    ]
    # curl separates each header with CRLF and prints a trailing blank line.
    return "".join(f"{ln}\r\n" for ln in lines) + "\r\n"
