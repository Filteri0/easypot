"""capture_cowrie.py —— 把擬真度題庫的 30 題餵進 **Cowrie**，收集輸出，
產生與 capture_ground_truth.sh 相同格式的檔案，供 run_probes.py --cowrie 對照。

為什麼需要這支
--------------
報告核心賣點是 easypot vs Cowrie 的**擬真度**對照（目標一）。real 與 easypot 兩欄
已有採集途徑（capture_ground_truth.sh / run_probes 直接呼叫 resolver），但 Cowrie
欄一直是空的。這支補上最後一欄，讓三方（real / easypot / cowrie）都用**同一份題目**
與**同一個判定器**（fidelity_judge）評分，對照才成立。

注意：與 Cowrie 比的是**擬真度**（SALC/FALC），不是 hit/miss。hit/miss 是 easypot
內部「規則接住 vs 掉到 LLM」的架構指標，Cowrie 無 LLM 補盲層，比不對等。擬真度這把
尺同時涵蓋「Cowrie 支不支援這命令」（不支援 → command not found → 判定器抓露餡）與
「支援時輸出像不像真機」（罐頭輸出可能結構對但細節露餡 = SALNLC）。

題目來源
--------
直接讀 probes.py 的 PROBES（單一真實來源），不另抄一份命令清單，避免與題庫漂移。

輸出格式
--------
與 capture_ground_truth.sh 一致（===Q<id>=== / "$ cmd" / 輸出 / ===EXIT:<n>===），
故可直接被 run_probes.parse_ground_truth 解析。Cowrie 的 shell 對 `$?` 支援有限，
取不到 exit code 時**省略 EXIT 行**（判定器對 exit_code=None 有 heuristic 兜底，
不影響 not-found / 結構類判定）。

用法
----
    pip install asyncssh
    python -m tools.capture_cowrie --host localhost --port 22222 \
        --user rootroot --password <你的密碼> --out cowrie_out.txt

    # 再併入對照表（三欄齊全）
    python -m tools.run_probes --ground-truth tools/ground_truth.txt \
        --cowrie cowrie_out.txt --repeat 10 \
        --out fidelity_table.md --detail-out fidelity_detail.md

Cowrie 跑在別台（例如 Windows Docker）時，--host 給那台的 IP；若本機跑不動
asyncssh，也可把這支複製到那台跑，再把產出的檔案傳回來。
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.probes import PROBES  # noqa: E402

# 終端控制碼（Cowrie 會送顏色/游標序列，判定前要洗掉，否則污染結構比對）
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[()][B0]")


def _clean(text: str) -> str:
    """去除 ANSI 控制碼與 \\r，讓輸出貼近 capture_ground_truth.sh 的純文字。"""
    text = _ANSI_RE.sub("", text)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _extract(raw: str, command: str, sentinel: str) -> str:
    """從 PTY 逐字流中抽出某題的乾淨輸出。

    流長這樣（PTY 會回顯你打的字）：
        <prompt>$ uname -a          <- 命令回顯
        Linux svr04 ...             <- 真正輸出
        <prompt>$ echo ___EPn___    <- sentinel 命令的回顯
        ___EPn___                   <- sentinel 輸出（結束標記）
    取「命令回顯之後」到「最後一個 sentinel 之前」，再剝掉 sentinel 命令的回顯行
    與尾端 prompt。用**最後一個** sentinel 當結束點，可避免回顯造成的重複匹配。
    """
    text = _clean(raw)

    # 1) 結束點：最後一次出現的 sentinel（前面那次多半是命令回顯）
    idx = text.rfind(sentinel)
    if idx != -1:
        text = text[:idx]

    lines = text.split("\n")

    # 2) 起點：找到回顯命令的那一行，取其後。命令可能被 prompt 前綴，故用包含判斷。
    #    找不到就整段保留（PTY 回顯關閉的情況）。
    start = 0
    for i, ln in enumerate(lines):
        if command in ln:
            start = i + 1
            break
    lines = lines[start:]

    # 3) 剝掉 sentinel 命令的回顯行，以及尾端殘留的 prompt 行
    out: list[str] = []
    for ln in lines:
        if sentinel in ln or f"echo {sentinel}" in ln:
            continue
        out.append(ln)
    while out and _is_prompt_or_blank(out[-1]):
        out.pop()

    return "\n".join(out).strip("\n")


def _is_prompt_or_blank(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    # 典型 shell prompt 尾巴：user@host:~$ / # / $
    return bool(re.search(r"[\$#]\s*$", s) and "@" in s) or s in ("$", "#")


async def capture(host: str, port: int, user: str, password: str,
                  read_timeout: float, verbose: bool) -> dict[int, tuple[str, str, int | None]]:
    """連上 Cowrie，逐題送命令，回傳 {id: (command, output, exit_code)}。"""
    import asyncssh  # lazy import：與 transport / replay_cowrie 一致

    results: dict[int, tuple[str, str, int | None]] = {}

    async with asyncssh.connect(
        host, port=port, username=user, password=password,
        known_hosts=None,       # 蜜罐 host key 不驗
        client_keys=None,
    ) as conn:
        # 請求 PTY 走互動式 shell —— 與真實攻擊者操作一致，也是 Cowrie 的主要路徑
        proc = await conn.create_process(term_type="xterm")

        # 吃掉登入 banner / 第一個 prompt
        await _read_idle(proc, 1.5)

        for probe in PROBES:
            sentinel = f"___EP{probe.id}___"
            if verbose:
                print(f"[Q{probe.id}] {probe.command}", file=sys.stderr)

            proc.stdin.write(probe.command + "\n")
            # 緊接著送 sentinel（附帶 $? 以嘗試取 exit code；Cowrie 不展開就會是字面值）
            proc.stdin.write(f"echo {sentinel}:$?\n")

            # Q10 之類含 sleep 的題需要更久
            budget = read_timeout + (4.0 if "sleep" in probe.command else 0.0)
            raw = await _read_until(proc, sentinel, budget)

            output = _extract(raw, probe.command, sentinel)
            exit_code = _parse_exit(raw, sentinel)
            results[probe.id] = (probe.command, output, exit_code)

        proc.stdin.write("exit\n")
        await _read_idle(proc, 0.5)

    return results


def _parse_exit(raw: str, sentinel: str) -> int | None:
    """從 sentinel 尾巴取 exit code；Cowrie 沒展開 $? 時回 None。"""
    m = re.findall(rf"{re.escape(sentinel)}:(\d+)", _clean(raw))
    return int(m[-1]) if m else None


async def _read_until(proc, sentinel: str, timeout: float) -> str:
    """讀到 sentinel 出現（第 2 次，避開命令回顯）或逾時。"""
    buf = ""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        try:
            chunk = await asyncio.wait_for(proc.stdout.read(1024), timeout=0.3)
        except asyncio.TimeoutError:
            # 已看到 sentinel 且資料停了 → 該題結束
            if _clean(buf).count(sentinel) >= 2:
                break
            continue
        if not chunk:
            break
        buf += chunk
        if _clean(buf).count(sentinel) >= 2:
            # 再多等一點點，確保 sentinel 那行完整收到
            try:
                buf += await asyncio.wait_for(proc.stdout.read(256), timeout=0.3)
            except asyncio.TimeoutError:
                pass
            break
    return buf


async def _read_idle(proc, idle: float) -> str:
    """讀到沒有新資料為止（用來吃 banner）。"""
    buf = ""
    while True:
        try:
            chunk = await asyncio.wait_for(proc.stdout.read(1024), timeout=idle)
        except asyncio.TimeoutError:
            return buf
        if not chunk:
            return buf
        buf += chunk


def render(results: dict[int, tuple[str, str, int | None]], host: str, port: int) -> str:
    """輸出成 capture_ground_truth.sh 的格式，供 parse_ground_truth 解析。"""
    lines = [
        f"### cowrie probe capture from {host}:{port}",
        f"### probes: {len(results)} (source: tools/probes.py)",
        "",
    ]
    for pid in sorted(results):
        command, output, exit_code = results[pid]
        lines.append(f"===Q{pid}===")
        lines.append(f"$ {command}")
        if output:
            lines.append(output)
        if exit_code is not None:
            lines.append(f"===EXIT:{exit_code}===")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="把題庫 30 題餵進 Cowrie 收集輸出")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=22222,
                    help="Cowrie SSH port（docker -p 22222:2222 → 22222）")
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default="x",
                    help="Cowrie userdb 接受的密碼（預設 userdb 多半任意密碼皆可）")
    ap.add_argument("--out", default="cowrie_out.txt")
    ap.add_argument("--read-timeout", type=float, default=6.0,
                    help="每題最長等待秒數（含 sleep 的題會自動加時）")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    try:
        results = asyncio.run(capture(
            args.host, args.port, args.user, args.password,
            args.read_timeout, args.verbose,
        ))
    except Exception as e:  # noqa: BLE001
        print(f"採集失敗：{type(e).__name__}: {e}", file=sys.stderr)
        print("檢查：Cowrie 是否在跑、port/帳密是否正確、防火牆是否放行。",
              file=sys.stderr)
        return 1

    Path(args.out).write_text(render(results, args.host, args.port),
                              encoding="utf-8")

    empty = [pid for pid, (_, o, _) in results.items() if not o.strip()]
    print(f"已寫入 {args.out}（{len(results)} 題）")
    if empty:
        print(f"⚠ 這些題收到空輸出，請人工確認：{empty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
