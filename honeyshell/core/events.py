"""結構化稽核事件（audit events）。

設計血緣
--------
取代 HANDOFF §5 目前散落的 `ServerConfig.login_logger` callback + 裸 logging。
把「登入 / 命令 / 下載 / session / LLM」統一成 dataclass 事件，讓：
  * 現有 logging 行為可無縫接上（見 event_bus.LoggingSink）；
  * 未來 HoneyGPT 的成本 / 記憶統計（論文 §4.6）有結構化來源可聚合；
  * 之後可再掛 JSONL / SIEM / metrics sink 而不動發布端。

與 dict 事件的差異
------------------
刻意用型別階層而非 dict：欄位明確、可被靜態檢查、序列化格式穩定。
每個事件自帶 `event_id`（uuid4）與 `timestamp`（epoch 秒，float），
發布端不必自己造這兩個欄位。

延後項（本版不做，等 backends/ 那輪）
------------------------------------
  * `CommandEvent.hit` 與 `LLMEvent` 只立欄位，暫不接線 emit。
  * DownloadEvent 預留給未來 wget/curl 命令。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

__all__ = [
    "EventType",
    "Event",
    "SessionStartEvent",
    "SessionEndEvent",
    "LoginEvent",
    "CommandEvent",
    "DownloadEvent",
    "LLMEvent",
]


class EventType(str, Enum):
    """事件種類標籤。

    繼承 str 讓值可直接當字串用（JSON 序列化、log 格式化），
    同時保有 enum 的可列舉性。
    """

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    LOGIN = "login"
    COMMAND = "command"
    DOWNLOAD = "download"
    LLM = "llm"


def _new_event_id() -> str:
    return uuid.uuid4().hex


@dataclass
class Event:
    """所有稽核事件的基底類。

    子類必須以 `type: EventType = <值>` 覆寫（欄位有預設值，可放在
    基底欄位之後）。`session_id` 對應一條 SSH 連線；跨事件關聯用。
    """

    type: EventType = field(init=False, default=None)  # 由子類覆寫
    session_id: Optional[str] = None
    event_id: str = field(default_factory=_new_event_id)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """轉為純資料 dict（供 JSONL / SIEM sink）。

        EventType 因繼承 str，asdict 後即為字串值，可直接 json.dumps。
        """
        data = asdict(self)
        # asdict 會把 EventType 保留成 enum 實例的 value？實際上 str 子類
        # 序列化為其字串值；為保險明確轉字串。
        if isinstance(data.get("type"), EventType):
            data["type"] = data["type"].value
        return data


@dataclass
class SessionStartEvent(Event):
    """一條 SSH 連線建立。"""

    type: EventType = field(init=False, default=EventType.SESSION_START)
    src_ip: Optional[str] = None
    src_port: Optional[int] = None


@dataclass
class SessionEndEvent(Event):
    """一條 SSH 連線結束。

    duration 為秒；由發布端以 (end - start) 計算後填入，core 不自行計時，
    避免對 session 生命週期做假設。
    """

    type: EventType = field(init=False, default=EventType.SESSION_END)
    duration: Optional[float] = None
    command_count: int = 0


@dataclass
class LoginEvent(Event):
    """一次認證嘗試（對齊 Cowrie 記錄帳密與成敗）。"""

    type: EventType = field(init=False, default=EventType.LOGIN)
    username: str = ""
    password: str = ""
    success: bool = False


@dataclass
class CommandEvent(Event):
    """一行命令被直譯。

    欄位語意
    --------
    raw            : 攻擊者輸入的原始命令列（未展開）。
    resolved_name  : registry 命中的命令名；未命中為 None。
    hit            : registry 是否命中。False = 落到 LLM seam（未來走 backends）。
                     本版僅立欄位，emit 接線留給 backends/ 那輪。
    """

    type: EventType = field(init=False, default=EventType.COMMAND)
    raw: str = ""
    resolved_name: Optional[str] = None
    hit: bool = True


@dataclass
class DownloadEvent(Event):
    """攻擊者透過 wget/curl 等下載外部資源（預留）。"""

    type: EventType = field(init=False, default=EventType.DOWNLOAD)
    url: str = ""
    outfile: Optional[str] = None


@dataclass
class LLMEvent(Event):
    """一次 LLM 生成（對應論文 §4.6 成本/延遲統計，預留）。

    prompt_tokens / response_tokens / latency_ms 供成本聚合；
    cached=True 表示命中 hybrid 部署的 cache（論文 §3.4），未實際打 LLM。
    """

    type: EventType = field(init=False, default=EventType.LLM)
    model: str = ""
    prompt_tokens: int = 0
    response_tokens: int = 0
    latency_ms: float = 0.0
    cached: bool = False
