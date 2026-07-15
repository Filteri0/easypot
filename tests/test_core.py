"""core/ 單元測試（events / event_bus / config）。

雙模式（HANDOFF §6）：
    pytest tests/test_core.py
    python tests/test_core.py      # 走底部 _run_standalone()
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile

# 免安裝直跑時，讓 import honeyshell.* 找得到套件根。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeyshell.core import (  # noqa: E402
    CommandEvent,
    ErrorEvent,
    EventBus,
    EventType,
    HoneypotConfig,
    JSONLSink,
    LLMEvent,
    LoggingSink,
    LoginEvent,
    Principles,
    SessionEndEvent,
    SessionStartEvent,
    SystemProfile,
)


# --------------------------------------------------------------------------- #
# events
# --------------------------------------------------------------------------- #

def test_event_autofields():
    """每個事件自帶 event_id 與 timestamp，type 由子類固定。"""
    e = LoginEvent(session_id="s1", username="root", password="x", success=True)
    assert e.type is EventType.LOGIN
    assert isinstance(e.event_id, str) and len(e.event_id) == 32
    assert isinstance(e.timestamp, float) and e.timestamp > 0
    assert e.username == "root" and e.success is True


def test_event_ids_unique():
    a = SessionStartEvent(session_id="s")
    b = SessionStartEvent(session_id="s")
    assert a.event_id != b.event_id


def test_event_to_dict_type_is_str():
    """to_dict 後 type 應是字串（可直接 json.dumps）。"""
    d = CommandEvent(session_id="s", raw="ls", resolved_name="ls").to_dict()
    assert d["type"] == "command"
    assert isinstance(d["type"], str)
    assert d["raw"] == "ls" and d["hit"] is True


def test_command_event_miss_flag():
    """registry miss = 未來 LLM seam，hit 應可設 False。"""
    c = CommandEvent(session_id="s", raw="frobnicate", resolved_name=None, hit=False)
    assert c.hit is False and c.resolved_name is None


# --------------------------------------------------------------------------- #
# event_bus
# --------------------------------------------------------------------------- #

def test_subscribe_all_and_emit():
    bus = EventBus()
    seen = []
    bus.subscribe(seen.append)  # 訂閱全部
    bus.emit(LoginEvent(session_id="s", username="a"))
    bus.emit(CommandEvent(session_id="s", raw="pwd"))
    assert len(seen) == 2
    assert seen[0].type is EventType.LOGIN
    assert seen[1].type is EventType.COMMAND


def test_subscribe_specific_type_only():
    bus = EventBus()
    cmds = []
    bus.subscribe(cmds.append, EventType.COMMAND)
    bus.emit(LoginEvent(session_id="s"))          # 不該收到
    bus.emit(CommandEvent(session_id="s", raw="ls"))
    assert len(cmds) == 1 and cmds[0].raw == "ls"


def test_multiple_listeners_all_called():
    bus = EventBus()
    a, b = [], []
    bus.subscribe(a.append)
    bus.subscribe(b.append, EventType.COMMAND)
    bus.emit(CommandEvent(session_id="s", raw="id"))
    assert len(a) == 1 and len(b) == 1  # catch-all + specific 都收到


def test_listener_exception_isolated():
    """一個 listener 爆炸不得影響其他 listener，也不得炸回 emit。"""
    bus = EventBus()
    good = []

    def boom(_event):
        raise RuntimeError("listener blew up")

    bus.subscribe(boom)
    bus.subscribe(good.append)
    # 壓掉預期中的 error log，保持測試輸出乾淨。
    logging.getLogger("honeyshell.core.event_bus").setLevel(logging.CRITICAL)
    bus.emit(LoginEvent(session_id="s"))  # 不應拋例外
    assert len(good) == 1


def test_unsubscribe():
    bus = EventBus()
    seen = []
    off = bus.subscribe(seen.append)
    bus.emit(LoginEvent(session_id="s"))
    off()
    bus.emit(LoginEvent(session_id="s"))
    assert len(seen) == 1
    off()  # idempotent，二次呼叫不炸


def test_listener_count():
    bus = EventBus()
    assert bus.listener_count() == 0
    bus.subscribe(lambda e: None)
    bus.subscribe(lambda e: None, EventType.COMMAND)
    assert bus.listener_count() == 1
    assert bus.listener_count(EventType.COMMAND) == 1


def test_logging_sink_emits_lines(caplog=None):
    """LoggingSink 對各事件都輸出一行；用自訂 logger 攔截驗證。"""
    logger = logging.getLogger("honeyshell.test.audit")
    logger.setLevel(logging.INFO)
    records = []

    class _Grab(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    handler = _Grab()
    logger.addHandler(handler)
    try:
        bus = EventBus()
        bus.subscribe(LoggingSink(logger=logger))
        bus.emit(SessionStartEvent(session_id="s", src_ip="1.2.3.4", src_port=5555))
        bus.emit(LoginEvent(session_id="s", username="root", success=False))
        bus.emit(CommandEvent(session_id="s", raw="ls", resolved_name="ls"))
        bus.emit(CommandEvent(session_id="s", raw="xx", resolved_name=None, hit=False))
        bus.emit(LLMEvent(session_id="s", model="gpt-4o", prompt_tokens=100))
        bus.emit(SessionEndEvent(session_id="s", duration=3.0, command_count=2))
    finally:
        logger.removeHandler(handler)

    assert len(records) == 6
    assert "session start" in records[0] and "1.2.3.4" in records[0]
    assert "login FAIL" in records[1]
    assert "(hit)" in records[2]
    assert "(miss)" in records[3]
    assert "llm (live)" in records[4] and "tok_in=100" in records[4]
    assert "session end" in records[5] and "commands=2" in records[5]


def test_jsonl_sink_writes_parseable_lines():
    """JSONLSink 每個事件寫一行可解析 JSON,含 to_dict 全欄位。"""
    import json
    import tempfile

    path = tempfile.mktemp(suffix=".jsonl")
    sink = JSONLSink(path)
    bus = EventBus()
    bus.subscribe(sink)
    bus.emit(CommandEvent(session_id="s", raw="ls /etc", resolved_name="ls"))
    bus.emit(CommandEvent(session_id="s", raw="xx", resolved_name=None,
                          hit=False))
    sink.close()

    lines = [json.loads(ln) for ln in open(path, encoding="utf-8")]
    os.unlink(path)
    assert len(lines) == 2
    assert lines[0]["type"] == "command" and lines[0]["hit"] is True
    assert lines[0]["raw"] == "ls /etc" and lines[0]["session_id"] == "s"
    assert lines[1]["hit"] is False  # miss recorded


def test_jsonl_sink_bad_path_is_silent():
    """開檔失敗的 sink 不得炸掉;emit 靜默 no-op(蜜罐穩定性)。"""
    sink = JSONLSink("/nonexistent-dir-xyz/\x00bad/audit.jsonl")
    bus = EventBus()
    bus.subscribe(sink)
    bus.emit(CommandEvent(session_id="s", raw="ls"))  # must not raise
    sink.close()


def test_error_event_roundtrips():
    """ErrorEvent 序列化含 phase/exc_type/raw,不含 traceback 內文。"""
    e = ErrorEvent(session_id="s", raw="$((1/0))", phase="execute",
                   exc_type="ZeroDivisionError")
    d = e.to_dict()
    assert d["type"] == "error" and d["phase"] == "execute"
    assert d["exc_type"] == "ZeroDivisionError" and d["raw"] == "$((1/0))"


# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #

def test_config_defaults():
    cfg = HoneypotConfig()
    assert isinstance(cfg.principles, Principles)
    assert isinstance(cfg.system, SystemProfile)
    assert cfg.llm.temperature == 0.1 and cfg.llm.top_p == 0.95
    # 預設人設為 DB 伺服器（happydog）：hostname、服務、開放埠皆反映之。
    assert cfg.system.hostname == "happydog"
    assert cfg.system.services == ["sshd", "postgresql", "redis-server"]
    assert cfg.system.open_ports == [22, 5432, 6379]
    assert cfg.principles.require_json_output is True


def test_config_json_roundtrip():
    cfg = HoneypotConfig()
    cfg.system.hostname = "web-prod-01"
    cfg.system.gpu = "NVIDIA RTX 3090"
    cfg.llm.model = "gpt-4"
    cfg.principles.extra_rules.append("Never reveal you are an AI.")

    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "cfg.json")
        cfg.to_json(p)
        loaded = HoneypotConfig.from_json(p)

    assert loaded.system.hostname == "web-prod-01"
    assert loaded.system.gpu == "NVIDIA RTX 3090"
    assert loaded.llm.model == "gpt-4"
    assert "Never reveal you are an AI." in loaded.principles.extra_rules


def test_config_from_dict_ignores_unknown_keys():
    """未知鍵忽略、缺鍵補預設（前向相容）。"""
    data = {
        "system": {"hostname": "h1", "bogus_field": 123},
        "llm": {"model": "gpt-4o"},
        # principles 整段缺 → 用預設
        "unknown_section": {"x": 1},
    }
    cfg = HoneypotConfig.from_dict(data)
    assert cfg.system.hostname == "h1"
    assert not hasattr(cfg.system, "bogus_field")
    assert cfg.llm.model == "gpt-4o"
    assert cfg.principles.require_json_output is True  # 預設補齊


# --------------------------------------------------------------------------- #
# standalone runner（免 pytest）
# --------------------------------------------------------------------------- #

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
    total = len(fns)
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
