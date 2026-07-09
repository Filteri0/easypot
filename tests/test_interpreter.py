"""Tests for honeyshell.shell.expand and honeyshell.shell.interpreter.

Runnable two ways:
    python -m pytest tests/test_interpreter.py
    python tests/test_interpreter.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.commands import ShellContext, StringWriter  # noqa: E402
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402
from honeyshell.shell import Interpreter, expand_token  # noqa: E402


def _ctx(cwd="/", **env):
    environ = {"HOME": "/root", "USER": "root", "PATH": "/usr/bin:/bin"}
    environ.update(env)
    return ShellContext(
        fs=build_sample_fs(hostname="svr04"), cwd=cwd, environ=environ,
        username="root",
    )


def _sh(ctx=None):
    ctx = ctx or _ctx()
    out, err = StringWriter(), StringWriter()
    return Interpreter(ctx, out, err), out, err


def _exec(line, ctx=None):
    interp, out, err = _sh(ctx)
    code = asyncio.run(interp.execute(line))
    return code, out.getvalue(), err.getvalue(), interp


# --- expansion (unit) ----------------------------------------------------


def test_expand_simple_var():
    ctx = _ctx(FOO="bar")
    assert expand_token("$FOO", ctx) == "bar"


def test_expand_braced_var():
    ctx = _ctx(FOO="bar")
    assert expand_token("x${FOO}y", ctx) == "xbary"


def test_expand_undefined_is_empty():
    assert expand_token("$NOPE", _ctx()) == ""


def test_expand_status():
    assert expand_token("$?", _ctx(), status=3) == "3"


def test_expand_tilde():
    assert expand_token("~", _ctx()) == "/root"
    assert expand_token("~/x", _ctx()) == "/root/x"


def test_expand_lone_dollar_is_literal():
    assert expand_token("a$", _ctx()) == "a$"


# --- interpreter: basics -------------------------------------------------


def test_echo_roundtrip():
    code, out, err, _ = _exec("echo hello world")
    assert code == 0 and out == "hello world\n" and err == ""


def test_var_expansion_in_command():
    code, out, _, _ = _exec("echo $HOME")
    assert out == "/root\n"


def test_command_not_found():
    code, out, err, _ = _exec("definitely_not_here")
    assert code == 127
    assert err == "bash: definitely_not_here: command not found\n"
    assert out == ""


def test_syntax_error_reported():
    code, _, err, _ = _exec("ls &&")
    assert code == 2 and "syntax error" in err


def test_empty_line_keeps_status():
    interp, out, err = _sh()
    asyncio.run(interp.execute("false"))
    code = asyncio.run(interp.execute("   "))
    assert code == 1


def test_cd_persists_across_executes():
    interp, out, err = _sh()
    asyncio.run(interp.execute("cd /etc"))
    asyncio.run(interp.execute("pwd"))
    assert out.getvalue().strip().endswith("/etc")


def test_status_dollar_question():
    interp, out, err = _sh()
    asyncio.run(interp.execute("false"))
    asyncio.run(interp.execute("echo $?"))
    assert out.getvalue() == "1\n"


# --- job control ---------------------------------------------------------


def test_and_short_circuits_on_failure():
    code, out, _, _ = _exec("false && echo nope")
    assert out == "" and code == 1


def test_and_runs_on_success():
    code, out, _, _ = _exec("true && echo yes")
    assert out == "yes\n" and code == 0


def test_or_runs_on_failure():
    code, out, _, _ = _exec("false || echo recovered")
    assert out == "recovered\n" and code == 0


def test_semicolon_runs_both():
    code, out, _, _ = _exec("echo a ; echo b")
    assert out == "a\nb\n"


def test_chained_precedence():
    code, out, _, _ = _exec("true || echo b && echo c")
    assert out == "c\n"


# --- pipelines -----------------------------------------------------------


def test_simple_pipe():
    code, out, _, _ = _exec("echo piped | cat")
    assert out == "piped\n"


def test_pipe_from_fs():
    code, out, _, _ = _exec("cat /etc/hostname | cat")
    assert out == "svr04\n"


def test_pipe_status_is_last_stage():
    code, _, _, _ = _exec("echo x | false")
    assert code == 1


def test_undefined_var_word_removed():
    code, out, err, _ = _exec("cat $NOPE")
    assert code == 0 and out == "" and err == ""


# --- redirection ---------------------------------------------------------


def test_redirect_write_then_read():
    interp, out, err = _sh()
    asyncio.run(interp.execute("echo hi > /tmp/f"))
    asyncio.run(interp.execute("cat /tmp/f"))
    assert out.getvalue() == "hi\n"


def test_redirect_append():
    interp, out, err = _sh()
    asyncio.run(interp.execute("echo one > /tmp/f"))
    asyncio.run(interp.execute("echo two >> /tmp/f"))
    asyncio.run(interp.execute("cat /tmp/f"))
    assert out.getvalue() == "one\ntwo\n"


def test_redirect_input():
    code, out, _, _ = _exec("cat < /etc/hostname")
    assert out == "svr04\n"


def test_redirect_input_missing_file():
    code, _, err, _ = _exec("cat < /nope")
    assert code == 1 and "No such file or directory" in err


def test_redirect_write_does_not_print():
    code, out, _, interp = _exec("echo silent > /tmp/s")
    assert out == "" and interp.ctx.fs.readtext("/tmp/s") == "silent\n"


# --- realistic sequence --------------------------------------------------


def test_realistic_session():
    interp, out, err = _sh()
    asyncio.run(interp.execute("cd /tmp && echo 'data' > note && cat note"))
    assert out.getvalue() == "data\n"
    assert interp.ctx.cwd == "/tmp"
    assert err.getvalue() == ""


# --- standalone runner ---------------------------------------------------


def _run_standalone() -> int:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
        else:
            passed += 1
            print(f"ok   {fn.__name__}")
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
