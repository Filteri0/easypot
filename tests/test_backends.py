"""backends/ unit tests — fully offline via a fake LLM client.

Dual-mode (HANDOFF §6):
    pytest tests/test_backends.py
    python tests/test_backends.py

A real Ollama round-trip is covered separately in test_ollama_integration.py,
which skips when localhost:11434 is unreachable.
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeyshell.backends import (  # noqa: E402
    CacheEntry,
    ChainResolver,
    LLMResult,
    OllamaClient,
    PromptBuilder,
    ResponseCache,
    extract_json,
    make_llm_command_factory,
    parse_result,
)
from honeyshell.backends.client import LLMUnavailable  # noqa: E402
from honeyshell.commands import ShellContext, StringReader, StringWriter  # noqa: E402
from honeyshell.core import EventBus, EventType, HoneypotConfig  # noqa: E402
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402
from honeyshell.shell import Interpreter  # noqa: E402


# --- fakes ---------------------------------------------------------------

class FakeLLM:
    """Returns a canned JSON reply; records how many times it was called."""

    def __init__(self, content: str, model: str = "fake") -> None:
        self.content = content
        self.model = model
        self.calls = 0

    async def chat(self, messages):
        self.calls += 1
        return LLMResult(content=self.content, model=self.model,
                         prompt_tokens=10, response_tokens=5, latency_ms=1.0)


class DownLLM:
    async def chat(self, messages):
        raise LLMUnavailable("down")


def _cfg() -> HoneypotConfig:
    cfg = HoneypotConfig()
    cfg.system.hostname = "svr04"
    return cfg


def _ctx(cwd="/root"):
    return ShellContext(fs=build_sample_fs(hostname="svr04"), cwd=cwd,
                        username="root")


# --- json / parsing ------------------------------------------------------

def test_extract_json_clean():
    assert extract_json('{"output": "hi", "impact": 0}') == {
        "output": "hi", "impact": 0}


def test_extract_json_from_fenced():
    obj = extract_json('```json\n{"output": "x"}\n```')
    assert obj == {"output": "x"}


def test_extract_json_garbage_returns_none():
    assert extract_json("not json at all") is None


def test_parse_result_normalises():
    # parse_result now returns a 4-tuple (A, C, F, fs_ops); fs_ops defaults [].
    assert parse_result({"output": "root", "state_change": "none",
                         "impact": "3"}) == ("root", "", 3, [])
    # out-of-range impact clamps; missing keys default
    assert parse_result({"impact": 99}) == ("", "", 4, [])
    assert parse_result(None) == ("", "", 0, [])


def test_parse_result_extracts_fs_ops():
    ops = [{"op": "mkdir", "path": "/tmp/x"}]
    a, c, f, got = parse_result(
        {"output": "", "state_change": "made dir", "impact": 1, "fs_ops": ops}
    )
    assert (a, c, f) == ("", "made dir", 1)
    assert got == ops
    # a non-list fs_ops is coerced to []
    assert parse_result({"fs_ops": "nope"})[3] == []


# --- prompt builder ------------------------------------------------------

def test_prompt_builder_shapes_messages():
    b = PromptBuilder(_cfg())
    msgs = b.build(["uname", "-a"], "/root")
    assert msgs[0]["role"] == "system"
    assert "svr04" in msgs[0]["content"]
    assert "0-4" in msgs[0]["content"] or "0–4" in msgs[0]["content"]
    # last message carries the actual command + cwd
    assert msgs[-1]["role"] == "user"
    assert "uname -a" in msgs[-1]["content"] and "/root" in msgs[-1]["content"]


def test_system_prompt_instructs_play_along_not_judge():
    """C: the persona must tell the model NOT to judge command existence and to
    succeed on unknown/attacker tools — the fix for the not-found failure."""
    sys_msg = PromptBuilder(_cfg()).build(["x"], "/root")[0]["content"].lower()
    assert "not a judge" in sys_msg
    assert "command not found" in sys_msg  # in the "never answer with" rule
    assert "when unsure" in sys_msg  # succeed-by-default guidance


def test_system_prompt_forbids_helpful_ai_tone():
    """The cold-bash rules: the persona must explicitly forbid the explanatory,
    helpful-assistant voice (e.g. qwen's "isn't installed, using apt-get
    instead...") that is the biggest AI tell."""
    sys_msg = PromptBuilder(_cfg()).build(["x"], "/root")[0]["content"].lower()
    assert "cold" in sys_msg and "machine-like" in sys_msg
    assert "never explains" in sys_msg or "never explain" in sys_msg
    # the specific failure phrasing is called out as forbidden
    assert "instead" in sys_msg
    assert "biggest tell" in sys_msg


def test_fewshot_includes_unknown_tool_success_examples():
    """A: the exemplars must demonstrate an unknown downloader/installer
    SUCCEEDING with fs_ops, and all 6 pairs must reach the message list."""
    msgs = PromptBuilder(_cfg()).build(["x"], "/root")
    joined = " ".join(m["content"] for m in msgs)
    # the two 'play along' anchors are present
    assert "fetch-payload" in joined
    assert "install-miner" in joined
    # they carry fs_ops (simulated success writes to the tree)
    assert "write_file" in joined
    # 6 few-shot pairs (12 msgs) + system + final user = 14 messages
    assert len(msgs) == 14


# --- cache ---------------------------------------------------------------

def test_cache_put_get_keyed_by_cwd():
    c = ResponseCache()
    c.put("ls", "/root", CacheEntry("a", "", 0))
    assert c.get("ls", "/root").output == "a"
    assert c.get("ls", "/tmp") is None  # different cwd -> miss


def test_cache_roundtrip(tmp_path=None):
    import tempfile
    c = ResponseCache()
    c.put("id", "/root", CacheEntry("uid=0", "", 0))
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "c.json")
        c.save(p)
        c2 = ResponseCache.load(p)
    assert c2.get("id", "/root").output == "uid=0"


