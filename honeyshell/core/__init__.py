"""honeyshell.core — 設定 + 稽核事件匯流排。

HoneyGPT 整合的地基層（HANDOFF §8 建議的第一步）：先有可觀測性與靜態設定，
後續 backends/（LLM 成本統計）與 memory/（記憶事件）才有依附點。

零外部相依（HANDOFF §6）：只用 stdlib，asyncssh 絕不進入本層。
"""

from __future__ import annotations

from .config import (
    HoneypotConfig,
    LLMSettings,
    Principles,
    SystemProfile,
)
from .event_bus import EventBus, Listener, LoggingSink
from .events import (
    CommandEvent,
    DownloadEvent,
    Event,
    EventType,
    LLMEvent,
    LoginEvent,
    SessionEndEvent,
    SessionStartEvent,
)

__all__ = [
    # config
    "HoneypotConfig",
    "Principles",
    "SystemProfile",
    "LLMSettings",
    # event bus
    "EventBus",
    "Listener",
    "LoggingSink",
    # events
    "EventType",
    "Event",
    "SessionStartEvent",
    "SessionEndEvent",
    "LoginEvent",
    "CommandEvent",
    "DownloadEvent",
    "LLMEvent",
]
