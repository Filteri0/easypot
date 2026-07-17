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

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from honeyshell.backends.cache import CacheEntry, ResponseCache
from honeyshell.backends.client import (
    LLMClient,
    LLMUnavailable,
    extract_json,
)
from honeyshell.backends.prompt_builder import (
    PromptBuilder,
    looks_like_command_not_found,
    parse_result,
)
from honeyshell.core.config import HoneypotConfig, BOOT_AGE_SECONDS
from honeyshell.core.event_bus import EventBus
from honeyshell.core.events import LLMEvent

__all__ = ["Resolution", "ChainResolver"]

_logger = logging.getLogger("honeyshell.backends.resolver")


@dataclass
class Resolution:
    """The resolved response for one command.

    ``fs_ops`` is the structured C_i (list of filesystem-op dicts); the
    LLMCommand applies it to the VirtualFS so the tree matches the narrated
    output. Present on both live and cached resolutions so replay stays
    consistent. ``state_change`` remains the prose fallback for anything the
    model couldn't express structurally.
    """

    output: str
    state_change: str
    impact: int
    cached: bool = False
    fs_ops: list[dict[str, Any]] = field(default_factory=list)


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
    #: 模擬時鐘的開機時間戳（epoch 秒）。預設為「現在往前推 BOOT_AGE_SECONDS」，
    #: 與 session 層一致，讓 LLM 生成 ps/uptime/date 時有真實時間錨點，不再憑空
    #: 亂編（否則 ps 的 START/TIME、date 的輸出會與模擬時鐘矛盾而露餡）。
    boot_time: float = field(default_factory=lambda: time.time() - BOOT_AGE_SECONDS)

    def __post_init__(self) -> None:
        if self.builder is None:
            self.builder = PromptBuilder(self.config)

    async def resolve(
        self,
        argv: list[str],
        cwd: str,
        *,
        username: str = "root",
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
                              cached=True, fs_ops=list(hit.fs_ops))

        # 計算模擬時鐘的「現在」與「開機時間」，餵給 builder 供 inject_time 用。
        # 沒有這個，builder 的 now 一直是 None、inject_time 形同虛設，LLM 生成
        # ps/uptime/date 時只能亂編時間 → 露餡。now 用真實牆鐘（模擬主機的時間就是
        # 現在），boot_time 是固定 7 天前，兩者一致。
        _now = datetime.now(timezone.utc)
        _boot = datetime.fromtimestamp(self.boot_time, timezone.utc)
        now_str = (f"{_now:%Y-%m-%d %H:%M:%S UTC} "
                   f"(booted {_boot:%Y-%m-%d %H:%M:%S UTC})")
        messages = self.builder.build(
            argv, cwd, username=username, sr=sr, history=history, now=now_str
        )
        _logger.debug("querying LLM for %r (cwd=%s)", command, cwd)
        try:
            result = await self.client.chat(messages)
        except LLMUnavailable as exc:
            _logger.warning(
                "LLM unavailable for %r; falling back to command-not-found: %s",
                command, exc,
            )
            return None

        output, state, impact, fs_ops = parse_result(extract_json(result.content))
        _logger.debug(
            "LLM answered %r: impact=%d, %d chars, %d fs_ops, %.0fms",
            command, impact, len(output), len(fs_ops), result.latency_ms,
        )
        self._emit(
            session_id, result.model, result.prompt_tokens,
            result.response_tokens, result.latency_ms, cached=False,
        )

        # B safeguard: if the model gave up and imitated "command not found"
        # (no fs_ops, output is just a not-found line), don't surface its ad-hoc
        # string. Return None so the interpreter emits its own canonical
        # `bash: <cmd>: command not found` — one consistent error, and nothing
        # junk gets cached. A genuine simulated success (has fs_ops, or real
        # output) is never caught by this — see looks_like_command_not_found.
        if looks_like_command_not_found(output, fs_ops):
            _logger.debug(
                "LLM emulated not-found for %r; deferring to interpreter "
                "fallback", command,
            )
            return None

        # Cache low-impact commands *including* their fs_ops, so a replay
        # re-applies the same tree mutation (see CacheEntry.fs_ops).
        if impact <= self.cache_max_impact:
            self.cache.put(command, cwd,
                           CacheEntry(output, state, impact, tuple(fs_ops)))
        return Resolution(output, state, impact, cached=False, fs_ops=fs_ops)

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