# --- resolver ------------------------------------------------------------

def test_resolver_calls_llm_then_caches_low_impact():
    llm = FakeLLM('{"output": "Linux svr04", "state_change": "none", '
                  '"impact": 0}')
    r = ChainResolver(client=llm, config=_cfg())
    res = asyncio.run(r.resolve(["uname"], "/root"))
    assert res.output == "Linux svr04" and res.impact == 0 and not res.cached
    # second call served from cache, LLM not hit again
    res2 = asyncio.run(r.resolve(["uname"], "/root"))
    assert res2.cached and llm.calls == 1


def test_resolver_does_not_cache_high_impact():
    llm = FakeLLM('{"output": "", "state_change": "deleted /etc", "impact": 4}')
    r = ChainResolver(client=llm, config=_cfg())
    asyncio.run(r.resolve(["rm", "-rf", "/etc"], "/root"))
    asyncio.run(r.resolve(["rm", "-rf", "/etc"], "/root"))
    assert llm.calls == 2  # high impact re-evaluated each time


def test_resolver_emits_llm_event():
    llm = FakeLLM('{"output": "x", "impact": 0}')
    bus = EventBus()
    seen = []
    bus.subscribe(seen.append, EventType.LLM)
    r = ChainResolver(client=llm, config=_cfg(), bus=bus)
    asyncio.run(r.resolve(["whoami"], "/root", session_id="s1"))
    assert len(seen) == 1 and seen[0].model == "fake"
    assert seen[0].prompt_tokens == 10 and not seen[0].cached


def test_resolver_returns_none_when_llm_down():
    r = ChainResolver(client=DownLLM(), config=_cfg())
    assert asyncio.run(r.resolve(["foo"], "/root")) is None


# --- llm command + interpreter seam --------------------------------------

def _run_line(line, resolver, ctx=None):
    ctx = ctx or _ctx()
    out, err = StringWriter(), StringWriter()
    factory = make_llm_command_factory(resolver, session_id="s1")
    interp = Interpreter(ctx, out, err, miss_handler=factory)
    code = asyncio.run(interp.execute(line))
    return code, out.getvalue(), err.getvalue(), ctx


def test_interpreter_miss_routes_to_llm():
    # Use a command that is NOT a builtin so it reaches the LLM. (uname/mkdir
    # are now emulated builtins and correctly bypass the model.)
    llm = FakeLLM('{"output": "frob complete", "state_change": "none", '
                  '"impact": 0}')
    r = ChainResolver(client=llm, config=_cfg())
    code, out, err, ctx = _run_line("frobnicate --now", r)
    assert code == 0
    assert out == "frob complete\n"
    assert err == ""
    assert llm.calls == 1


