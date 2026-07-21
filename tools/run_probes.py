"""擬真度探測 runner —— 對 10 題探測命令，收集三方輸出、判定、出對照表。

這是目標一（擬真度 SALC/FALC 對照）的執行入口。三個「受測對象」：

  * easypot   —— 直接呼叫 ChainResolver.resolve() 拿 LLM 補盲的輸出（需 Ollama）。
  * cowrie    —— 可選：若給了 Cowrie 的輸出檔則納入對照（見 --cowrie）。
  * real      —— 真機基準（ground_truth.txt，由 capture_ground_truth.sh 採集）。

判定看結構/OS 邏輯（見 fidelity_judge），非數值相等，故 real 一欄理應全通過，
easypot 一欄的通過率就是「擬真度」量化結果，可與 Cowrie 對照成報告的核心表。

用法（在實機、Ollama 已跑）：
    # 只測 easypot vs real
    python -m tools.run_probes --ground-truth ground_truth.txt

    # 指定模型 / Ollama 位址
    python -m tools.run_probes --ground-truth ground_truth.txt \\
        --model qwen2.5:14b --base-url http://localhost:11434

    # 純驗證判定流程、不連 LLM（容器內可跑）：easypot 一欄用 real 輸出灌入
    python -m tools.run_probes --ground-truth ground_truth.txt --dry-run

設計刻意點
----------
  * easypot 一欄**直接呼叫 resolver**，不經 SSH/audit——題庫是離線探測工具，
    比走完整連線更快更可控（HANDOFF §32 原設想「先讓 audit 記輸出」其實不需要）。
  * 對 pipe 型題（Q2/Q3/Q7/Q9），resolver 是逐命令的，故對這些題我們送**整條
    命令字串**給 LLM（模型能理解 pipe 語意），與真機的整條輸出對照。這對「擬真度」
    是合理的：攻擊者看到的就是整條命令的最終輸出。
  * 不對 easypot 做重試/挑選：一次輸出定生死，避免灌水（與報告誠實原則一致）。
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.probes import PROBES, Probe  # noqa: E402
from tools.fidelity_judge import classify, Judgement  # noqa: E402


# --- 解析 ground_truth.txt -------------------------------------------------


@dataclass
class RealAnswer:
    command: str
    output: str
    exit_code: int | None


def parse_ground_truth(text: str) -> dict[int, RealAnswer]:
    """解析 capture_ground_truth.sh 的輸出格式（===Q<id>=== 分段）。"""
    answers: dict[int, RealAnswer] = {}
    blocks = re.split(r"^===Q(\d+)===$", text, flags=re.MULTILINE)
    # blocks: [前言, id1, body1, id2, body2, ...]
    for i in range(1, len(blocks) - 1, 2):
        pid = int(blocks[i])
        body = blocks[i + 1]
        # 第一行是 "$ <command>"，中間是輸出，尾端 "===EXIT:<n>==="
        cmd_m = re.search(r"^\$ (.+)$", body, flags=re.MULTILINE)
        exit_m = re.search(r"^===EXIT:(\d+)===$", body, flags=re.MULTILINE)
        command = cmd_m.group(1) if cmd_m else ""
        exit_code = int(exit_m.group(1)) if exit_m else None
        # 輸出 = 去掉 "$ cmd" 行與 "===EXIT===" 行之間的內容
        out = body
        if cmd_m:
            out = out.split(cmd_m.group(0), 1)[1]
        if exit_m:
            out = out.split(exit_m.group(0), 1)[0]
        answers[pid] = RealAnswer(command.strip(), out.strip("\n"), exit_code)
    return answers


# --- 取得 easypot 對每題的輸出 --------------------------------------------


async def easypot_output(resolver, probe: Probe) -> tuple[str, int | None]:
    """呼叫 resolver 拿 easypot 對該命令的輸出。回 (output, exit_code)。

    resolver 回的是 Resolution(output, state_change, impact, ...)；exit_code
    不在 (A,C,F) 三元組內（見 llm_command.py），故 easypot 一律回 None，讓
    判定器改以「輸出結構 + not-found 樣式」推斷成功與否。

    per_command 題（如 Q10 的 date;sleep;date）：拆分號逐段**各自獨立**呼叫
    resolver，模擬真實蜜罐的逐命令、無跨命令狀態處理。sleep 段不送 LLM（它本身
    無輸出），其餘段各自 resolve，輸出依序串接。這才能真實暴露 easypot 有沒有
    跨命令狀態——而非讓 LLM 一次看到整條、照著 sleep 2 生出假一致的結果。
    """
    if probe.per_command:
        parts = [p.strip() for p in probe.command.split(";") if p.strip()]
        outputs: list[str] = []
        for part in parts:
            argv = part.split()
            if argv and argv[0] == "sleep":
                continue  # sleep 無 stdout，且不佔 LLM；跳過但保留其語意分隔
            resolution = await resolver.resolve(argv, cwd="/root")
            if resolution is None:
                return "", None
            if resolution.output:
                outputs.append(resolution.output)
        return "\n".join(outputs), None

    resolution = await resolver.resolve(probe.command.split(), cwd="/root")
    if resolution is None:
        return "", None  # LLM 不可用
    return resolution.output, None


def build_resolver(model: str, base_url: str):
    """照 ssh_server 的組裝方式建一個 ChainResolver（需 Ollama）。"""
    from honeyshell.backends import ChainResolver, OllamaClient
    from honeyshell.core.config import HoneypotConfig

    hp = HoneypotConfig()
    hp.llm.model = model
    client = OllamaClient(model=model, base_url=base_url)
    return ChainResolver(client=client, config=hp)


# --- 報表 ------------------------------------------------------------------


def render_table(rows: list[dict]) -> str:
    """產出對照表（Markdown），含每題各系統的類別與是否通過，及總通過率。"""
    lines = [
        "| Q | ATT&CK | 命令 | 預期 | real | easypot | cowrie |",
        "|---|--------|------|------|------|---------|--------|",
    ]
    tallies: dict[str, list[int]] = {"real": [0, 0], "easypot": [0, 0],
                                     "cowrie": [0, 0]}
    for r in rows:
        cells = []
        for sysname in ("real", "easypot", "cowrie"):
            j: Judgement | None = r.get(sysname)
            if j is None:
                cells.append("—")
                continue
            mark = "✅" if j.passed else "❌"
            cells.append(f"{j.predicted_class} {mark}")
            tallies[sysname][0] += int(j.passed)
            tallies[sysname][1] += 1
        exp = "過" if r["probe"].expect_easypot_pass else "預期輸"
        cmd = r["probe"].command
        if len(cmd) > 38:
            cmd = cmd[:37] + "…"
        lines.append(
            f"| {r['probe'].id} | {r['probe'].attack_technique.split(' ')[0]} "
            f"| `{cmd}` | {exp} | {cells[0]} | {cells[1]} | {cells[2]} |"
        )
    lines.append("")
    for sysname, (ok, total) in tallies.items():
        if total:
            pct = 100.0 * ok / total
            lines.append(f"- **{sysname}** 通過 {ok}/{total}（{pct:.0f}%）")
    return "\n".join(lines)


async def hybrid_output(resolver, probe: Probe) -> tuple[str, int | None]:
    """走**攻擊者實際路徑**拿 easypot 輸出：完整 Interpreter（hit→內建、miss→LLM）。

    與 :func:`easypot_output` 的差別（這是報告解讀的關鍵）：

    * ``easypot_output`` 直接呼叫 ``ChainResolver.resolve()``，而 resolve 內部只有
      ``cache → LLM``、**不查 registry**，等於強制 30 題全走 LLM、繞過 61 個內建
      命令。那是「假設全部 miss」的**最壞情況壓力測試**，是 easypot 的**下界**。
    * 本函式建真的 ``Interpreter`` 並把 ``miss_handler`` 接上 LLM factory——與
      ssh_server 的線上組裝方式一致。registry 有的走內建（毫秒級），沒有的才降級
      到 LLM。這才是攻擊者連進來**實際體驗**到的東西。

    兩個數字都要報：下界證明「就算規則全失效也還有多少」，實際路徑才是系統真實
    擬真度。兩者的差距即「內建命令的貢獻」。

    exit_code 照 easypot_output 的理由回 None（讓判定器用輸出結構推斷）。
    """
    from honeyshell.backends import make_llm_command_factory
    from honeyshell.commands import ShellContext, StringWriter
    from honeyshell.fs.build_sample_fs import build as build_sample_fs
    from honeyshell.shell import Interpreter

    ctx = ShellContext(
        fs=build_sample_fs(hostname="svr04"), cwd="/root",
        environ={"HOME": "/root", "USER": "root", "PATH": "/usr/bin:/bin"},
        username="root",
    )
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(
        ctx, out, err,
        miss_handler=make_llm_command_factory(resolver) if resolver else None,
    )
    # 整條命令列交給 interpreter（含 pipeline / 分號），與真實 shell 行為一致：
    # sleep、管線、跨命令狀態都由 interpreter 自己處理，不像 easypot_output 需要
    # 人工拆分號——這正是要量測的「系統整體」行為。
    await interp.execute(probe.command)
    return (out.getvalue() + err.getvalue()), None


async def _easypot_trials(resolver, probe, repeat, verbose, hybrid=False):
    """對一題跑 repeat 次 easypot，回 (通過次數, 各次 Judgement, 各次原始輸出)。

    多次重跑是為了消化 LLM 生成的隨機性：同一題不同次結果會變（實測 Q2 有時
    產出乾淨 cpuinfo、有時把 flags 展開成假欄位）。單次數字不穩，跑 N 次算通過率
    分布才是可寫進報告的擬真度量測。

    注意判定器局限（誠實揭露）：幻覺類檢查（如 Q9 掛載點）是白名單式，只抓已知
    幻覺樣式。若 LLM 生出未列入黑名單的新型幻覺，可能被誤判為通過。故細項輸出
    （--detail-out）保留每次原始輸出，供人工複核高通過率題是否真的乾淨。
    """
    judgements = []
    outputs = []
    latencies = []
    passes = 0
    for i in range(repeat):
        import time as _t
        _start = _t.perf_counter()
        _fn = hybrid_output if hybrid else easypot_output
        out, ec = await _fn(resolver, probe)
        elapsed = _t.perf_counter() - _start
        latencies.append(elapsed)
        j = classify(probe, out, ec, "easypot")
        judgements.append(j)
        outputs.append(out)
        passes += int(j.passed)
        if verbose:
            mark = "✅" if j.passed else "❌"
            print(f"[Q{probe.id} 第{i+1}/{repeat}次 {mark} {j.predicted_class} "
                  f"{elapsed:.1f}s] {j.reason}\n{out}\n{'-'*40}", file=sys.stderr)
    return passes, judgements, outputs, latencies


def write_detail(rows: list[dict], repeat: int, path: str) -> None:
    """把每題每次的判定與原始輸出寫成結構化 Markdown，供人工複核。

    特別用途：複核「高通過率題」是否真乾淨（判定器白名單可能漏抓新型幻覺），
    以及引用具體露餡案例寫進報告（如 Q5 每次的雜訊長相、Q10 每次的時間戳）。
    """
    out_lines = [f"# 擬真度細項（每題 {repeat} 次）\n"]
    for r in rows:
        p = r["probe"]
        ep = r.get("easypot")
        if ep is None:
            continue
        passes, judgements, outputs, latencies = ep
        out_lines.append(f"\n## Q{p.id} {p.command}")
        out_lines.append(f"- ATT&CK：{p.attack_technique}")
        out_lines.append(f"- 考點：{p.checkpoint}")
        out_lines.append(f"- 通過：{passes}/{repeat}\n")
        for i, (j, o) in enumerate(zip(judgements, outputs), 1):
            mark = "✅" if j.passed else "❌"
            out_lines.append(f"### 第 {i} 次 {mark} {j.predicted_class}")
            out_lines.append(f"判定：{j.reason}\n")
            out_lines.append("```")
            out_lines.append(o if o else "(空輸出)")
            out_lines.append("```\n")
    Path(path).write_text("\n".join(out_lines), encoding="utf-8")


def render_table(rows: list[dict], repeat: int) -> str:
    """產出對照表（Markdown）。repeat>1 時 easypot 欄顯示通過率 x/N。"""
    lines = [
        "| Q | ATT&CK | 命令 | 預期 | real | easypot | cowrie |",
        "|---|--------|------|------|------|---------|--------|",
    ]
    tallies: dict[str, list[int]] = {"real": [0, 0], "cowrie": [0, 0]}
    easypot_rate_sum = 0.0
    easypot_n = 0
    all_latencies: list[float] = []
    for r in rows:
        cells = []
        # real / cowrie：單一 Judgement
        for sysname in ("real",):
            j = r.get(sysname)
            if j is None:
                cells.append("—")
            else:
                cells.append(f"{j.predicted_class} {'✅' if j.passed else '❌'}")
                tallies[sysname][0] += int(j.passed)
                tallies[sysname][1] += 1
        # easypot：可能多次
        ep = r.get("easypot")
        if ep is None:
            cells.append("—")
        elif repeat > 1:
            passes, judgements, _, latencies = ep
            rate = 100.0 * passes / repeat
            easypot_rate_sum += rate
            easypot_n += 1
            avg_lat = sum(latencies)/len(latencies) if latencies else 0
            all_latencies.extend(latencies)
            cells.append(f"{passes}/{repeat}（{rate:.0f}%, {avg_lat:.1f}s）")
        else:
            j = ep[1][0]
            lat = ep[3][0] if len(ep) > 3 and ep[3] else 0
            all_latencies.extend(ep[3] if len(ep) > 3 else [])
            cells.append(f"{j.predicted_class} {'✅' if j.passed else '❌'}")
            easypot_rate_sum += 100.0 * int(j.passed)
            easypot_n += 1
        # cowrie
        cj = r.get("cowrie")
        if cj is None:
            cells.append("—")
        else:
            cells.append(f"{cj.predicted_class} {'✅' if cj.passed else '❌'}")
            tallies["cowrie"][0] += int(cj.passed)
            tallies["cowrie"][1] += 1

        exp = "過" if r["probe"].expect_easypot_pass else "預期輸"
        cmd = r["probe"].command
        if len(cmd) > 38:
            cmd = cmd[:37] + "…"
        lines.append(
            f"| {r['probe'].id} | {r['probe'].attack_technique.split(' ')[0]} "
            f"| `{cmd}` | {exp} | {cells[0]} | {cells[1]} | {cells[2]} |"
        )
    lines.append("")
    for sysname, (ok, total) in tallies.items():
        if total:
            lines.append(f"- **{sysname}** 通過 {ok}/{total}"
                         f"（{100.0*ok/total:.0f}%）")
    if easypot_n:
        avg = easypot_rate_sum / easypot_n
        suffix = f"（每題 {repeat} 次取平均）" if repeat > 1 else ""
        lines.append(f"- **easypot** 平均通過率 {avg:.1f}%{suffix}")
    if all_latencies:
        avg_l = sum(all_latencies) / len(all_latencies)
        mx = max(all_latencies)
        lines.append(f"- **延遲**：每次呼叫平均 {avg_l:.1f}s、最長 {mx:.1f}s"
                     f"（共 {len(all_latencies)} 次）")
    return "\n".join(lines)


async def main_async(args) -> int:
    gt_text = Path(args.ground_truth).read_text(encoding="utf-8")
    real = parse_ground_truth(gt_text)

    resolver = None
    if not args.dry_run:
        resolver = build_resolver(args.model, args.base_url)

    cowrie = {}
    if args.cowrie:
        cowrie = parse_ground_truth(Path(args.cowrie).read_text(encoding="utf-8"))

    rows = []
    for probe in PROBES:
        row: dict = {"probe": probe}

        ra = real.get(probe.id)
        if ra:
            row["real"] = classify(probe, ra.output, ra.exit_code, "real")

        if args.dry_run:
            # 純驗證管線：用 real 輸出灌 easypot 欄（單次）。
            if ra:
                j = classify(probe, ra.output, ra.exit_code, "easypot")
                row["easypot"] = (int(j.passed), [j], [ra.output], [0.0])
        elif resolver is not None:
            row["easypot"] = await _easypot_trials(
                resolver, probe, args.repeat, args.verbose, args.hybrid)

        ca = cowrie.get(probe.id)
        if ca:
            row["cowrie"] = classify(probe, ca.output, ca.exit_code, "cowrie")

        rows.append(row)

    table = render_table(rows, args.repeat)
    print(table)
    if args.out:
        Path(args.out).write_text(table + "\n", encoding="utf-8")
        print(f"\n[已寫出對照表 → {args.out}]", file=sys.stderr)
    if args.detail_out and not args.dry_run:
        write_detail(rows, args.repeat, args.detail_out)
        print(f"[已寫出細項 → {args.detail_out}]", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="擬真度探測 runner（SALC/FALC 對照）")
    ap.add_argument("--ground-truth", required=True,
                    help="真機基準檔（capture_ground_truth.sh 的輸出）")
    ap.add_argument("--model", default="qwen2.5:14b")
    ap.add_argument("--base-url", default="http://localhost:11434")
    ap.add_argument("--cowrie", default=None,
                    help="可選：Cowrie 對同題的輸出（同 ground_truth 格式）")
    ap.add_argument("--out", default=None, help="把對照表寫到檔案")
    ap.add_argument("--detail-out", default=None,
                    help="把每題每次的判定+原始輸出寫成結構化檔（供人工複核、"
                         "引用露餡案例）")
    ap.add_argument("--repeat", type=int, default=1,
                    help="每題重跑次數（消化 LLM 隨機性；建議 8-10）")
    ap.add_argument("--hybrid", action="store_true",
                    help="easypot 欄走**攻擊者實際路徑**（完整 Interpreter：hit→內建、miss→LLM），而非預設的 LLM-only 下界")
    ap.add_argument("--dry-run", action="store_true",
                    help="不連 LLM，用 real 輸出灌 easypot 欄，驗證判定管線")
    ap.add_argument("--verbose", action="store_true",
                    help="印出 easypot 每題原始輸出（除錯用）")
    args = ap.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
