"""analyzer 單元測試（雙模式：pytest 或 python tests/test_analyze.py）。

覆蓋：載入容錯、LLM 效率比例、session 串接、情報聚合、輸出格式不炸。
測試以純函式（load_events / analyze）為主，不碰檔案 I/O，符合專案慣例。
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from honeyshell.analyze import (  # noqa: E402
    analyze,
    load_events,
    render_console,
    render_markdown,
)


def _line(**kw) -> str:
    return json.dumps(kw, ensure_ascii=False)


def _sample_lines() -> list[str]:
    """一段合成流量：2 個 session、規則命中 + LLM miss + 憑證 + 錯誤。"""
    return [
        _line(type="command", session_id="s1", timestamp=100.0,
              raw="whoami", resolved_name="whoami", hit=True, _source="hp-a"),
        _line(type="command", session_id="s1", timestamp=101.0,
              raw="ls -la", resolved_name="ls", hit=True, _source="hp-a"),
        _line(type="command", session_id="s1", timestamp=102.0,
              raw="weirdtool --x", resolved_name=None, hit=False,
              _source="hp-a"),
        _line(type="login", session_id="s1", timestamp=103.0,
              username="root", password="hunter2", success=True,
              _source="hp-a"),
        _line(type="command", session_id="s2", timestamp=200.0,
              raw="uname -a", resolved_name="uname", hit=True, _source="hp-b"),
        _line(type="command", session_id="s2", timestamp=201.0,
              raw="weirdtool --y", resolved_name=None, hit=False,
              _source="hp-b"),
        _line(type="error", session_id="s2", timestamp=202.0,
              raw="echo $((1/0))", phase="execute",
              exc_type="ZeroDivisionError", _source="hp-b"),
    ]


# --------------------------------------------------------------------------- #
# 載入容錯
# --------------------------------------------------------------------------- #

def test_load_skips_bad_lines():
    lines = [
        _line(type="command", session_id="s1", raw="ls", hit=True),
        "not json at all {{{",                       # 壞 JSON
        json.dumps([1, 2, 3]),                        # 非 dict
        json.dumps({"_source": "hp-a", "_raw": "garbage"}),  # collector 壞行包裝
        json.dumps({"_source": "hp-a", "_value": 42}),       # 非 dict 包裝
        "   ",                                        # 空白行
    ]
    events, skipped = load_events(lines)
    assert len(events) == 1
    assert skipped == 4  # 壞JSON + 非dict + _raw + _value（空白行不計）


# --------------------------------------------------------------------------- #
# 目標二：LLM 效率
# --------------------------------------------------------------------------- #

def test_llm_efficiency_ratio():
    events, skipped = load_events(_sample_lines())
    r = analyze(events, skipped=skipped)
    # 5 個 command（whoami/ls/weirdtool @s1 + uname/weirdtool @s2），3 hit / 2 miss
    assert r.llm.total_commands == 5
    assert r.llm.rule_hits == 3
    assert r.llm.llm_misses == 2
    assert abs(r.llm.hit_rate - 0.6) < 1e-9
    assert abs(r.llm.miss_rate - 0.4) < 1e-9


def test_llm_top_misses():
    events, _ = load_events(_sample_lines())
    r = analyze(events)
    # weirdtool 走了兩次 LLM
    misses = dict(r.llm.top_misses)
    assert misses.get("weirdtool") == 2


def test_empty_input_no_crash():
    r = analyze([], skipped=0)
    assert r.llm.total_commands == 0
    assert r.llm.hit_rate == 0.0
    assert r.llm.miss_rate == 0.0
    assert r.sessions.total_sessions == 0
    # 輸出不因空資料炸掉
    assert isinstance(render_console(r), str)
    assert isinstance(render_markdown(r), str)


# --------------------------------------------------------------------------- #
# 目標三：Session
# --------------------------------------------------------------------------- #

def test_sessions_grouped_and_ordered():
    events, _ = load_events(_sample_lines())
    r = analyze(events)
    assert r.sessions.total_sessions == 2
    busiest = r.sessions.busiest
    assert busiest is not None
    # s1 有 3 個 command，s2 有 2 個 → s1 最活躍
    assert busiest.session_id == "s1"
    assert busiest.command_count == 3
    assert busiest.credentials == 1
    # duration = last - first = 103 - 100 = 3
    assert abs(busiest.duration - 3.0) < 1e-9


def test_session_command_order_by_timestamp():
    # 故意亂序餵入，聚合後 commands 應按 timestamp 排好
    lines = [
        _line(type="command", session_id="s1", timestamp=3.0, raw="third",
              hit=True),
        _line(type="command", session_id="s1", timestamp=1.0, raw="first",
              hit=True),
        _line(type="command", session_id="s1", timestamp=2.0, raw="second",
              hit=True),
    ]
    events, _ = load_events(lines)
    r = analyze(events)
    rec = r.sessions.sessions[0]
    assert rec.commands == ["first", "second", "third"]


# --------------------------------------------------------------------------- #
# 目標三：情報
# --------------------------------------------------------------------------- #

def test_intel_credentials_and_sources():
    events, _ = load_events(_sample_lines())
    r = analyze(events)
    # 憑證
    assert ("root", "hunter2", "hp-a") in r.intel.credentials
    # per-source 命令量：hp-a 3 個 command、hp-b 2 個
    assert r.intel.per_source_commands["hp-a"] == 3
    assert r.intel.per_source_commands["hp-b"] == 2
    # per-source miss：兩台各 1
    assert r.intel.per_source_misses["hp-a"] == 1
    assert r.intel.per_source_misses["hp-b"] == 1
    # 錯誤型別
    assert ("ZeroDivisionError", 1) in r.intel.error_types


def test_top_commands_tokenized():
    events, _ = load_events(_sample_lines())
    r = analyze(events)
    top = dict(r.intel.top_commands)
    # raw "ls -la" → token "ls"; "weirdtool --x/--y" → "weirdtool" ×2
    assert top.get("weirdtool") == 2
    assert top.get("whoami") == 1
    assert top.get("ls") == 1


# --------------------------------------------------------------------------- #
# 輸出格式
# --------------------------------------------------------------------------- #

def test_report_to_dict_serializable():
    events, skipped = load_events(_sample_lines())
    r = analyze(events, skipped=skipped)
    d = r.to_dict()
    # 可 json 序列化（不含非序列化物件）
    s = json.dumps(d, ensure_ascii=False)
    assert "llm_efficiency" in s
    assert d["llm_efficiency"]["miss_rate"] == 0.4
    assert d["totals"]["sessions"] == 2


def test_renderers_contain_key_numbers():
    events, _ = load_events(_sample_lines())
    r = analyze(events)
    con = render_console(r)
    assert "60.00%" in con        # hit rate
    assert "40.00%" in con        # miss rate
    assert "hunter2" in con        # 憑證出現
    md = render_markdown(r)
    assert "60.00%" in md
    assert "40.00%" in md


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
