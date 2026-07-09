"""honeyshell.memory — dynamic multi-turn memory (paper §3.2.2).

Holds the per-session SR/H/FL structures (:class:`SessionMemory`) and the
Memory Pruning algorithm (:class:`Pruner`: Weaken-Factor decay + impact-ranked
eviction) that keep a long attack dialogue consistent within the model's
context budget. One SessionMemory is attached to each session's ShellContext;
the LLM command records into it and the prompt builder reads SR/H back out.

Zero external dependencies — pure stdlib, like ``core``.
"""

from __future__ import annotations

from honeyshell.memory.pruner import Pruner
from honeyshell.memory.session_memory import Interaction, SessionMemory

__all__ = ["SessionMemory", "Interaction", "Pruner"]
