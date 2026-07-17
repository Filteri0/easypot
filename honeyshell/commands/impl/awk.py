"""awk —— 樣式掃描與欄位提取（常見子集）。

設計血緣（HANDOFF §28、§32；「做法 B」）
-------------------------------------------
``awk`` 是真實重放流量中**最大的覆蓋缺口**（2497 次 miss，top_miss 第一名）。
幾乎每一次真實呼叫都是從其他命令用管線接進來的欄位提取 idiom：

    cat /proc/cpuinfo | grep name | awk '{print $4}'
    awk '{print $2 ,$3, $4, $5, $6, $7}'
    ifconfig | awk '{print $2}'

這些是確定性的，該由內建處理（依 §4 的 hit/miss 分工）：假造它們很容易、
且能讓一個 session 內輸出保持一致。我們**刻意不模擬**的部分——樣式
（``/re/{...}``）、``BEGIN``/``END``、算術、``NR``/``NF`` 邏輯、字串函式、
賦值、多語句——罕見，且交給 LLM **生成**比手刻更好。遇到這些，命令會
raise :class:`DeferToLLM`，interpreter 會把它記成**真正的 miss**（hit=False）
並轉交給模型。這讓 miss rate 這個數字保持誠實（HANDOFF §21/§32）：一個被降級的
複雜 awk 算 miss、不算 hit，即使它有註冊類別。

支援的 program 文法（其餘一律降級）
--------------------------------------------------
* 單一動作區塊 ``{ print ARGS }``（容忍內外空白與尾端 ``;``）。不含前置樣式、
  不含 ``BEGIN``/``END``。
* ARGS：以逗號分隔的項目，每項為欄位參照（``$1`` .. ``$N``、``$0`` 整行、
  ``$NF`` 最後一欄）或單/雙引號字串字面。無參數的 bare ``print`` 等同 ``print $0``。
* ``-F SEP`` / ``-FSEP`` 設定欄位分隔符（預設：連續空白，對齊 awk 預設切分——
  非單一空格）。
* 輸出欄位分隔符（OFS）為單一空格（awk 預設）；記錄中的尾端 ``;`` 不模擬。

欄位語意對齊 awk：使用預設分隔符時，忽略前後空白、以連續空白切分。指定 ``-F``
時，該行以該字面分隔符切分（每一次出現都切）。

透過 :class:`_FileOrStdin` 讀取檔案運算元或 stdin，因此可在管線中組合。越界的
``$N`` 回空字串（awk 行為），絕不報錯。
"""

from __future__ import annotations

import re

from honeyshell.commands.base import DeferToLLM
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fileorstdin import _FileOrStdin

__all__ = ["Awk"]

# 欄位參照：$0、$1..、或 $NF。
_FIELD_RE = re.compile(r"^\$(?:NF|\d+)$")
# 我們唯一處理的 program 形狀：可選空白、{、print、args、可選 ;、}。
# 擷取 "print" 與結尾大括號之間的 args。
_PRINT_RE = re.compile(r"^\{\s*print\b(?P<args>.*?)\s*;?\s*\}$", re.DOTALL)


def _split_print_args(raw: str) -> list[str] | None:
    """以頂層逗號切分 print 的參數列。

    引號字串字面內的逗號不算分隔。回傳去除空白後的參數 token 串列；若語法不在
    我們模擬範圍內則回 None（會觸發降級）。空白 ``raw`` -> ``["$0"]``（bare
    ``print``）。
    """
    raw = raw.strip()
    if not raw:
        return ["$0"]
    args: list[str] = []
    cur = ""
    quote = None
    for ch in raw:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            cur += ch
            continue
        if ch == ",":
            args.append(cur.strip())
            cur = ""
            continue
        cur += ch
    if quote:  # 未閉合的字串字面 -> 不在我們的文法內
        return None
    args.append(cur.strip())
    return [a for a in args]