def test_interpreter_builtin_still_wins_over_llm():
    """A registry hit (echo) must NOT reach the LLM."""
    llm = FakeLLM('{"output": "SHOULD_NOT_APPEAR", "impact": 0}')
    r = ChainResolver(client=llm, config=_cfg())
    code, out, err, ctx = _run_line("echo hello", r)
    assert out == "hello\n" and llm.calls == 0


def test_interpreter_llm_down_falls_back_to_not_found():
    r = ChainResolver(client=DownLLM(), config=_cfg())
    code, out, err, ctx = _run_line("frobnicate", r)
    assert code == 127 and "command not found" in err


# --- B safeguard: LLM emulating "command not found" -> interpreter fallback --

def test_looks_like_command_not_found_positives():
    from honeyshell.backends import looks_like_command_not_found as lk
    assert lk("bash: foo: command not found", [])
    assert lk("foo: command not found", [])
    assert lk("sh: 1: foo: not found", [])
    assert lk("-bash: baz: command not found", [])
    assert lk("  frobnicate: command not found  ", [])  # whitespace tolerated


def test_looks_like_command_not_found_negatives():
    from honeyshell.backends import looks_like_command_not_found as lk
    # any fs_ops present -> it's a real simulated action, never a giveup
    assert not lk("foo: command not found", [{"op": "touch", "path": "x"}])
    # empty output -> not a not-found line
    assert not lk("", [])
    # "not found" mid-text (e.g. grep/search output) must NOT match (end-anchor)
    assert not lk("Searching... pattern not found in 3 files, then continuing",
                  [])
    # long output that merely ends oddly is capped out
    assert not lk("x" * 200 + "command not found", [])


def test_resolver_defers_emulated_not_found_to_interpreter():
    """When the model imitates a not-found error with no fs_ops, the resolver
    returns None so the interpreter prints its OWN canonical
    'bash: <cmd>: command not found' — not the model's ad-hoc string."""
    llm = FakeLLM('{"output": "fetch-payload: command not found", '
                  '"state_change": "none", "fs_ops": [], "impact": 0}')
    r = ChainResolver(client=llm, config=_cfg())
    code, out, err, ctx = _run_line("fetch-payload", r)
    assert code == 127
    # the interpreter's canonical form, with the bash: prefix
    assert "bash: fetch-payload: command not found" in err
    # the model's own string is not what the attacker sees
    assert out == ""


def test_resolver_keeps_simulated_success_with_fs_ops():
    """A simulated success carrying fs_ops must pass through untouched even if
    its output somehow mentions 'not found' — fs_ops presence guards it."""
    llm = FakeLLM('{"output": "downloaded; signature not found", '
                  '"state_change": "wrote /tmp/x", '
                  '"fs_ops": [{"op": "write_file", "path": "/tmp/x", '
                  '"content": "data"}], "impact": 3}')
    r = ChainResolver(client=llm, config=_cfg())
    code, out, err, ctx = _run_line("fetch-payload -o /tmp/x", r)
    assert code == 0
    assert "downloaded" in out
    assert ctx.fs.is_file("/tmp/x")  # fs_op applied, not deferred


def test_llm_command_records_state_log():
    # LLM state_change/impact now land in ctx.memory (SR/H/FL), the memory
    # milestone's home for this data. mkdir/uname are builtins, so use a
    # non-builtin command that goes through the LLM.
    from honeyshell.core.config import MemorySettings
    from honeyshell.memory import Pruner, SessionMemory

    llm = FakeLLM('{"output": "", "state_change": "installed toolkit", '
                  '"impact": 1}')
    r = ChainResolver(client=llm, config=_cfg())
    ctx = _ctx()
    ctx.memory = SessionMemory()
    ctx.pruner = Pruner(MemorySettings())
    _run_line("install-toolkit", r, ctx=ctx)
    assert len(ctx.memory) == 1
    assert ctx.memory.sr_notes() == ["installed toolkit"]
    assert ctx.memory.fl[0] == 1.0 * MemorySettings().weaken_factor  # decayed


# --- C_i -> VFS write-back (HANDOFF "最大整合風險") -----------------------

