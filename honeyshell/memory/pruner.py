"""Pruner — Memory Pruning with a Weaken Factor (paper §3.2.2).

As a session grows, H_i lengthens and the prompt eventually exceeds the model's
context window. The paper keeps the most useful history within that budget by:

1. **Time decay.** Each turn, every stored impact F_j is multiplied by a Weaken
   Factor w (< 1), so older commands fade. w is chosen so a high-impact command
   from three turns ago still outranks a fresh one (F_i·w³ > F_{i+3}); the paper
   derives w ∈ (0.623, 1] and uses 0.8.

2. **Impact-ranked eviction.** When the prompt approaches its limit, drop the
   turn with the smallest (decayed) F — the least consequential history — and
   repeat until it fits. The "write-elevate-execute" chain thus survives while
   idle `ls`/`cat` turns are shed first.

We measure "length" with a tokenizer-free character estimate (see
SessionMemory.estimated_chars), which is stable and needs no extra model call.
A ``min_keep`` floor prevents evicting the most recent turns that form the
current context.
"""

from __future__ import annotations

from dataclasses import dataclass

from honeyshell.core.config import MemorySettings
from honeyshell.memory.session_memory import SessionMemory

__all__ = ["Pruner"]


@dataclass
class Pruner:
    """Applies decay and eviction to a SessionMemory per the paper."""

    settings: MemorySettings

    def decay(self, memory: SessionMemory) -> None:
        """Multiply every stored impact by the Weaken Factor w.

        Call once per interaction (after recording the new turn). The newest
        turn is included; that's fine — w applied once to a fresh high value
        still leaves it well above decayed old low values.
        """
        w = self.settings.weaken_factor
        memory.fl = [f * w for f in memory.fl]

    def prune(self, memory: SessionMemory) -> int:
        """Evict lowest-impact turns until the estimate fits the budget.

        Returns the number of turns dropped. Eviction is purely by smallest
        (decayed) impact F — the paper's rule — so a high-impact command like
        ``wget``/privilege-escalation survives while idle reads are shed first.
        ``min_keep`` is a floor on the *total* number of turns retained (stop
        pruning once only that many remain), NOT a protection of the most
        recent turns; protecting recency would perversely force evicting a
        high-F turn to keep a low-F newer one.
        """
        dropped = 0
        limit = self.settings.max_prompt_chars
        floor = max(0, self.settings.min_keep)

        while memory.estimated_chars() > limit and len(memory) > floor:
            idx = self._argmin(memory)
            if idx is None:
                break
            memory.drop(idx)
            dropped += 1
        return dropped

    def step(self, memory: SessionMemory) -> int:
        """Convenience: decay then prune. Returns turns dropped."""
        self.decay(memory)
        return self.prune(memory)

    @staticmethod
    def _argmin(memory: SessionMemory) -> int | None:
        """Index of the smallest-impact turn (ties: the oldest such turn).

        Returns None on empty memory. Oldest-on-tie means equal-impact idle
        turns are shed front-to-back, roughly oldest-first.
        """
        n = len(memory)
        if n == 0:
            return None
        best_idx = 0
        best_val = memory.fl[0]
        for i in range(1, n):
            if memory.fl[i] < best_val:
                best_val = memory.fl[i]
                best_idx = i
        return best_idx
