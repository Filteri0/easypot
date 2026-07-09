"""LLM client abstraction with a local-Ollama implementation.

Why an abstraction
-------------------
The HoneyGPT paper drives the honeypot with ChatGPT; this deployment targets a
**local** model served by Ollama (``qwen2.5:7b`` by default). We hide the
provider behind a tiny :class:`LLMClient` protocol so the rest of ``backends``
never hard-codes Ollama — a future OpenAI/vLLM client can drop in unchanged.

Dependency policy (mirrors asyncssh in transport)
-------------------------------------------------
``httpx`` is imported lazily and only here. If it (or the Ollama server) is
unavailable, the client raises :class:`LLMUnavailable`; the resolver catches
that and degrades gracefully to bash's ``command not found`` — the honeypot
must never crash because the model is down.

Ollama chat API
---------------
POST ``{base_url}/api/chat`` with ``{model, messages, stream:false, options,
format}``. We request ``format:"json"`` so the model returns a single JSON
object (the paper's structured ``(A_i, C_i, F_i)`` output, §3.3.1). The reply
body is ``{"message": {"content": "..."}, "prompt_eval_count", "eval_count",
...}``; we surface content plus token counts for the audit ``LLMEvent``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "LLMResult",
    "LLMClient",
    "OllamaClient",
    "LLMUnavailable",
]


class LLMUnavailable(RuntimeError):
    """Raised when the model backend can't be reached or errors out.

    The resolver treats this as a signal to fall back to non-LLM behaviour.
    """


@dataclass
class LLMResult:
    """One completion plus the metadata the audit trail needs."""

    content: str
    model: str
    prompt_tokens: int = 0
    response_tokens: int = 0
    latency_ms: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LLMClient(Protocol):
    """Minimal async chat interface every provider must satisfy."""

    async def chat(self, messages: list[dict[str, str]]) -> LLMResult:
        """Send chat ``messages`` ([{role, content}, ...]) and return a result.

        Implementations should raise :class:`LLMUnavailable` on any transport
        or server error rather than leaking provider-specific exceptions.
        """
        ...


@dataclass
class OllamaClient:
    """Talks to a local Ollama server's ``/api/chat`` endpoint.

    ``json_format`` asks Ollama to constrain output to a JSON object, which the
    prompt builder relies on for parsing ``(A_i, C_i, F_i)``. ``options`` maps
    to Ollama's sampling knobs; defaults mirror the paper's low-stochasticity
    setup (§3.3.3: temperature 0.1, top_p 0.95).
    """

    model: str = "qwen2.5:7b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.1
    top_p: float = 0.95
    timeout: float = 30.0
    json_format: bool = True

    async def chat(self, messages: list[dict[str, str]]) -> LLMResult:
        httpx = _import_httpx()
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature, "top_p": self.top_p},
        }
        if self.json_format:
            payload["format"] = "json"

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat", json=payload
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001 — normalise to one error type
            raise LLMUnavailable(f"ollama chat failed: {exc}") from exc

        latency_ms = (time.perf_counter() - started) * 1000.0
        content = (data.get("message") or {}).get("content", "")
        return LLMResult(
            content=content,
            model=self.model,
            prompt_tokens=int(data.get("prompt_eval_count", 0) or 0),
            response_tokens=int(data.get("eval_count", 0) or 0),
            latency_ms=latency_ms,
            raw=data,
        )

    async def is_available(self) -> bool:
        """Best-effort probe: True if the Ollama server answers ``/api/tags``."""
        try:
            httpx = _import_httpx()
        except LLMUnavailable:
            return False
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:  # noqa: BLE001
            return False


def _import_httpx():
    """Lazily import httpx; raise LLMUnavailable if it isn't installed."""
    try:
        import httpx  # noqa: PLC0415 — intentional lazy import
    except ImportError as exc:  # pragma: no cover
        raise LLMUnavailable(
            "httpx is not installed; run: pip install httpx"
        ) from exc
    return httpx


# JSON helper kept here so both client and tests can share one parser.
def extract_json(text: str) -> dict[str, Any] | None:
    """Best-effort parse of a JSON object from ``text``.

    Ollama's ``format:"json"`` normally yields a clean object, but smaller
    models occasionally wrap it in prose or code fences. We try a strict parse
    first, then fall back to the outermost ``{...}`` slice. Returns None if no
    object can be recovered.
    """
    text = text.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            obj = json.loads(text[start:end + 1])
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None
    return None
