"""awk 內建的測試（#1 覆蓋缺口，HANDOFF §28）。

涵蓋支援的 ``{print $N}`` 子集（確定性欄位提取），以及複雜 program
（樣式/BEGIN/算術）的 DeferToLLM 降級路徑，包含驗證降級的 awk：(a) 在 audit
被記為 miss、(b) 有接 LLM 時轉交 miss_handler、(c) 無 LLM 時退回整行輸出。

兩種跑法：
    python -m pytest tests/test_awk.py
    python tests/test_awk.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.commands import (  # noqa: E402
    ShellContext,
    StringReader,
    StringWriter,
    discover,
    resolve,
)
from honeyshell.commands.base import Command, DeferToLLM  # noqa: E402
from honeyshell.core.events import CommandEvent  # noqa: E402
from honeyshell.shell.interpreter import Interpreter  # noqa: E402
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402

discover()


def _ctx(cwd="/tmp"):
    return ShellContext(fs=build_sample_fs(hostname="svr04"), cwd=cwd,
                        username="root")


def _run(tail, stdin="", ctx=None):
    ctx = ctx or _ctx()
    cls = resolve("awk")
    assert cls is not None, "awk not registered"
    out, err = StringWriter(), StringWriter()
    code = asyncio.run(cls(ctx, ["awk", *tail], StringReader(stdin), out,
                           err).run())
    return code, out.getvalue(), err.getvalue()


def _defers(tail, stdin=""):
    """以這組參數跑 awk 若 raise DeferToLLM 則回 True。"""
    ctx = _ctx()
    cls = resolve("awk")
    out, err = StringWriter(), StringWriter()
    try:
        asyncio.run(cls(ctx, ["awk", *tail], StringReader(stdin), out,
                        err).run())
        return False, out.getvalue()
    except DeferToLLM:
        return True, out.getvalue()


# --- registration --------------------------------------------------------


def test_awk_registered():
    assert resolve("awk") is not None
    assert resolve("gawk") is not None, "gawk alias should register"


# --- supported {print $N} subset -----------------------------------------


def test_print_single_field():
    # 真實 fixture idiom：cat /proc/cpuinfo | grep name | awk '{print $4}'
    _, out, _ = _run(["{print $4}"], stdin="model name : Intel Core i7\n")
    assert out == "Intel\n"


def test_print_multi_field_comma_spacing():
    # 真實 fixture：awk '{print $2 ,$3, $4, $5, $6, $7}'
    _, out, _ = _run(["{print $2 ,$3, $4}"], stdin="a b c d e\n")
    assert out == "b c d\n"


def test_print_trailing_semicolon():
    # 真實 fixture：awk '{print $4,$5,$6,$7,$8,$9;}'
    _, out, _ = _run(["{print $1,$2;}"], stdin="x y z\n")
    assert out == "x y\n"


def test_field_separator_colon():
    _, out, _ = _run(["-F:", "{print $1}"], stdin="root:x:0:0:root\n")
    assert out == "root\n"


def test_field_separator_attached():
    _, out, _ = _run(["-F,", "{print $2}"], stdin="a,b,c\n")
    assert out == "b\n"


def test_whole_line_field_zero():
    _, out, _ = _run(["{print $0}"], stdin="hello world\n")
    assert out == "hello world\n"


def test_last_field_nf():
    _, out, _ = _run(["{print $NF}"], stdin="a b c\n")
    assert out == "c\n"


def test_string_literal():
    _, out, _ = _run(['{print "IP:", $1}'], stdin="10.0.0.1 foo\n")
    assert out == "IP: 10.0.0.1\n"


def test_bare_print_is_dollar_zero():
    _, out, _ = _run(["{print}"], stdin="whole line\n")
    assert out == "whole line\n"


def test_out_of_range_field_empty():
    # awk 對缺少的欄位印空字串，絕不報錯。
    _, out, _ = _run(["{print $9}"], stdin="a b\n")
    assert out == "\n"


def test_default_split_collapses_whitespace():
    # 預設 FS 忽略前導與連續空白（awk 語意）。
    _, out, _ = _run(["{print $1}"], stdin="   spaced    out   here\n")
    assert out == "spaced\n"


def test_multiple_lines():
    _, out, _ = _run(["{print $2}"], stdin="a b\nc d\ne f\n")
    assert out == "b\nd\nf\n"


# --- defer: complex programs go to the LLM -------------------------------


def test_defer_pattern():
    deferred, out = _defers(["/root/{print $1}"], stdin="root x\n")
    assert deferred
    assert out == "", "must not emit partial output before deferring"


def test_defer_begin_block():
    deferred, _ = _defers(["BEGIN{print \"hi\"}"])
    assert deferred


def test_defer_arithmetic():
    deferred, _ = _defers(["{print $1+$2}"], stdin="1 2\n")
    assert deferred


def test_defer_nr_filter():
    deferred, _ = _defers(["NR==1{print}"], stdin="a\nb\n")
    assert deferred


def test_defer_dash_v_assignment():
    deferred, _ = _defers(["-v", "x=1", "{print $1}"], stdin="a\n")
    assert deferred


def test_defer_field_function():
    deferred, _ = _defers(["{print substr($1,1,3)}"], stdin="abcdef\n")
    assert deferred


# --- defer routing through the interpreter (miss + miss_handler) ---------


class _StubLLM(Command):
    """代替 LLM miss_handler：回顯一個標記，讓測試能看出它有被走到。"""

    async def run(self) -> int:
        self.line("<llm-generated>")
        return 0


def _events_sink():
    events = []

    class Bus:
        def emit(self, ev):
            events.append(ev)

    return events, Bus()


def test_deferred_awk_audited_as_miss_and_routed_to_llm():
    events, bus = _events_sink()
    ctx = _ctx()
    ctx.event_bus = bus

    def miss_handler(c, argv, stdin, stdout, stderr):
        return _StubLLM(c, argv, stdin, stdout, stderr)

    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err,
                         miss_handler=miss_handler)
    code = asyncio.run(interp.execute("awk '/x/{print $1}'"))

    # 已轉交 LLM stub。
    assert "<llm-generated>" in out.getvalue()
    # 在 audit 被記為真正的 miss，而非 hit。
    cmd_events = [e for e in events if isinstance(e, CommandEvent)]
    assert len(cmd_events) == 1
    assert cmd_events[0].hit is False
    assert cmd_events[0].resolved_name is None


def test_deferred_awk_fallback_without_llm():
    # 沒接 miss_handler：降級的 awk 必須退回整行輸出（不是 "command not
    # found"——執行檔存在）且絕不崩潰。
    ctx = _ctx()
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)  # miss_handler=None
    # 用 echo 餵輸入，讓管線把 stdin 供給 awk。
    code = asyncio.run(interp.execute("echo 'a b c' | awk '/x/{print $2}'"))
    assert "command not found" not in err.getvalue()
    # fallback 整行回顯。
    assert out.getvalue() == "a b c\n"


def test_simple_awk_still_hit_in_interpreter():
    # 支援的 program 必須維持正常 hit（dispatch 重構的回歸防線）。
    events, bus = _events_sink()
    ctx = _ctx()
    ctx.event_bus = bus
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    asyncio.run(interp.execute("echo 'a b c' | awk '{print $2}'"))
    assert out.getvalue() == "b\n"
    cmd_events = [e for e in events if isinstance(e, CommandEvent)
                  and e.raw.startswith("awk")]
    assert cmd_events and cmd_events[0].hit is True
    assert cmd_events[0].resolved_name == "awk"


def _run_standalone():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