def test_llm_fs_op_creates_file_visible_to_ls():
    """The core consistency guarantee: an LLM that narrates creating a file
    actually mutates the VFS, so a follow-up `ls`/`cat` sees it."""
    llm = FakeLLM(
        '{"output": "", "state_change": "created payload", '
        '"fs_ops": [{"op": "write_file", "path": "/tmp/payload.sh", '
        '"content": "echo pwned\\n"}], "impact": 2}'
    )
    r = ChainResolver(client=llm, config=_cfg())
    ctx = _ctx()
    # the sample fs has /tmp; run an unknown command so it routes to the LLM
    _run_line("drop-payload", r, ctx=ctx)
    assert ctx.fs.is_file("/tmp/payload.sh")
    assert ctx.fs.readtext("/tmp/payload.sh") == "echo pwned\n"


def test_llm_fs_op_impact_is_derived_not_trusted():
    """When ops apply, SR note + impact come from the applier, overriding the
    model's own (here deliberately wrong) impact/state_change."""
    from honeyshell.core.config import MemorySettings
    from honeyshell.memory import Pruner, SessionMemory

    llm = FakeLLM(
        '{"output": "", "state_change": "totally harmless", '
        '"fs_ops": [{"op": "rm", "path": "/tmp"}], "impact": 0}'
    )
    r = ChainResolver(client=llm, config=_cfg())
    ctx = _ctx()
    ctx.memory = SessionMemory()
    ctx.pruner = Pruner(MemorySettings())
    _run_line("nuke", r, ctx=ctx)
    assert not ctx.fs.exists("/tmp")  # actually removed
    # FL records derived impact 4 (rm), decayed once by w — not the model's 0.
    assert ctx.memory.fl[0] == 4.0 * MemorySettings().weaken_factor
    # SR note reflects what the applier did, not the model's fib.
    assert "removed" in ctx.memory.sr_notes()[0]


def test_llm_prose_state_change_used_when_no_fs_ops():
    """Non-structural changes (e.g. 'started a service') keep the prose C_i and
    the model's self-scored impact — the fallback path stays intact."""
    from honeyshell.core.config import MemorySettings
    from honeyshell.memory import Pruner, SessionMemory

    llm = FakeLLM(
        '{"output": "", "state_change": "started nginx", '
        '"fs_ops": [], "impact": 3}'
    )
    r = ChainResolver(client=llm, config=_cfg())
    ctx = _ctx()
    ctx.memory = SessionMemory()
    ctx.pruner = Pruner(MemorySettings())
    _run_line("svc-up", r, ctx=ctx)
    assert ctx.memory.sr_notes() == ["started nginx"]
    assert ctx.memory.fl[0] == 3.0 * MemorySettings().weaken_factor


def test_cached_fs_op_reapplies_on_replay():
    """A cached create (impact 1 <= cache_max_impact) must still mutate the VFS
    on its second run in a fresh session — cache carries fs_ops."""
    llm = FakeLLM(
        '{"output": "", "state_change": "made dir", '
        '"fs_ops": [{"op": "mkdir", "path": "/tmp/cached"}], "impact": 1}'
    )
    r = ChainResolver(client=llm, config=_cfg())  # shared cache

    ctx1 = _ctx()
    _run_line("mkcache", r, ctx=ctx1)
    assert ctx1.fs.is_dir("/tmp/cached") and llm.calls == 1

    # second session: same command hits cache (no LLM call) but VFS still changes
    ctx2 = _ctx()
    _run_line("mkcache", r, ctx=ctx2)
    assert ctx2.fs.is_dir("/tmp/cached")
    assert llm.calls == 1  # served from cache, model not re-queried


def test_no_miss_handler_keeps_bash_behaviour():
    """Without a miss_handler the interpreter is unchanged (no backends)."""
    ctx = _ctx()
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, out, err)  # no miss_handler
    code = asyncio.run(interp.execute("frobnicate"))
    assert code == 127 and "command not found" in err.getvalue()


# --- ollama client shape (no network) ------------------------------------

def test_ollama_client_defaults():
    c = OllamaClient()
    assert c.model == "qwen2.5:7b"
    assert c.base_url == "http://localhost:11434"
    assert c.temperature == 0.1 and c.top_p == 0.95


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
