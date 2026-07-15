"""LLM-backed content generation for the download builtins (curl/wget).

Why this exists
---------------
curl/wget don't touch the network. On the *save* path a static placeholder is
fine (nobody cats a downloaded binary). But on the *stdout* path — ``curl URL``,
``wget URL -O -``, and especially ``curl URL | sh`` — the attacker sees the body
directly, and a ``# downloaded from ...`` placeholder is an obvious tell. This
fetcher asks the LLM to synthesise believable content for a URL, turning
``curl https://.../install.sh`` into a plausible script and
``curl https://site`` into plausible HTML.

This is the paper's spirit (§3.4 hybrid): generate dynamic, believable content
with the model instead of a rigid canned response — but only where it pays off
(the stdout path), and always with a placeholder fallback so a missing/broken
model never breaks the honeypot.

Design notes
------------
* **Session-scoped cache (option A).** The same URL must return the same body
  within a session, or ``curl x`` twice (or ``curl x | sh`` re-run) would show
  different content and expose the emulation. We cache per-URL in memory for
  the session's lifetime; no cross-session persistence (kept deliberately
  simple).
* **Plain-text, not JSON.** Unlike the command-simulation path (which parses
  ``(A_i, C_i, F_i)`` from JSON), here we want the raw body, so we use a
  dedicated text prompt and a non-JSON client call.
* **Resilient.** Any model error -> return None -> the command falls back to
  the placeholder. The honeypot never crashes on a bad model (HANDOFF2 §4-2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from honeyshell.backends.client import LLMClient, LLMUnavailable

__all__ = ["ContentFetcher", "build_content_messages"]

_MAX_BODY_BYTES = 64 * 1024  # cap generated bodies so a runaway model can't flood


def build_content_messages(url: str) -> list[dict[str, str]]:
    """Prompt the model to emit *only* the body a GET of ``url`` would return.

    Kept deliberately tight: the model tends to wrap output in prose or code
    fences, which would leak into the terminal. We tell it to return the raw
    bytes and nothing else. (Fence stripping is done on the result as a second
    line of defence.)
    """
    system = (
        "You are a web server. The user will give you a URL. "
        "Respond with ONLY the raw response body that a GET request to that URL "
        "would return — no explanations, no markdown code fences, no commentary. "
        "For a shell installer URL (e.g. install.sh) return a plausible POSIX "
        "shell script. For a web page return plausible HTML. For a raw file "
        "return its likely contents. Output the body and nothing else."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": url},
    ]


def _strip_code_fences(text: str) -> str:
    """Remove a wrapping ```...``` fence if the model added one anyway."""
    t = text.strip()
    if t.startswith("```"):
        # drop the first fence line (``` or ```sh) and a trailing fence
        lines = t.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        t = "\n".join(lines)
    return t


@dataclass
class ContentFetcher:
    """Generate (and cache) URL bodies via an :class:`LLMClient`.

    Instantiated once per connection alongside the LLM backend and wired to
    ``ctx.fetch_content``. ``__call__`` is the hook the commands invoke.
    """

    client: LLMClient
    _cache: dict[str, bytes] = field(default_factory=dict)

    async def __call__(self, url: str) -> bytes | None:
        if url in self._cache:
            return self._cache[url]
        try:
            result = await self.client.chat(build_content_messages(url))
        except LLMUnavailable:
            return None
        except Exception:  # noqa: BLE001 — never crash the session on the model
            return None
        body = _strip_code_fences(result.content or "")
        if not body:
            return None
        data = body.encode("utf-8", "replace")[:_MAX_BODY_BYTES]
        self._cache[url] = data
        return data
