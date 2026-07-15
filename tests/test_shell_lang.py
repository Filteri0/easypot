"""Tests for the stage-A shell-language handling (assignments / no-op builtins /
control keywords) that keeps piped scripts from spewing errors.

Driven through a real Interpreter, since that's where the handling lives. The
headline case is a multi-line installer piped into sh producing clean output.

Runnable two ways:
    python -m pytest tests/test_shell_lang.py
    python tests/test_shell_lang.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.commands import ShellContext, StringWriter, discover  # noqa: E402
from honeyshell.shell.interpreter import Interpreter  # noqa: E402
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402

discover()


def _run(line, ctx=None):
    ctx = ctx or ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/tmp",
                              username="root")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute(line))
    return code, out.getvalue(), err.getvalue(), ctx


# --- assignment + expansion ----------------------------------------------


def test_assignment_then_expansion_same_ctx():
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/tmp",
                       username="root")
    _run("FOO=bar", ctx)
    _, out, _, _ = _run("echo $FOO", ctx)
    assert out == "bar\n"


def test_assignment_value_is_expanded():
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/tmp",
                       username="root")
    _run("A=hello", ctx)
    _run("B=$A", ctx)
    _, out, _, _ = _run("echo $B", ctx)
    assert out == "hello\n"


def test_assignment_makes_quoted_var_usable():
    # The reported failure: DIR set, then mkdir -p "$DIR" must get an operand.
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/tmp",
                       username="root")
    _run("DIR=/opt/app", ctx)
    _, out, err, _ = _run('mkdir -p "$DIR"', ctx)
    assert err == ""
    assert ctx.fs.exists("/opt/app")


def test_leading_assignment_then_command():
    code, out, err, _ = _run("A=1 B=2 echo hi")
    assert out == "hi\n" and err == ""


def test_temp_env_visible_to_command():
    _, out, _, _ = _run('MSG=hello sh -c "echo $MSG"')
    assert out == "hello\n"


# --- no-op builtins ------------------------------------------------------


def test_set_e_is_silent_success():
    code, out, err, _ = _run("set -e")
    assert code == 0 and out == "" and err == ""


def test_export_sets_environ():
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/tmp",
                       username="root")
    _run("export PATH=/custom/bin", ctx)
    assert ctx.environ.get("PATH") == "/custom/bin"


def test_unset_removes_environ():
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/tmp",
                       username="root")
    _run("X=1", ctx)
    _run("unset X", ctx)
    _, out, _, _ = _run("echo $X", ctx)
    assert out == "\n"  # unset -> empty


def test_colon_builtin_is_noop():
    code, out, err, _ = _run(": anything goes here")
    assert code == 0 and err == ""


def test_umask_shopt_silent():
    for line in ("umask 022", "shopt -s nullglob"):
        code, out, err, _ = _run(line)
        assert err == "", line


# --- control keywords ----------------------------------------------------


def test_control_keywords_are_swallowed():
    for line in ("if [ -d /tmp ]; then", "fi", "for i in a b; do", "done",
                 "while true; do", "case $x in", "esac", "else"):
        code, out, err, _ = _run(line)
        assert "command not found" not in err, line


# --- the headline: a piped installer stays clean -------------------------


def test_piped_installer_no_error_noise():
    script = "\n".join([
        "#!/bin/sh",
        "set -e",
        "INSTALL_DIR=/opt/brave",
        'mkdir -p "$INSTALL_DIR"',
        'if [ -d "$INSTALL_DIR" ]; then',
        '    echo "created $INSTALL_DIR"',
        "fi",
        "for f in a b c; do",
        '    echo "$f"',
        "done",
        "export PATH=/usr/bin",
        "echo done",
    ])

    async def fetch(url):
        return script.encode()

    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/root",
                       username="root")
    ctx.fetch_content = fetch
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    asyncio.run(interp.execute("curl http://x/install.sh | sh"))
    out_s, err_s = out.getvalue(), err.getvalue()

    # No command-not-found / syntax noise.
    assert "command not found" not in err_s
    assert "syntax error" not in err_s
    # Real work happened: dir created, echoes ran.
    assert ctx.fs.exists("/opt/brave")
    assert "created /opt/brave" in out_s
    assert "done" in out_s


# --- standalone runner ---------------------------------------------------


def _run_standalone() -> int:
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
