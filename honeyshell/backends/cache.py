"""Response cache for the hybrid deployment (paper §3.4).

Attackers repeat themselves heavily in the wild (the paper's field study notes
this), so caching resolved ``(command, cwd) -> (A_i, C_i, F_i)`` responses
avoids re-querying the model for identical requests. For a local Ollama model
there's no per-call fee, but there IS latency; the cache keeps repeat commands
instant and cuts load.

Scope & correctness
-------------------
The cache key intentionally includes ``cwd`` because the same command yields
different output in different directories (``ls`` etc.). It does NOT capture
full system state, so it's only sound for commands whose output depends on
(command, cwd) alone; callers should cache read-like, low-impact commands and
may choose to skip caching state-mutating ones. Kept in-memory by default;
optional JSON persistence lets a deployment warm the cache across restarts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["ResponseCache", "CacheEntry"]


@dataclass(frozen=True)
class CacheEntry:
    output: str
    state_change: str
    impact: int
    # Structured C_i. Stored so a cache *hit* re-applies the same VFS mutation
    # the live call would have (e.g. a cached "mkdir /tmp/x" still creates the
    # dir on replay). Without this, a low-impact create/touch — which IS cached
    # (impact 1 <= cache_max_impact) — would desync the tree on its second run.
    # Tuple (not list) so the frozen dataclass stays hashable-friendly; the
    # applier accepts any sequence of dicts.
    fs_ops: tuple[dict[str, Any], ...] = ()


@dataclass
class ResponseCache:
    """In-memory (command, cwd) -> CacheEntry store with optional JSON file."""

    _data: dict[str, CacheEntry] = field(default_factory=dict)

    @staticmethod
    def _key(command: str, cwd: str) -> str:
        return f"{cwd}\x00{command}"

    def get(self, command: str, cwd: str) -> CacheEntry | None:
        return self._data.get(self._key(command, cwd))

    def put(
        self, command: str, cwd: str, entry: CacheEntry
    ) -> None:
        self._data[self._key(command, cwd)] = entry

    def __len__(self) -> int:
        return len(self._data)

    # -- optional persistence --

    def save(self, path: str | Path) -> None:
        obj = {
            k: {"output": e.output, "state_change": e.state_change,
                "impact": e.impact, "fs_ops": list(e.fs_ops)}
            for k, e in self._data.items()
        }
        Path(path).write_text(json.dumps(obj, ensure_ascii=False),
                              encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "ResponseCache":
        p = Path(path)
        if not p.exists():
            return cls()
        obj = json.loads(p.read_text(encoding="utf-8"))
        data = {
            k: CacheEntry(
                v.get("output", ""), v.get("state_change", ""),
                int(v.get("impact", 0)),
                tuple(v.get("fs_ops", []) or []),
            )
            for k, v in obj.items()
        }
        return cls(_data=data)
