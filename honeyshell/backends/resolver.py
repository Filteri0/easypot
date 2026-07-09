"""Command resolution chain — the hybrid router (paper §3.4).

Order of resolution for a command the interpreter couldn't match in the
registry:

    cache hit  -> return the stored response instantly
    cache miss -> query the LLM, store the result, return it
    LLM down   -> raise/return None so the interpreter falls back to bash's
                  "command not found" (the honeypot must never crash)

The registry stage itself lives in the interpreter (built-in emulated commands
run first); this resolver owns everything past a registry miss. Keeping the two
split matches the paper's design: rule-following commands stay on the cheap
emulated path, novel/context-sensitive ones go to the model.

Emits an :class:`~honeyshell.core.events.LLMEvent` per model interaction (cached
or live) so the audit bus can track cost/latency (paper §4.6).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from honeyshell.backends.cache import CacheEntry, ResponseCache
from honeyshell.backends.client import (
    LLMClient,
    LLMUnavailable,
    extract_json,
)
from honeyshell.backends.prompt_builder import PromptBuilder, parse_result
from honeyshell.core.config import HoneypotConfig
from honeyshell.core.event_bus import EventBus
from honeyshell.core.events import LLMEvent

__all__ = ["Resolution", "ChainResolver"]


@dataclass
class Resolution:
    """The resolved response for one command."""

    output: str
    state_change: str
    impact: int
    cached: bool = False


@dataclass
class ChainResolver:
    """Resolves a registry-missed command via cache then LLM.

    ``cache_max_impact`` gates what gets cached: only responses at or below
    this impact are stored, so state-mutating commands (impact >= 3) are always
    re-evaluated rather than served stale. Read-like commands (impact 0) cache
    freely.
    """

    client: LLMClient
    config: HoneypotConfig
    cache: ResponseCache = field(default_factory=ResponseCache)
    bus: EventBus | None = None
    builder: PromptBuilder | None = None
    cache_max_impact: int = 1

    def __post_init__(self) -> None:
        if self.builder is None:
            self.builder = PromptBuilder(self.config)

    async def resolve(
        self,
        argv: list[str],
        cwd: str,
        *,
        session_id: str | None = None,
        sr: list[str] | None = None,
        history: list[tuple[str, str]] | None = None,
    ) -> Resolution | None:
        """Resolve ``argv``; return None if the LLM is unavailable."""
        command = " ".join(argv)

        hit = self.cache.get(command, cwd)
        if hit is not None:
            self._emit(session_id, self.config.llm.model, 0, 0, 0.0, cached=True)
            return Resolution(hit.output, hit.state_change, hit.impact,
                              cached=True)

        messages = self.builder.build(argv, cwd, sr=sr, history=history)
        try:
            result = await self.client.chat(messages)
        except LLMUnavailable:
            return None

        output, state, impact = parse_result(extract_json(result.content))
        self._emit(
            session_id, result.model, result.prompt_tokens,
            result.response_tokens, result.latency_ms, cached=False,
        )

        if impact <= self.cache_max_impact:
            self.cache.put(command, cwd,
                           CacheEntry(output, state, impact))
        return Resolution(output, state, impact, cached=False)

    def _emit(
        self,
        session_id: str | None,
        model: str,
        ptok: int,
        rtok: int,
        latency_ms: float,
        *,
        cached: bool,
    ) -> None:
        if self.bus is None:
            return
        self.bus.emit(LLMEvent(
            session_id=session_id,
            model=model,
            prompt_tokens=ptok,
            response_tokens=rtok,
            latency_ms=latency_ms,
            cached=cached,
        ))
