"""Tests for command substitution — $(...) and backticks — plus mktemp.

Command substitution is a pre-parse pass (bash evaluates it before word
splitting), so these run through a real Interpreter. The headline case is
``cd $(mktemp -d)`` landing in a directory that actually exists.

Runnable two ways:
    python -m pytest tests/test_cmdsubst.py
    python tests/test_cmdsubst.py
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
from honeyshell.shell.interpreter import Interpreter  # noqa: E402
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402

discover()


def _ctx(cwd="/tmp"):
    return ShellContext(fs=build_sample_fs(hostname="svr04"), cwd=cwd,
                        username="root")


def _run(line, ctx=None):
    ctx = ctx or _ctx()
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute(line))
    return code, out.getvalue(), err.getvalue(), ctx


# --- $(...) --------------------------------------------------------------


def test_simple_substitution():
    _, out, _, _ = _run("echo $(whoami)")
    assert out == "root\n"


def test_substitution_in_assignment():
    ctx = _ctx()
    _run("VERSION=$(uname -r)", ctx)
    _, out, _, _ = _run("echo $VERSION", ctx)
    assert out.strip() != "" and "unknown" not in out


def test_nested_substitution():
    _, out, _, _ = _run("echo $(echo $(whoami))")
    assert out == "root\n"


def test_substitution_splits_into_args():
    # $(...) output undergoes word-splitting: two words -> two echo args.
    ctx = _ctx()
    ctx.fs.write_file("/tmp/two.txt", b"alpha beta\n", "/tmp")
    _, out, _, _ = _run("echo $(cat /tmp/two.txt)", ctx)
    assert out == "alpha beta\n"


# --- backticks -----------------------------------------------------------


def test_backtick_substitution():
    _, out, _, _ = _run("echo `whoami`")
    assert out == "root\n"


# --- mktemp + the headline case ------------------------------------------


def test_mktemp_file_creates_vfs_node():
    ctx = _ctx()
    code, out, err, _ = _run("mktemp", ctx)
    path = out.strip()
    assert path.startswith("/tmp/") and ctx.fs.exists(path)


def test_mktemp_d_creates_directory():
    ctx = _ctx()
    _, out, _, _ = _run("mktemp -d", ctx)
    path = out.strip()
    assert ctx.fs.exists(path) and ctx.fs.stat(path).is_dir


def test_cd_into_mktemp_d():
    # The reported failure: cd $(mktemp -d) landed on a literal '$(mktemp'.
    ctx = _ctx(cwd="/root")
    _, out, err, _ = _run("cd $(mktemp -d)", ctx)
    assert err == ""
    assert ctx.cwd.startswith("/tmp/")
    assert ctx.fs.exists(ctx.cwd)  # cwd is a real directory


def test_no_substitution_line_unaffected():
    # A plain line without $( or ` must pass straight through unchanged.
    _, out, _, _ = _run("echo hello world")
    assert out == "hello world\n"


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
