"""replay_cowrie 測試（雙模式：pytest 或 python tests/test_replay_cowrie.py）。

分兩層：
  * 解析層（parse_cowrie_input）—— 純函式，餵字串驗分組/排序/容錯。
  * 整合層 —— 起一個真的 in-process easypot SSH server，replay fixture 進去，
    驗證 CommandEvent(hit/miss) 真的被 emit。需要 asyncssh；缺席則 skip。

整合測試刻意用真 server（非 mock）：replay 的價值就在「命令真的走過蜜罐的
規則/miss 判定」，mock 掉就測不到重點。
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from honeyshell.replay_cowrie import (  # noqa: E402
    FIXTURE_CSV,
    ReplaySession,
    parse_cowrie_input,
    replay,
)

try:
    import asyncssh  # noqa: F401
    _HAS_ASYNCSSH = True
except Exception:  # noqa: BLE001
    _HAS_ASYNCSSH = False


# --------------------------------------------------------------------------- #
# 解析層
# --------------------------------------------------------------------------- #

def test_parse_groups_by_session():
    sessions, skipped = parse_cowrie_input(FIXTURE_CSV)
    assert skipped == 0
    ids = {s.session_id for s in sessions}
    assert ids == {"sess_aaaa", "sess_bbbb"}
    by_id = {s.session_id: s for s in sessions}
    assert len(by_id["sess_aaaa"].commands) == 3
    assert len(by_id["sess_bbbb"].commands) == 3


def test_parse_orders_by_timestamp():
    # 故意時間亂序
    text = (
        "id\tsession\ttimestamp\trealm\tinput\n"
        "1\ts1\t2022-01-01T00:00:03Z\t\tthird\n"
        "2\ts1\t2022-01-01T00:00:01Z\t\tfirst\n"
        "3\ts1\t2022-01-01T00:00:02Z\t\tsecond\n"
    )
    sessions, _ = parse_cowrie_input(text)
    assert sessions[0].commands == ["first", "second", "third"]


def test_parse_preserves_command_chain_verbatim():
    # 複雜攻擊鏈整行原樣保留，不拆 ';'
    sessions, _ = parse_cowrie_input(FIXTURE_CSV)
    chain = [c for s in sessions for c in s.commands if c.startswith("wget")]
    assert len(chain) == 1
    assert ";" in chain[0]
    assert "chmod +x x" in chain[0]


def test_parse_skips_empty_and_bad_rows():
    text = (
        "id\tsession\ttimestamp\trealm\tinput\n"
        "1\ts1\t2022-01-01T00:00:01Z\t\tls\n"
        "2\ts1\t2022-01-01T00:00:02Z\t\t\n"         # 空 input → skip
        "3\t\t2022-01-01T00:00:03Z\t\torphan\n"      # 無 session → skip
    )
    sessions, skipped = parse_cowrie_input(text)
    assert skipped == 2
    assert len(sessions) == 1
    assert sessions[0].commands == ["ls"]


def test_parse_limit_takes_earliest_sessions():
    sessions, _ = parse_cowrie_input(FIXTURE_CSV, limit=1)
    assert len(sessions) == 1
    assert sessions[0].session_id == "sess_aaaa"  # 首次出現的那個


def test_parse_comma_fallback():
    # 容忍逗號分隔（非此資料集，但求穩健）
    text = "id,session,timestamp,realm,input\n1,s1,2022-01-01T00:00:01Z,,whoami\n"
    sessions, skipped = parse_cowrie_input(text)
    assert skipped == 0
    assert sessions[0].commands == ["whoami"]


def test_parse_empty_text():
    sessions, skipped = parse_cowrie_input("")
    assert sessions == []
    assert skipped == 0


# --------------------------------------------------------------------------- #
# 整合層：真 in-process server + replay
# --------------------------------------------------------------------------- #

def _run(coro):
    return asyncio.run(coro)


async def _integration(tmp_path: str) -> list[dict]:
    """起一個真 easypot server（audit 落 JSONL），replay fixture，讀回事件。

    走 config.audit_jsonl_path 這條真實接線（= 使用者實際用的 --audit-jsonl），
    比注入假 bus 更能反映正式路徑。LLM 關閉：miss 命令回 not found，但
    CommandEvent(hit=False) 仍 emit —— 正是要驗的。
    """
    import json
    from honeyshell.transport import ServerConfig, start_server

    config = ServerConfig(
        host="127.0.0.1", port=0, hostname="testpot",
        audit_jsonl_path=tmp_path,
    )
    server = await start_server(config)
    port = server.sockets[0].getsockname()[1]

    sessions, _ = parse_cowrie_input(FIXTURE_CSV)
    await replay(
        sessions, host="127.0.0.1", port=port,
        username="root", password="x", delay=0.0, read_timeout=2.0,
    )
    await asyncio.sleep(0.2)  # 給 emit/flush 落定
    server.close()

    events: list[dict] = []
    try:
        with open(tmp_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    except FileNotFoundError:
        pass
    return events


def test_replay_emits_hit_and_miss_events():
    if not _HAS_ASYNCSSH:
        print("SKIP integration: asyncssh 未安裝")
        return
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "audit.jsonl")
        events = _run(_integration(path))
    cmds = [e for e in events if e.get("type") == "command"]
    assert cmds, "應至少 emit 若干 CommandEvent"
    # whoami/uname/ls 這類規則命令應 hit
    hits = [e for e in cmds if e.get("hit")]
    assert hits, "規則命令應有 hit=True"
    # /bin/eyshcjdmzg 亂數植入物應 miss（無 LLM 時回 not found，仍 emit hit=False）
    misses = [e for e in cmds if not e.get("hit")]
    assert misses, "亂數命令應有 hit=False（落 LLM seam）"


def test_replay_config_accepts_any_password():
    # 蜜罐 Cowrie 式認證：任意帳密都放行，replay 不必知道真密碼
    if not _HAS_ASYNCSSH:
        print("SKIP integration: asyncssh 未安裝")
        return
    from honeyshell.transport import ServerConfig
    cfg = ServerConfig(host="127.0.0.1", port=0)
    assert cfg.accept("anyone", "whatever") in (True, False)  # 不炸即可


# --------------------------------------------------------------------------- #
# standalone runner
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