def _is_supported_arg(arg: str) -> bool:
    """我們能模擬的 print 參數：欄位參照或引號字串字面。"""
    if _FIELD_RE.match(arg):
        return True
    if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in ("'", '"'):
        return True
    return False


@register("awk", "/usr/bin/awk")
@register("gawk", "/usr/bin/gawk")
class Awk(_FileOrStdin):
    async def run(self) -> int:
        sep = None  # None => 預設以空白切分
        program = None
        operands: list[str] = []

        args = self.args
        i = 0
        while i < len(args):
            a = args[i]
            if a == "-F":
                sep = args[i + 1] if i + 1 < len(args) else ""
                i += 2
                continue
            if a.startswith("-F"):
                sep = a[2:]
                i += 1
                continue
            if a.startswith("-") and a != "-":
                # -v、-f progfile、--posix… ：不模擬 -> 降級。
                raise DeferToLLM
            # 第一個非旗標運算元是 program，其餘是檔案。
            if program is None:
                program = a
                i += 1
                continue
            operands.append(a)
            i += 1

        if program is None:
            # 真實 awk 沒帶 program 是用法錯誤，但這是罕見/退化情況；
            # 交給模型而非自行臆測。
            raise DeferToLLM

        # 在**寫任何輸出之前**先判定此 program 是否在支援文法內。若否，乾淨降級
        # （不留部分輸出，這樣 interpreter 轉交 LLM 時才不會重複列印）。
        m = _PRINT_RE.match(program.strip())
        if m is None:
            raise DeferToLLM
        parsed = _split_print_args(m.group("args"))
        if parsed is None or not all(_is_supported_arg(a) for a in parsed):
            raise DeferToLLM

        self._parsed_args = parsed
        self._sep = sep

        rc = 0
        async for _, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            for line in text.splitlines():
                self.line(self._render(line, parsed, sep))
        return rc

    def _render(self, line: str, parsed: list[str], sep: str | None) -> str:
        fields = self._fields(line, sep)
        out: list[str] = []
        for arg in parsed:
            if _FIELD_RE.match(arg):
                out.append(self._field_value(arg, line, fields))
            else:  # 引號字串字面
                out.append(arg[1:-1])
        return " ".join(out)  # OFS = 單一空格

    @staticmethod
    def _fields(line: str, sep: str | None) -> list[str]:
        if sep is None or sep == "":
            # 預設：以連續空白切分，忽略前後空白。
            return line.split()
        return line.split(sep)

    @staticmethod
    def _field_value(ref: str, line: str, fields: list[str]) -> str:
        if ref == "$0":
            return line
        if ref == "$NF":
            return fields[-1] if fields else ""
        idx = int(ref[1:])
        if idx == 0:
            return line
        return fields[idx - 1] if 1 <= idx <= len(fields) else ""

    async def fallback(self) -> int:
        """無 LLM 時的降級：整行回顯（類似 ``print $0``）。

        當複雜 awk 降級了、卻沒有模型可生成輸出時，逐行原樣輸出是最不可疑的
        行為——許多攻擊者的 awk one-liner 本就是 ``print`` 形狀，整行輸出是合理
        （雖不完美）的結果，遠勝於一個會暴露蜜罐的假造錯誤。只有在無 LLM 部署時
        才會走到；有 LLM 時改由 miss_handler 處理。
        """
        # 只重新解析到足以找出檔案運算元：跳過旗標，第一個裸 token 當 program，
        # 其餘當檔案。
        operands: list[str] = []
        seen_program = False
        i = 0
        args = self.args
        while i < len(args):
            a = args[i]
            if a == "-F":
                i += 2
                continue
            if a.startswith("-") and a != "-":
                i += 1
                continue
            if not seen_program:
                seen_program = True
                i += 1
                continue
            operands.append(a)
            i += 1
        rc = 0
        async for _, text in self._inputs(operands):
            if text is None:
                rc = 1
                continue
            for line in text.splitlines():
                self.line(line)
        return rc
