"""SessionMemory — the paper's dynamic memory (SR_i, H_i, FL).

HoneyGPT feeds each LLM turn with prior context so multi-turn attacks stay
consistent:

    (A_i, C_i, F_i) = LLM(P, S, Q_i, SR_i, H_i)

This class holds the three per-session structures, kept index-parallel so
pruning can drop a turn from all of them at once:

* ``history`` : H_i — list of (command Q, output A) pairs.
* ``sr``      : SR_i — list of state-change notes C (one per turn; "" if none).
* ``fl``      : FL  — list of impact factors F (Table 1, 0–4), later decayed by
                the Weaken Factor and used by the pruner to pick what to drop.

One SessionMemory lives per SSH connection (like the per-session VFS) and is
attached to the ShellContext as ``ctx.memory``. The LLM command records each
interaction here; the prompt builder reads ``sr``/``history`` back out.

Design note — why parallel lists, not a list of records
------------------------------------------------------
The paper treats H, SR and FL as three sequences updated in lockstep, and the
pruning algorithm indexes into them by position (remove the j-th entry from H
and FL). Mirroring that structure keeps the pruner a direct translation of the
paper rather than an abstraction over it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["SessionMemory", "Interaction"]


@dataclass
class Interaction:
    """One recorded turn (a convenience view; storage stays in parallel lists)."""

    command: str
    output: str
    state_change: str
    impact: float


@dataclass
class SessionMemory:
    """Per-session SR/H/FL, updated after every LLM interaction."""

    history: list[tuple[str, str]] = field(default_factory=list)
    sr: list[str] = field(default_factory=list)
    fl: list[float] = field(default_factory=list)

    def record(
        self, command: str, output: str, state_change: str, impact: float
    ) -> None:
        """Append one interaction across all three parallel structures.

        A blank ``state_change`` still appends an empty SR slot so the three
        lists stay index-aligned with ``history``/``fl``.
        """
        self.history.append((command, output))
        self.sr.append(state_change or "")
        self.fl.append(float(impact))

    def sr_notes(self) -> list[str]:
        """Non-empty state-change notes, for injection into the prompt (SR_i)."""
        return [s for s in self.sr if s]

    def as_history(self) -> list[tuple[str, str]]:
        """The (command, output) history for the prompt (H_i)."""
        return list(self.history)

    def drop(self, index: int) -> None:
        """Remove the turn at ``index`` from all three structures.

        Used by the pruner. Out-of-range indices are ignored so a caller can't
        crash the session by mispruning.
        """
        if 0 <= index < len(self.history):
            del self.history[index]
            del self.sr[index]
            del self.fl[index]

    def estimated_chars(self) -> int:
        """Rough size of the memory when rendered into a prompt.

        Counts command + output + state-change characters across all turns.
        Used as a tokenizer-free proxy for prompt length (~4 chars/token); the
        pruner compares this against ``max_prompt_chars``.
        """
        total = 0
        for (cmd, out), note in zip(self.history, self.sr):
            total += len(cmd) + len(out) + len(note)
        return total

    def __len__(self) -> int:
        return len(self.history)
