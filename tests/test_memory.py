"""memory/ unit tests — SessionMemory (SR/H/FL) and Pruner.

Dual-mode (HANDOFF §6):
    pytest tests/test_memory.py
    python tests/test_memory.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeyshell.core.config import MemorySettings  # noqa: E402
from honeyshell.memory import Pruner, SessionMemory  # noqa: E402


# --- SessionMemory -------------------------------------------------------

def test_record_keeps_lists_parallel():
    m = SessionMemory()
    m.record("ls", "a b", "", 0)
    m.record("mkdir x", "", "created /x", 1)
    assert len(m) == 2
    assert m.history == [("ls", "a b"), ("mkdir x", "")]
    assert m.sr == ["", "created /x"]
    assert m.fl == [0.0, 1.0]


def test_sr_notes_filters_blanks():
    m = SessionMemory()
    m.record("ls", "out", "", 0)
    m.record("wget u", "ok", "downloaded /tmp/u", 3)
    assert m.sr_notes() == ["downloaded /tmp/u"]


def test_drop_removes_across_all_structures():
    m = SessionMemory()
    m.record("a", "1", "sa", 0)
    m.record("b", "2", "sb", 2)
    m.drop(0)
    assert m.history == [("b", "2")]
    assert m.sr == ["sb"] and m.fl == [2.0]


def test_drop_out_of_range_is_noop():
    m = SessionMemory()
    m.record("a", "1", "", 0)
    m.drop(5)  # ignored
    m.drop(-1)  # ignored
    assert len(m) == 1


def test_estimated_chars():
    m = SessionMemory()
    m.record("ls", "abc", "note", 0)  # 2 + 3 + 4 = 9
    assert m.estimated_chars() == 9


# --- Pruner: decay -------------------------------------------------------

def test_decay_multiplies_all_impacts():
    m = SessionMemory()
    m.record("a", "", "", 4)
    m.record("b", "", "", 2)
    p = Pruner(MemorySettings(weaken_factor=0.5))
    p.decay(m)
    assert m.fl == [2.0, 1.0]
    p.decay(m)
    assert m.fl == [1.0, 0.5]


# --- Pruner: eviction ----------------------------------------------------

def test_prune_evicts_lowest_impact_first():
    m = SessionMemory()
    m.record("ls", "x", "", 0)         # low
    m.record("wget u", "ok", "dl", 3)  # high — must survive
    m.record("cat f", "data", "", 0)   # low
    # tiny budget forces eviction down to min_keep=1
    p = Pruner(MemorySettings(max_prompt_chars=1, min_keep=1))
    dropped = p.prune(m)
    assert dropped == 2
    assert [h[0] for h in m.history] == ["wget u"]  # high-impact kept


def test_prune_respects_min_keep_floor():
    m = SessionMemory()
    for i in range(5):
        m.record(f"c{i}", "x", "", 0)
    p = Pruner(MemorySettings(max_prompt_chars=1, min_keep=2))
    p.prune(m)
    assert len(m) == 2  # stops at the floor even though still over budget


def test_prune_noop_when_within_budget():
    m = SessionMemory()
    m.record("ls", "x", "", 0)
    p = Pruner(MemorySettings(max_prompt_chars=10_000, min_keep=1))
    assert p.prune(m) == 0 and len(m) == 1


def test_step_decays_then_prunes():
    m = SessionMemory()
    m.record("ls", "x", "", 0)
    m.record("id", "uid=0", "", 0)
    m.record("wget u", "ok", "dl", 4)
    p = Pruner(MemorySettings(weaken_factor=0.8, max_prompt_chars=1, min_keep=1))
    dropped = p.step(m)
    # decayed then pruned to the single highest-impact turn
    assert dropped == 2 and [h[0] for h in m.history] == ["wget u"]
    assert abs(m.fl[0] - 3.2) < 1e-9  # 4 * 0.8


def test_weaken_factor_keeps_old_high_above_new_low():
    """Paper's rationale: a 3-turn-old high-impact command should still
    outrank a fresh low one (F_i * w^3 > F_{i+3})."""
    w = 0.8
    m = SessionMemory()
    m.record("wget u", "ok", "dl", 3)  # high, turn i
    p = Pruner(MemorySettings(weaken_factor=w))
    for _ in range(3):                  # three more turns pass
        p.decay(m)
        m.record("ls", "x", "", 0)      # fresh low turns (but decay first)
    # old high after 3 decays vs a brand-new low (0)
    old_high = m.fl[0]
    assert old_high == 3 * (w ** 3)
    assert old_high > 0  # survives ranking against new impact-0 turns


# --- integration: memory feeds the LLM command ---------------------------

def test_llm_command_records_into_session_memory():
    from honeyshell.backends import ChainResolver, LLMResult, make_llm_command_factory
    from honeyshell.commands import ShellContext, StringWriter
    from honeyshell.core.config import HoneypotConfig
    from honeyshell.fs.build_sample_fs import build
    from honeyshell.shell import Interpreter

    class FakeLLM:
        def __init__(self):
            self.calls = 0
            self.seen_messages = None

        async def chat(self, messages):
            self.calls += 1
            self.seen_messages = messages
            return LLMResult(
                content='{"output": "done", "state_change": "touched /a", '
                        '"impact": 1}',
                model="fake",
            )

    llm = FakeLLM()
    r = ChainResolver(client=llm, config=HoneypotConfig())
    ctx = ShellContext(fs=build(hostname="svr04"), cwd="/root", username="root")
    ctx.memory = SessionMemory()
    ctx.pruner = Pruner(MemorySettings())
    factory = make_llm_command_factory(r)

    def run(line):
        out, err = StringWriter(), StringWriter()
        i = Interpreter(ctx, out, err, miss_handler=factory)
        asyncio.run(i.execute(line))
        return out.getvalue()

    run("frobnicate one")
    run("frobnicate two")
    # both turns recorded in memory
    assert len(ctx.memory) == 2
    assert ctx.memory.history[0][0] == "frobnicate one"
    assert "touched /a" in ctx.memory.sr_notes()
    # second call's prompt carried the first turn as history
    joined = " ".join(msg["content"] for msg in llm.seen_messages)
    assert "frobnicate one" in joined


# --- standalone runner ---------------------------------------------------

def _run_standalone() -> int:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {exc!r}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
