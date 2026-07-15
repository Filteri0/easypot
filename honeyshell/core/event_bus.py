"""同步 pub/sub 稽核匯流排。

為何同步、不用 asyncio.Queue
----------------------------
發布點（interpreter、session）多在 async context，但「發布」本身必須：
  * 零延遲、不阻塞蜜罐主流程 —— 稽核不能拖慢對攻擊者的回應，否則露餡；
  * 不因某個 sink 失敗而中斷蜜罐運作。
因此 emit() 是同步、盡量無副作用的分派：把事件推給每個 listener。
listener 若需要做 IO（寫檔、送遠端），自己在內部開 asyncio.create_task 或
交給背景執行緒；bus 不替 listener 決定並行策略。

隔離性保證
----------
單一 listener 拋例外不得影響其他 listener，也不得往上炸回發布端（蜜罐）。
例外被捕捉並記到內部 logger。這是蜜罐穩定性的硬需求。

設計血緣
--------
取代 HANDOFF §5 目前的 login_logger callback：改為統一的事件訂閱模型。
LoggingSink 讓現有 logging 行為無縫接上；未來的 JSONLSink / MetricsSink /
SIEMSink 只要 subscribe 即可，發布端不動。
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, TextIO

from .events import Event, EventType

__all__ = ["Listener", "EventBus", "LoggingSink", "JSONLSink"]

# listener 簽章：吃一個 Event，回傳忽略。
Listener = Callable[[Event], None]

_logger = logging.getLogger("honeyshell.core.event_bus")


@dataclass
class EventBus:
    """同步事件匯流排。

    用法
    ----
        bus = EventBus()
        bus.subscribe(my_listener)                 # 訂閱全部事件
        bus.subscribe(cmd_listener, EventType.COMMAND)  # 只訂閱某類
        bus.emit(LoginEvent(...))                   # 發布

    subscribe 回傳一個 unsubscribe callable，方便測試與臨時掛勾。
    """

    # 每個 EventType → 該類專屬 listeners；None 鍵存「訂閱全部」的 listeners。
    _subscribers: dict = field(default_factory=dict)

    def subscribe(
        self, listener: Listener, event_type: EventType | None = None
    ) -> Callable[[], None]:
        """訂閱事件。event_type=None 表示接收所有事件。

        回傳 unsubscribe()：呼叫後移除此訂閱。
        """
        bucket = self._subscribers.setdefault(event_type, [])
        bucket.append(listener)

        def _unsubscribe() -> None:
            try:
                bucket.remove(listener)
            except ValueError:
                pass  # 已被移除，idempotent

        return _unsubscribe

    def emit(self, event: Event) -> None:
        """同步分派事件給相符的 listeners。

        分派對象 = 訂閱該事件 type 的 listeners + 訂閱全部（None）的 listeners。
        任一 listener 拋例外都被捕捉，不影響其他 listener、不炸回發布端。
        """
        targets: list[Listener] = []
        specific = self._subscribers.get(event.type)
        if specific:
            targets.extend(specific)
        catch_all = self._subscribers.get(None)
        if catch_all:
            targets.extend(catch_all)

        for listener in targets:
            try:
                listener(event)
            except Exception:  # noqa: BLE001 — 蜜罐穩定性優先，吞掉並記錄
                _logger.exception(
                    "event listener raised; isolated (event=%s id=%s)",
                    event.type,
                    event.event_id,
                )

    def listener_count(self, event_type: EventType | None = None) -> int:
        """回傳某類（或全部訂閱）目前的 listener 數，供測試/診斷。"""
        return len(self._subscribers.get(event_type, []))


@dataclass
class LoggingSink:
    """把事件轉成人類可讀 log 行的內建 listener。

    無縫接上現有 logging 行為：登入成敗、命令、下載、LLM 統計都輸出一行。
    掛法：
        bus.subscribe(LoggingSink())          # 用預設 logger
        bus.subscribe(LoggingSink(logger=lg)) # 注入自訂 logger

    刻意保持格式簡單；結構化輸出（JSONL）由另一個 sink 負責，不混在這裡。
    """

    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("honeyshell.audit")
    )
    level: int = logging.INFO

    def __call__(self, event: Event) -> None:
        self.logger.log(self.level, self._format(event))

    @staticmethod
    def _format(event: Event) -> str:
        et = event.type
        sid = event.session_id or "-"
        if et is EventType.SESSION_START:
            return f"[{sid}] session start src={event.src_ip}:{event.src_port}"
        if et is EventType.SESSION_END:
            return (
                f"[{sid}] session end duration={event.duration}s "
                f"commands={event.command_count}"
            )
        if et is EventType.LOGIN:
            outcome = "OK" if event.success else "FAIL"
            return (
                f"[{sid}] login {outcome} user={event.username!r} "
                f"pass={event.password!r}"
            )
        if et is EventType.COMMAND:
            tag = "hit" if event.hit else "miss"
            return f"[{sid}] cmd ({tag}) {event.raw!r} -> {event.resolved_name}"
        if et is EventType.DOWNLOAD:
            return f"[{sid}] download url={event.url!r} outfile={event.outfile}"
        if et is EventType.LLM:
            cache = "cached" if event.cached else "live"
            return (
                f"[{sid}] llm ({cache}) model={event.model} "
                f"tok_in={event.prompt_tokens} tok_out={event.response_tokens} "
                f"lat={event.latency_ms}ms"
            )
        if et is EventType.ERROR:
            return (
                f"[{sid}] error phase={event.phase} exc={event.exc_type} "
                f"cmd={event.raw!r}"
            )
        return f"[{sid}] event {et}"


@dataclass
class JSONLSink:
    """把事件以 JSON Lines（每行一個 JSON 物件）落地到檔案。

    為何是 JSONL 而非單一 JSON 陣列
    --------------------------------
    JSONL 可 append-only 寫入、逐行讀取、天然適合串流給 collector/分析端，
    不必把整個檔案讀進記憶體或維護陣列括號。每行是一個 ``event.to_dict()``。

    穩定性
    ------
    寫入包在 try 內：磁碟滿、權限錯等 IO 例外被吞掉並記到內部 logger，
    絕不炸回 EventBus.emit（進而絕不影響蜜罐主流程）。這與 emit 的隔離
    保證一致——稽核落地失敗，蜜罐照常運作、不露餡。

    並行
    ----
    一把 threading.Lock 序列化寫入，讓多個 session 併發 emit 時每行完整、
    不交錯。emit 本身同步且快，鎖持有時間極短。

    掛法
    ----
        sink = JSONLSink("audit.jsonl")
        bus.subscribe(sink)
        ...
        sink.close()   # 程式結束時關檔（或用 with）
    """

    path: str
    _fh: Optional[TextIO] = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False,
                                  repr=False)

    def __post_init__(self) -> None:
        # 確保父目錄存在；開檔失敗只記錄，不讓 sink 建構炸掉呼叫端。
        try:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(self.path, "a", encoding="utf-8")
        except Exception:  # noqa: BLE001 — any open failure disables the sink
            _logger.exception("JSONLSink: cannot open %s; sink disabled",
                              self.path)
            self._fh = None

    def __call__(self, event: Event) -> None:
        fh = self._fh
        if fh is None:
            return
        try:
            line = json.dumps(event.to_dict(), ensure_ascii=False)
            with self._lock:
                fh.write(line + "\n")
                fh.flush()
        except Exception:  # noqa: BLE001 — audit IO must never break the honeypot
            _logger.exception("JSONLSink: write failed (event=%s)", event.type)

    def close(self) -> None:
        with self._lock:
            if self._fh is not None:
                try:
                    self._fh.close()
                finally:
                    self._fh = None

    def __enter__(self) -> "JSONLSink":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
