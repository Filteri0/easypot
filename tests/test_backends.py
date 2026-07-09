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
    assert parse_result({"output": "root", "state_change": "none",
                         "impact": "3"}) == ("root", "", 3)
    # out-of-range impact clamps; missing keys default
    assert parse_result({"impact": 99}) == ("", "", 4)
    assert parse_result(None) == ("", "", 0)


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
    llm = FakeLLM('{"output": "Linux svr04 5.10", "state_change": "none", '
                  '"impact": 0}')
    r = ChainResolver(client=llm, config=_cfg())
    code, out, err, ctx = _run_line("uname -a", r)
    assert code == 0
    assert out == "Linux svr04 5.10\n"
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


def test_llm_command_records_state_log():
    llm = FakeLLM('{"output": "", "state_change": "created /tmp/x", '
                  '"impact": 1}')
    r = ChainResolver(client=llm, config=_cfg())
    _, _, _, ctx = _run_line("mkdir /tmp/x", r)
    log = getattr(ctx, "llm_state_log", [])
    assert len(log) == 1 and log[0]["state_change"] == "created /tmp/x"
    assert log[0]["impact"] == 1


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
