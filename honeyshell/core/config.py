"""蜜罐靜態設定的單一真實來源。

對應 HoneyGPT 論文
------------------
論文互動式 `(A_i, C_i, F_i) = LLM(P, S, Q_i, SR_i, H_i)` 中的靜態部分：
  * P（Principles，系統原則）  → `Principles`
  * S（System Setting，軟硬體）→ `SystemProfile`
本模組只承載「資料位」，不含 prompt 組裝邏輯（那是 backends/prompt_builder 的事）。
把 P/S 集中在此，未來 PromptBuilder 直接讀，避免設定散落。

格式決策
--------
用 JSON（與 fs.json 一致；HANDOFF §4 已定調 runtime 不碰 pickle，
也不引入 TOML/YAML 外部相依，符合 §6「core 零外部相依」）。

延後項
------
  * hostname/port 目前仍由 transport.ServerConfig 掌管；此處的 runtime 欄位
    先保留骨架，實際接線（讓 __main__ 從單一 config 派生）留待後續小步。
  * LLM 專用參數（temperature/top_p 等，論文 §3.3.3）先立位，backends 那輪再用。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

__all__ = [
    "Principles",
    "SystemProfile",
    "LLMSettings",
    "MemorySettings",
    "HoneypotConfig",
    "BOOT_AGE_SECONDS",
]

#: 模擬主機「已開機多久」的固定時長（約 7 天）。用作模擬時鐘的錨點：
#: boot_time = now - BOOT_AGE_SECONDS。session 層（uptime/who）與 LLM 補盲路徑
#: （resolver 注入給 LLM 的 current time / boot time）共用同一個值，避免兩條路徑
#: 各自算時鐘而漂移、讓 ps/date/uptime 的時間互相矛盾而露餡。
BOOT_AGE_SECONDS = 7 * 86400 + 3 * 3600 + 14 * 60  # 7 天 3:14


@dataclass
class Principles:
    """論文 P：LLM 扮演蜜罐時應遵循的原則（靜態行為指引）。

    本版只承載文字原則清單 + 幾個開關；實際注入 prompt 的組裝在 backends。
    """

    role: str = (
        "You are an authentic Linux terminal. Respond exactly as the shell "
        "would, maintaining a believable system to keep the user engaged."
    )
    # 時間敏感（論文 §3.3.1 Time Sensitivity）：是否在 prompt 注入當前時間/開機時間。
    inject_time: bool = True
    # 輸出格式（論文 §3.3.1）：要求 LLM 以 JSON 回 (A_i, C_i, F_i)。
    require_json_output: bool = True
    # few-shot 範例數（論文建議 4–5；此處用 6 對以涵蓋「未知命令模擬成功」的
    # downloader / installer 範例——它們是 command-not-found 修正的關鍵錨點，
    # 詳見 backends/prompt_builder.py 的 _FEWSHOT 註解）。
    few_shot_examples: int = 6
    # 額外自由文字原則（逐條）。PromptBuilder 會把每條注入系統畫像。
    # 預設帶「DB 主機人設」引導，讓 LLM 生成的 log/process/config 與 fs.json
    # 的靜態 PostgreSQL/Redis 痕跡一致（cat 命中的靜態內容是 LLM 失效時的預設；
    # LLM 在線時則朝同一方向生成，兩者不打架）。
    extra_rules: list[str] = field(
        default_factory=lambda: [
            "This host is a production PostgreSQL 13 + Redis database server. "
            "Running services include postgresql (port 5432), redis-server "
            "(port 6379) and sshd (port 22). When emulating logs, process "
            "listings, config files or command output, stay consistent with a "
            "busy database host: reference postgres/redis processes, /var/lib/"
            "postgresql/13/main, /var/log/postgresql/, connection activity and "
            "backup jobs. Do NOT invent a web stack (nginx/apache/php) unless "
            "the attacker explicitly creates it.",
        ]
    )


@dataclass
class SystemProfile:
    """論文 S：被模擬終端的軟硬體設定。

    hardware / software 兩大類（對齊論文 §3.3.2）。欄位刻意保守，
    夠 PromptBuilder 組出可信系統畫像即可，之後按需擴充。
    """

    # --- 身分 / 軟體 ---
    # 人設：一台在服役的 PostgreSQL/Redis 正式資料庫機（高價值誘捕目標）。
    # services/open_ports 會被 PromptBuilder 注入系統畫像，引導 LLM 生成
    # 與 DB 主機一致的輸出（log、process、config），與 data/fs.json 的靜態
    # 痕跡對齊，避免「VFS 是 DB 機、LLM 卻生成 nginx」的兩層打架。
    hostname: str = "happydog"
    os_name: str = "Debian GNU/Linux"
    os_version: str = "11 (bullseye)"
    kernel: str = "5.10.0-19-amd64"
    architecture: str = "x86_64"
    default_user: str = "root"
    open_ports: list[int] = field(
        default_factory=lambda: [22, 5432, 6379]  # sshd / PostgreSQL / Redis
    )
    services: list[str] = field(
        default_factory=lambda: ["sshd", "postgresql", "redis-server"]
    )

    # --- 硬體（高階 GPU/CPU 可誘引特定攻擊者，論文 §3.3.2）---
    cpu_model: str = "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz"
    cpu_count: int = 4
    memory_mb: int = 8192
    gpu: str | None = None  # 例："NVIDIA GeForce RTX 3090" 可誘 crypto-miner


@dataclass
class LLMSettings:
    """LLM 推論參數（論文 §3.3.3；本版僅立位，backends 那輪使用）。"""

    model: str = "qwen2.5:14b"
    temperature: float = 0.1
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    # hybrid 部署（論文 §3.4）：是否啟用 cache / 簡單命令走 emulated。
    enable_cache: bool = True


@dataclass
class MemorySettings:
    """多輪記憶與 Memory Pruning 參數（論文 §3.2.2）。

    weaken_factor w：時間衰減，每輪把各筆 impact 乘以 w。論文推導出的合理
    範圍 (0.623, 1]，使三步前的高權限命令權重仍大於新命令；預設 0.8。

    max_prompt_chars：prompt 長度上限的字元近似（本地模型無統一 tokenizer，
    以字元數估算，約 4 字元/token）。超過時觸發裁剪，移除 impact 最小的歷史
    項。預設 8000 字元 ≈ 2000 token，對齊論文 §4.6 的平均 prompt 規模。
    """

    weaken_factor: float = 0.8
    max_prompt_chars: int = 8000
    #: 至少保留最近 N 筆歷史，避免裁剪把當前上下文清空。
    min_keep: int = 2


@dataclass
class HoneypotConfig:
    """頂層設定聚合。

    from_json / to_json 做 round-trip；未知鍵忽略（前向相容），
    缺鍵用 dataclass 預設補齊。
    """

    principles: Principles = field(default_factory=Principles)
    system: SystemProfile = field(default_factory=SystemProfile)
    llm: LLMSettings = field(default_factory=LLMSettings)
    memory: MemorySettings = field(default_factory=MemorySettings)

    # ---- 序列化 ----

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, path: str | Path, *, indent: int = 2) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=indent, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HoneypotConfig":
        """從 dict 建構；只取各子設定認得的鍵，未知鍵忽略。"""
        return cls(
            principles=_build(Principles, data.get("principles")),
            system=_build(SystemProfile, data.get("system")),
            llm=_build(LLMSettings, data.get("llm")),
            memory=_build(MemorySettings, data.get("memory")),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "HoneypotConfig":
        raw = Path(path).read_text(encoding="utf-8")
        return cls.from_dict(json.loads(raw))


def _build(kls, data: dict[str, Any] | None):
    """用 dict 建構 dataclass，過濾掉未知欄位（前向相容）。"""
    if not data:
        return kls()
    fields = {f.name for f in kls.__dataclass_fields__.values()}
    known = {k: v for k, v in data.items() if k in fields}
    return kls(**known)
