"""稽核聚合器（analyzer）—— 把 collector 的 ``_merged.jsonl`` 變成成果數字。

設計血緣
--------
承 HANDOFF §17「下一個要做的：analyzer」。collector（deploy/collector/collect.py）
已把 N 台蜜罐的事件合併成一份 JSONL、每行帶 ``_source`` 標記。這支把那份
raw log 做**結構化聚合**，產出三組對齊實習報告目標的數字：

  1. LlmEfficiency —— 規則命中 vs 走 LLM 的比例（hit=true / hit=false）。
     這是「混合架構值得做」的量化辯護，對應論文 §4.6 的 1.27%。
  2. Session       —— 按 session_id 串時間線：幾條 session、各打了幾條命令、
     憑證捕獲、走多深。蜜罐的**目的**是收情報。
  3. Intel         —— 命令頻率 top-N、憑證清單、兩蜜罐（_source）行為對比、
     最常 miss 的命令（= 蜜罐哪裡不夠像 = 未來補命令優先序）。

刻意不做（範圍守紀律）
----------------------
  * 不丟 LLM 分析：事件已被蜜罐標註 hit/resolved_name，聚合純結構化即可。
  * 不做即時 dashboard：批次跑一次產報告，符合一個月實習的節奏。
  * 不碰擬真度對照（native LLM vs 蜜罐 vs 真 Linux）：那是獨立的探測題庫工具，
    不靠這份 log。

輸入格式假設（以真實 emit 的 schema 為準，非臆測）
--------------------------------------------------
每行一個 JSON 物件，型別由 ``type`` 欄位區分：
  * command : {type, session_id, timestamp, raw, resolved_name, hit, _source}
  * login   : {type, session_id, timestamp, username, password, success, _source}
  * error   : {type, session_id, timestamp, raw, phase, exc_type, _source}
collector 對壞行/非 dict 會包成 {_source, _raw} 或 {_source, _value}——本模組
一律容忍：無法解讀的行計入 ``skipped``，不中斷聚合（與 collector「壞行不丟」一致）。

限制（誠實清單）
----------------
  * 目前 emit 端只發 command / error / login 三種事件，**未發 SessionStart**，
    故 audit 流裡**沒有 src_ip**。session 以 ``session_id`` 關聯；per-IP 分析
    需未來補 SessionStartEvent 的 emit 接線。此處 session 的「來源」以 _source
    （哪台蜜罐）表示，非攻擊者 IP。

資料集互動噪音過濾（replay 專屬，見 HANDOFF §19.3）
--------------------------------------------------
Cowrie 公開資料集的 ``input.csv`` 把「攻擊者輸入」與「互動程式的輸出提示」
混在同一欄。replay 忠實重放整欄 → passwd 之類互動程式的提示字串（如
``New password:``、``Changing password for root``）被當成命令送進蜜罐、
registry 找不到 → 被記成 ``hit=false``。實測這類噪音佔 miss 逾三成，會嚴重
**灌高 miss_rate**，讓報告核心數字失真。

本模組在**分析層**（非 replay 層）用精確 / 前綴匹配把這些互動提示排除在
miss 統計外，理由：
  * raw log 保留原貌（記錄了資料集的真實缺陷，本身是情報素材）；
  * 過濾規則可迭代，改規則隨時重算，不必重跑 replay（十幾分鐘 + 佔 Ollama）；
  * replay 的職責是忠實重放，清洗屬分析層（關注點分離）。

**關鍵：只用白名單式精確匹配，絕不誤殺真命令。** ``chpasswd``、``awk '...'``
等雖同為 ``resolved_name=null, hit=false``，但它們是真實工具、真實的覆蓋
缺口（正是 miss_rate 該計入的），故不匹配任何提示樣式 → 保留。被過濾的筆數
另計於 ``interactive_noise`` 並在報告透明呈現（不藏）。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

__all__ = [
    "load_events",
    "is_interactive_noise",
    "is_credential_noise",
    "LlmEfficiency",
    "LlmCost",
    "SessionSummary",
    "IntelSummary",
    "Report",
    "analyze",
    "main",
]


# --------------------------------------------------------------------------- #
# 載入
# --------------------------------------------------------------------------- #

def load_events(lines: Iterable[str]) -> tuple[list[dict[str, Any]], int]:
    """把 JSONL 逐行解析成 dict 事件。

    回傳 ``(events, skipped)``。skipped 計入：JSON 解析失敗、非 dict、或
    collector 包裝的無法解讀行（帶 ``_raw``）。這些不算「事件」但也不丟掉
    計數，好讓報告能誠實反映 log 品質。

    以純字串迭代為輸入（而非檔案路徑），讓單元測試能直接餵 list[str]，
    不必造暫存檔——與專案「純函式好測」的慣例一致。
    """
    events: list[dict[str, Any]] = []
    skipped = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            skipped += 1
            continue
        if not isinstance(obj, dict):
            skipped += 1
            continue
        # collector 對壞行的包裝：{_source, _raw} —— 無真正事件內容，跳過。
        if "_raw" in obj and "type" not in obj:
            skipped += 1
            continue
        # collector 對非 dict JSON 的包裝：{_source, _value}——同樣無 type。
        if "_value" in obj and "type" not in obj:
            skipped += 1
            continue
        events.append(obj)
    return events, skipped


def _by_type(events: list[dict[str, Any]], t: str) -> list[dict[str, Any]]:
    return [e for e in events if e.get("type") == t]


# --------------------------------------------------------------------------- #
# 互動噪音過濾（見模組 docstring「資料集互動噪音過濾」）
# --------------------------------------------------------------------------- #

# passwd/su 等互動程式的輸出提示，被 Cowrie input.csv 混進命令欄。
# 精確匹配（整行 strip 後完全相等才算）——保守，避免誤殺真命令。
_INTERACTIVE_NOISE_EXACT: frozenset[str] = frozenset({
    "New password:",
    "Retype new password:",
    "Enter new UNIX password:",
    "Retype new UNIX password:",
    "Current password:",
    "passwd: password updated successfully",
    "passwd: all authentication tokens updated successfully.",
    "Sorry, passwords do not match.",
    "Sorry, passwords do not match",
})

# 帶可變尾巴的提示（如使用者名），用前綴匹配。
_INTERACTIVE_NOISE_PREFIX: tuple[str, ...] = (
    "Changing password for ",
    "BAD PASSWORD:",
    "passwd: Authentication token manipulation error",
)


def is_interactive_noise(raw: str | None, resolved_name: str | None) -> bool:
    """判斷一筆 command 事件是否為資料集互動噪音（非真攻擊者命令）。

    純函式，好單測。**保守設計：只在能明確認出提示字串時才回 True。**

    前提 ``resolved_name is None``：被 registry 命中的（有 resolved_name）
    必然是真命令，直接排除。未命中者才進一步比對提示樣式。

    刻意**不會**誤判以下真命令（它們是真實覆蓋缺口，該計入 miss）：
      * ``chpasswd``            —— 單 token，不符任何提示樣式
      * ``awk '{print $2}'``    —— 不符任何提示樣式
      * ``passwd``/``passwd root`` —— 是命令本身，非提示輸出
    """
    if resolved_name is not None:
        return False
    if not raw:
        return False
    r = raw.strip()
    if r in _INTERACTIVE_NOISE_EXACT:
        return True
    return any(r.startswith(p) for p in _INTERACTIVE_NOISE_PREFIX)


def _partition_noise(
    commands: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """把 command 事件分成 (真命令, 被過濾的噪音筆數)。"""
    real: list[dict[str, Any]] = []
    noise = 0
    for c in commands:
        if is_interactive_noise(c.get("raw"), c.get("resolved_name")):
            noise += 1
        else:
            real.append(c)
    return real, noise


# --------------------------------------------------------------------------- #
# 憑證噪音過濾（見 report bug：passwd 提示/命令被誤當密碼捕獲）
# --------------------------------------------------------------------------- #

def is_credential_noise(username: str, password: str) -> bool:
    """判斷一筆 login 事件的「密碼」是否其實是噪音，不是真憑證。

    根因：Cowrie 資料集把 passwd 互動的**提示字串**和**後續命令**混進輸入流，
    蜜罐把它們當成 LoginEvent 的 password 發出來，導致憑證統計被灌水
    （如 ``Enter new UNIX password:``、整條 ``cat /proc/cpuinfo | ... | awk`` 命令）。

    保守判定：password 命中以下任一即視為噪音——
      1. 是已知的 passwd/su 互動提示（精確或前綴，重用 _INTERACTIVE_NOISE_*）；
      2. 看起來是一整條命令而非密碼：含 shell metachar（``| ; & > <`` 反引號）、
         或含多個空白分隔的 token 且長度偏長（真密碼極少長成這樣）。

    真憑證（如 ``root:admin``、``root:123456``、``root:P@ssw0rd!``）不符任何條件 → 保留。
    """
    p = (password or "").strip()
    if not p:
        return True  # 空密碼無情報價值
    # (1) passwd 互動提示
    if p in _INTERACTIVE_NOISE_EXACT:
        return True
    if any(p.startswith(pre) for pre in _INTERACTIVE_NOISE_PREFIX):
        return True
    if p.startswith("Enter ") or p.endswith("password:") or p.endswith("UNIX password:"):
        return True
    # (2) 看起來是命令而非密碼
    if any(ch in p for ch in "|;&<>`"):
        return True
    if p.count(" ") >= 3 and len(p) > 20:  # 多 token 長字串 = 命令，不是密碼
        return True
    return False


def _partition_credentials(
    logins: list[dict[str, Any]],
) -> tuple[list[tuple[str, str, "Optional[str]"]], int]:
    """把 login 事件分成 (真憑證, 被過濾的噪音筆數)。"""
    creds: list[tuple[str, str, Optional[str]]] = []
    noise = 0
    for lg in logins:
        user = lg.get("username", "")
        pw = lg.get("password", "")
        if is_credential_noise(user, pw):
            noise += 1
        else:
            creds.append((user, pw, lg.get("_source")))
    return creds, noise

@dataclass
class LlmEfficiency:
    """混合架構的量化辯護：多少命令被規則吃掉、多少落到 LLM。

    ``hit=True``  = registry 命中內建命令（毫秒級、零成本）。
    ``hit=False`` = registry miss，落到 LLM seam（慢、耗資源）。
    miss_rate 就是規模化成本的關鍵：N 台蜜罐的 LLM 負載 ≈ 總命令 × miss_rate。
    """

    total_commands: int = 0
    rule_hits: int = 0
    llm_misses: int = 0
    # 最常落到 LLM 的原始命令（token 層），指出蜜罐覆蓋缺口。
    top_misses: list[tuple[str, int]] = field(default_factory=list)
    # 被過濾掉的資料集互動噪音筆數（passwd 提示等，非真命令）。
    # 已排除在 total_commands / llm_misses 之外，此處僅供報告透明呈現。
    interactive_noise: int = 0

    @property
    def hit_rate(self) -> float:
        if self.total_commands == 0:
            return 0.0
        return self.rule_hits / self.total_commands

    @property
    def miss_rate(self) -> float:
        if self.total_commands == 0:
            return 0.0
        return self.llm_misses / self.total_commands


def _analyze_llm(commands: list[dict[str, Any]], top_n: int = 15) -> LlmEfficiency:
    # 先剔除資料集互動噪音（passwd 提示等），再算 miss rate。
    # 噪音不是真命令，計入會灌高 miss_rate（實測逾三成 miss 是噪音）。
    real, noise = _partition_noise(commands)

    total = len(real)
    hits = sum(1 for c in real if c.get("hit"))
    misses = total - hits
    # miss 的命令以第一個 token 聚合（raw 是整行；取 argv[0] 當「命令名」）。
    miss_tokens: Counter[str] = Counter()
    for c in real:
        if not c.get("hit"):
            raw = (c.get("raw") or "").strip()
            token = raw.split()[0] if raw else "(empty)"
            miss_tokens[token] += 1
    return LlmEfficiency(
        total_commands=total,
        rule_hits=hits,
        llm_misses=misses,
        top_misses=miss_tokens.most_common(top_n),
        interactive_noise=noise,
    )


# --------------------------------------------------------------------------- #
# 目標三：Session 時間線
# --------------------------------------------------------------------------- #

@dataclass
class SessionRecord:
    """單一 session 的聚合視圖（按 session_id 串起所有事件）。"""

    session_id: str
    source: Optional[str] = None            # 哪台蜜罐（_source），非攻擊者 IP
    command_count: int = 0
    first_ts: Optional[float] = None
    last_ts: Optional[float] = None
    credentials: int = 0                    # 該 session 捕獲的憑證數
    errors: int = 0                         # 觸發的非預期例外數
    commands: list[str] = field(default_factory=list)  # 依時序的 raw 命令

    @property
    def duration(self) -> float:
        if self.first_ts is None or self.last_ts is None:
            return 0.0
        return max(0.0, self.last_ts - self.first_ts)


@dataclass
class SessionSummary:
    total_sessions: int = 0
    sessions: list[SessionRecord] = field(default_factory=list)

    @property
    def busiest(self) -> Optional[SessionRecord]:
        """命令數最多的 session（最活躍的攻擊者）。"""
        return max(self.sessions, key=lambda s: s.command_count, default=None)


def _analyze_sessions(events: list[dict[str, Any]]) -> SessionSummary:
    by_sid: dict[str, SessionRecord] = {}

    def rec(sid: Optional[str], source: Optional[str]) -> SessionRecord:
        key = sid or "(no-session)"
        r = by_sid.get(key)
        if r is None:
            r = SessionRecord(session_id=key, source=source)
            by_sid[key] = r
        elif r.source is None and source is not None:
            r.source = source
        return r

    # 依 timestamp 排序，確保時間線與 commands 順序正確。
    ordered = sorted(events, key=lambda e: e.get("timestamp") or 0.0)
    for e in ordered:
        sid = e.get("session_id")
        src = e.get("_source")
        r = rec(sid, src)
        ts = e.get("timestamp")
        if ts is not None:
            if r.first_ts is None:
                r.first_ts = ts
            r.last_ts = ts
        etype = e.get("type")
        if etype == "command":
            r.command_count += 1
            raw = e.get("raw")
            if raw:
                r.commands.append(raw)
        elif etype == "login":
            r.credentials += 1
        elif etype == "error":
            r.errors += 1

    sessions = sorted(
        by_sid.values(), key=lambda s: s.command_count, reverse=True
    )
    return SessionSummary(total_sessions=len(sessions), sessions=sessions)


# --------------------------------------------------------------------------- #
# 目標三延伸：情報聚合
# --------------------------------------------------------------------------- #

@dataclass
class IntelSummary:
    # 攻擊者最常打的命令（第一個 token）。
    top_commands: list[tuple[str, int]] = field(default_factory=list)
    # 捕獲的憑證：(username, password, source)。蜜罐的高價值產出。
    credentials: list[tuple[str, str, Optional[str]]] = field(default_factory=list)
    # 被過濾的假憑證數（passwd 提示/命令誤當密碼），已排除在 credentials 外。
    credential_noise: int = 0
    # 每台蜜罐（_source）的命令量對比。
    per_source_commands: dict[str, int] = field(default_factory=dict)
    # 每台蜜罐的 miss 量（規則覆蓋缺口是否因人設而異）。
    per_source_misses: dict[str, int] = field(default_factory=dict)
    # 觸發的錯誤型別頻率（攻擊者踩到的未覆蓋邊界）。
    error_types: list[tuple[str, int]] = field(default_factory=list)


def _analyze_intel(events: list[dict[str, Any]], top_n: int = 15) -> IntelSummary:
    commands = _by_type(events, "command")
    logins = _by_type(events, "login")
    errors = _by_type(events, "error")

    # 與 LlmEfficiency 一致：剔除互動噪音，per-source miss 才對得上頭條數字。
    real_commands, _ = _partition_noise(commands)

    cmd_tokens: Counter[str] = Counter()
    per_src_cmd: Counter[str] = Counter()
    per_src_miss: Counter[str] = Counter()
    for c in real_commands:
        raw = (c.get("raw") or "").strip()
        token = raw.split()[0] if raw else "(empty)"
        cmd_tokens[token] += 1
        src = c.get("_source") or "(unknown)"
        per_src_cmd[src] += 1
        if not c.get("hit"):
            per_src_miss[src] += 1

    creds, cred_noise = _partition_credentials(logins)

    err_types: Counter[str] = Counter()
    for er in errors:
        err_types[er.get("exc_type") or "(unknown)"] += 1

    return IntelSummary(
        top_commands=cmd_tokens.most_common(top_n),
        credentials=creds,
        credential_noise=cred_noise,
        per_source_commands=dict(per_src_cmd),
        per_source_misses=dict(per_src_miss),
        error_types=err_types.most_common(),
    )


# --------------------------------------------------------------------------- #
# LLM 成本（對照論文 §4.6：真打 LLM 率 / cache 命中率 / token / 延遲）
# --------------------------------------------------------------------------- #

@dataclass
class LlmCost:
    """從 LLMEvent 聚合真實成本。

    關鍵區分（回答「為何 miss rate ≠ 論文 1.27%」）：
      * miss rate（LlmEfficiency）= 規則沒接住的比例，**含 cache 命中**。
      * 真打 LLM 率（這裡）= miss 中扣掉 cache、真的呼叫模型的比例。
        這才對得上論文 §4.6 的 1.27%。

    需要蜜罐端把 LLMEvent emit 進 audit（bus 接線）。若資料裡沒有 llm 事件
    （舊資料 / 未接線），所有欄位為 0，報告會標「無 LLM 事件」。
    """

    llm_events: int = 0          # LLMEvent 總數（= miss 中進到 resolver 的）
    live_calls: int = 0          # 真打 LLM（cached=False）
    cache_hits: int = 0          # 走 cache（cached=True）
    total_prompt_tokens: int = 0
    total_response_tokens: int = 0
    total_latency_ms: float = 0.0

    @property
    def cache_hit_rate(self) -> float:
        return self.cache_hits / self.llm_events if self.llm_events else 0.0

    @property
    def avg_prompt_tokens(self) -> float:
        return self.total_prompt_tokens / self.live_calls if self.live_calls else 0.0

    @property
    def avg_response_tokens(self) -> float:
        return self.total_response_tokens / self.live_calls if self.live_calls else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.live_calls if self.live_calls else 0.0

    def live_call_rate(self, total_commands: int) -> float:
        """真打 LLM 佔「全部命令」的比例——對照論文 §4.6 的 1.27%。"""
        return self.live_calls / total_commands if total_commands else 0.0


def _analyze_llm_cost(events: list[dict[str, Any]]) -> LlmCost:
    llm_events = _by_type(events, "llm")
    c = LlmCost(llm_events=len(llm_events))
    for e in llm_events:
        if e.get("cached"):
            c.cache_hits += 1
        else:
            c.live_calls += 1
            c.total_prompt_tokens += int(e.get("prompt_tokens") or 0)
            c.total_response_tokens += int(e.get("response_tokens") or 0)
            c.total_latency_ms += float(e.get("latency_ms") or 0.0)
    return c


# --------------------------------------------------------------------------- #
# 組裝
# --------------------------------------------------------------------------- #

@dataclass
class Report:
    llm: LlmEfficiency
    sessions: SessionSummary
    intel: IntelSummary
    cost: LlmCost = field(default_factory=LlmCost)
    total_events: int = 0
    skipped_lines: int = 0

    def to_dict(self) -> dict[str, Any]:
        """結構化輸出（report.json）。session.commands 略去以免檔案爆量，
        只留摘要欄位；完整命令仍在原始 JSONL。"""
        return {
            "totals": {
                "events": self.total_events,
                "skipped_lines": self.skipped_lines,
                "commands": self.llm.total_commands,
                "sessions": self.sessions.total_sessions,
            },
            "llm_efficiency": {
                "total_commands": self.llm.total_commands,
                "rule_hits": self.llm.rule_hits,
                "llm_misses": self.llm.llm_misses,
                "hit_rate": round(self.llm.hit_rate, 4),
                "miss_rate": round(self.llm.miss_rate, 4),
                "top_misses": self.llm.top_misses,
                "interactive_noise_filtered": self.llm.interactive_noise,
            },
            "llm_cost": {
                "llm_events": self.cost.llm_events,
                "live_calls": self.cost.live_calls,
                "cache_hits": self.cost.cache_hits,
                "cache_hit_rate": round(self.cost.cache_hit_rate, 4),
                "live_call_rate": round(
                    self.cost.live_call_rate(self.llm.total_commands), 4),
                "avg_prompt_tokens": round(self.cost.avg_prompt_tokens, 1),
                "avg_response_tokens": round(self.cost.avg_response_tokens, 1),
                "avg_latency_ms": round(self.cost.avg_latency_ms, 1),
            },
            "sessions": [
                {
                    "session_id": s.session_id,
                    "source": s.source,
                    "command_count": s.command_count,
                    "duration_sec": round(s.duration, 2),
                    "credentials": s.credentials,
                    "errors": s.errors,
                }
                for s in self.sessions.sessions
            ],
            "intel": {
                "top_commands": self.intel.top_commands,
                "credentials": [
                    {"username": u, "password": p, "source": s}
                    for (u, p, s) in self.intel.credentials
                ],
                "credential_noise_filtered": self.intel.credential_noise,
                "per_source_commands": self.intel.per_source_commands,
                "per_source_misses": self.intel.per_source_misses,
                "error_types": self.intel.error_types,
            },
        }


def analyze(events: list[dict[str, Any]], skipped: int = 0,
            top_n: int = 15) -> Report:
    """純函式：吃事件 list，吐 Report。無 I/O，好單測。"""
    commands = _by_type(events, "command")
    return Report(
        llm=_analyze_llm(commands, top_n=top_n),
        sessions=_analyze_sessions(events),
        intel=_analyze_intel(events, top_n=top_n),
        cost=_analyze_llm_cost(events),
        total_events=len(events),
        skipped_lines=skipped,
    )


# --------------------------------------------------------------------------- #
# 呈現
# --------------------------------------------------------------------------- #

def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def render_console(report: Report) -> str:
    r = report
    L: list[str] = []
    L.append("=" * 60)
    L.append("  easypot 稽核聚合報告")
    L.append("=" * 60)
    L.append(f"事件總數: {r.total_events}    (略過壞行: {r.skipped_lines})")
    L.append("")

    # --- 目標二：LLM 效率（報告核心數字）---
    L.append("── LLM 效率（混合架構驗證）" + "─" * 30)
    e = r.llm
    L.append(f"  命令總數       : {e.total_commands}")
    L.append(f"  規則命中       : {e.rule_hits}  ({_pct(e.hit_rate)})")
    L.append(f"  走 LLM (miss)  : {e.llm_misses}  ({_pct(e.miss_rate)})")
    if e.interactive_noise:
        L.append(f"  （已濾互動噪音 : {e.interactive_noise} 筆，"
                 f"資料集 passwd 提示等，不計入上方統計）")
    if e.total_commands:
        L.append(f"  → 規模化意義   : N 台蜜罐的 LLM 負載約 = 總命令量 × "
                 f"{_pct(e.miss_rate)}")
    if e.top_misses:
        L.append("  最常走 LLM 的命令（= 覆蓋缺口）:")
        for name, n in e.top_misses[:10]:
            L.append(f"      {n:>4}  {name}")
    # --- LLM 成本（對照論文 §4.6，需 audit 有 llm 事件）---
    c = r.cost
    if c.llm_events:
        L.append("")
        L.append("  ── LLM 實際成本（§4.6 對照）──")
        L.append(f"  miss 進 resolver : {c.llm_events}")
        L.append(f"  走 cache         : {c.cache_hits}  "
                 f"({_pct(c.cache_hit_rate)})")
        L.append(f"  真打 LLM         : {c.live_calls}  "
                 f"(佔全部命令 {_pct(c.live_call_rate(e.total_commands))}"
                 f" ← 對照論文 1.27%)")
        if c.live_calls:
            L.append(f"  平均 prompt token: {c.avg_prompt_tokens:.0f}"
                     f"、response token: {c.avg_response_tokens:.0f}"
                     f"、延遲: {c.avg_latency_ms:.0f}ms")
    else:
        L.append("  （無 LLM 事件：此資料未含 llm 事件，無法算真打 LLM 率；"
                 "需蜜罐 emit LLMEvent）")
    L.append("")

    # --- 目標三：Session ---
    L.append("── Session 時間線" + "─" * 38)
    s = r.sessions
    L.append(f"  session 總數   : {s.total_sessions}")
    if s.busiest:
        b = s.busiest
        L.append(f"  最活躍 session : {b.session_id[:12]}… "
                 f"({b.command_count} 命令, {b.duration:.1f}s, "
                 f"憑證 {b.credentials}, 錯誤 {b.errors})")
    top_sessions = s.sessions[:5]
    if top_sessions:
        L.append("  前幾大 session（命令數）:")
        for rec in top_sessions:
            src = f" @{rec.source}" if rec.source else ""
            L.append(f"      {rec.command_count:>4} 命令  "
                     f"{rec.session_id[:12]}…{src}")
    L.append("")

    # --- 目標三：情報 ---
    L.append("── 情報產出" + "─" * 44)
    i = r.intel
    if i.top_commands:
        L.append("  攻擊者最常打的命令:")
        for name, n in i.top_commands[:10]:
            L.append(f"      {n:>4}  {name}")
    if i.credentials:
        L.append(f"  捕獲憑證（{len(i.credentials)} 組）:")
        for u, p, src in i.credentials[:15]:
            tag = f" @{src}" if src else ""
            L.append(f"      {u}:{p}{tag}")
    elif i.credential_noise:
        L.append("  捕獲憑證（0 組真憑證）")
    if i.credential_noise:
        L.append(f"  （已濾假憑證 : {i.credential_noise} 筆，"
                 f"passwd 提示/命令被誤當密碼，不計入）")
    if i.per_source_commands:
        L.append("  各蜜罐命令量對比:")
        for src in sorted(i.per_source_commands):
            miss = i.per_source_misses.get(src, 0)
            tot = i.per_source_commands[src]
            L.append(f"      {src:<14} {tot:>5} 命令  (miss {miss})")
    if i.error_types:
        L.append("  攻擊者觸發的錯誤型別:")
        for et, n in i.error_types:
            L.append(f"      {n:>4}  {et}")
    L.append("=" * 60)
    return "\n".join(L)


def render_markdown(report: Report) -> str:
    r = report
    e, s, i = r.llm, r.sessions, r.intel
    M: list[str] = []
    M.append("# easypot 稽核聚合報告\n")
    M.append(f"- 事件總數：**{r.total_events}**（略過壞行 {r.skipped_lines}）\n")

    M.append("## LLM 效率（混合架構驗證）\n")
    M.append("| 指標 | 數值 |")
    M.append("|---|---|")
    M.append(f"| 命令總數 | {e.total_commands} |")
    M.append(f"| 規則命中 | {e.rule_hits}（{_pct(e.hit_rate)}） |")
    M.append(f"| 走 LLM (miss) | {e.llm_misses}（{_pct(e.miss_rate)}） |")
    if e.interactive_noise:
        M.append(f"| 已濾互動噪音 | {e.interactive_noise}（資料集 passwd 提示等，"
                 f"不計入） |")
    M.append("")
    if e.interactive_noise:
        M.append(f"> 註：Cowrie 公開資料集把互動程式輸出（如 `New password:`）"
                 f"混入命令欄，本次過濾 **{e.interactive_noise}** 筆，避免灌高 "
                 f"miss rate。此為資料清洗，raw log 保留原貌。\n")
    M.append(f"> N 台蜜罐的 LLM 負載約 = 總命令量 × **{_pct(e.miss_rate)}**，"
             f"證明混合架構規模化成本可控。\n")
    if e.top_misses:
        M.append("**最常走 LLM 的命令（覆蓋缺口 / 未來補命令優先序）：**\n")
        M.append("| 命令 | 次數 |")
        M.append("|---|---|")
        for name, n in e.top_misses[:10]:
            M.append(f"| `{name}` | {n} |")
        M.append("")

    M.append("## Session 時間線\n")
    M.append(f"- session 總數：**{s.total_sessions}**")
    if s.busiest:
        b = s.busiest
        M.append(f"- 最活躍 session：`{b.session_id[:12]}…` "
                 f"（{b.command_count} 命令、{b.duration:.1f}s、"
                 f"憑證 {b.credentials}、錯誤 {b.errors}）")
    M.append("")

    M.append("## 情報產出\n")
    if i.top_commands:
        M.append("**攻擊者最常打的命令：**\n")
        M.append("| 命令 | 次數 |")
        M.append("|---|---|")
        for name, n in i.top_commands[:10]:
            M.append(f"| `{name}` | {n} |")
        M.append("")
    if i.credentials:
        M.append(f"**捕獲憑證（{len(i.credentials)} 組）：**\n")
        M.append("| 使用者 | 密碼 | 來源 |")
        M.append("|---|---|---|")
        for u, p, src in i.credentials[:15]:
            M.append(f"| `{u}` | `{p}` | {src or ''} |")
        M.append("")
    if i.credential_noise:
        M.append(f"> 已濾假憑證 **{i.credential_noise}** 筆（passwd 提示/命令"
                 f"被誤當密碼，不計入）。\n")
    if i.per_source_commands:
        M.append("**各蜜罐對比：**\n")
        M.append("| 蜜罐 | 命令量 | miss |")
        M.append("|---|---|---|")
        for src in sorted(i.per_source_commands):
            M.append(f"| {src} | {i.per_source_commands[src]} | "
                     f"{i.per_source_misses.get(src, 0)} |")
        M.append("")
    return "\n".join(M)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _read_lines(path: str) -> list[str]:
    if path == "-":
        return sys.stdin.read().splitlines()
    return Path(path).read_text(encoding="utf-8").splitlines()


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="honeyshell.analyze",
        description="聚合 collector 的 _merged.jsonl，產出成果數字。",
    )
    p.add_argument("jsonl", help="_merged.jsonl 路徑（'-' 讀 stdin）")
    p.add_argument("-f", "--format", choices=["console", "json", "md"],
                   default="console", help="輸出格式（預設 console）")
    p.add_argument("-o", "--output", help="寫入檔案（預設印到 stdout）")
    p.add_argument("--top", type=int, default=15, help="top-N 榜長度（預設 15）")
    args = p.parse_args(argv)

    try:
        lines = _read_lines(args.jsonl)
    except OSError as exc:
        print(f"error: 無法讀取 {args.jsonl}: {exc}", file=sys.stderr)
        return 2

    events, skipped = load_events(lines)
    report = analyze(events, skipped=skipped, top_n=args.top)

    if args.format == "json":
        out = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    elif args.format == "md":
        out = render_markdown(report)
    else:
        out = render_console(report)

    if args.output:
        Path(args.output).write_text(out + "\n", encoding="utf-8")
        print(f"報告已寫入 {args.output}", file=sys.stderr)
    else:
        try:
            print(out)
        except BrokenPipeError:
            # 下游（head/less）提早關閉管線是正常的，別噴 traceback。
            try:
                sys.stdout.close()
            except Exception:  # noqa: BLE001
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
