"""Tests for LLM-backed download content (curl/wget stdout path).

Covers the scenario split agreed with the user:
  * stdout path (curl URL / wget -O -) uses ctx.fetch_content when wired;
  * save path (curl -o / wget -O file) always uses the placeholder;
  * when the fetcher returns None (no model), stdout falls back to placeholder;
  * ContentFetcher caches per URL (option A: same URL -> same body).

No real Ollama: a FakeClient/FakeFetcher stands in, mirroring how the memory
tests use a FakeLLM.

Runnable two ways:
    python -m pytest tests/test_download_content.py
    python tests/test_download_content.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.backends.client import LLMResult, LLMUnavailable  # noqa: E402
from honeyshell.backends.content_fetcher import ContentFetcher  # noqa: E402
from honeyshell.commands import (  # noqa: E402
    ShellContext,
    StringReader,
    StringWriter,
    discover,
    resolve,
)
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402

discover()


def _ctx(cwd="/tmp", fetch_content=None):
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd=cwd,
                       username="root")
    ctx.fetch_content = fetch_content
    return ctx


def _run(name, tail, ctx):
    cls = resolve(name)
    out, err = StringWriter(), StringWriter()
    cmd = cls(ctx, [name, *tail], StringReader(""), out, err)
    code = asyncio.run(cmd.run())
    return code, out.getvalue(), err.getvalue()


# --- a fake fetcher ------------------------------------------------------


def make_fetcher(body: str):
    async def fetch(url: str):
        return f"{body} for {url}".encode()
    return fetch


async def _none_fetcher(url: str):
    return None


# --- curl stdout uses the fetcher ----------------------------------------


def test_curl_stdout_uses_fetcher_when_wired():
    ctx = _ctx(fetch_content=make_fetcher("SCRIPT"))
    code, out, err = _run("curl", ["http://h/install.sh"], ctx)
    assert code == 0
    assert "SCRIPT for http://h/install.sh" in out
    assert "# downloaded from" not in out  # not the placeholder


def test_curl_stdout_appends_trailing_newline():
    # Models often omit the trailing newline, which would glue the next prompt
    # onto the body. content_for_stdout normalises it.
    async def no_nl(url):
        return b"exit 0"  # no trailing newline
    ctx = _ctx(fetch_content=no_nl)
    code, out, err = _run("curl", ["http://h/x"], ctx)
    assert out.endswith("\n")


def test_curl_stdout_falls_back_to_placeholder_without_fetcher():
    ctx = _ctx(fetch_content=None)
    code, out, err = _run("curl", ["http://h/x"], ctx)
    assert "# downloaded from http://h/x" in out


def test_curl_stdout_falls_back_when_fetcher_returns_none():
    ctx = _ctx(fetch_content=_none_fetcher)
    code, out, err = _run("curl", ["http://h/x"], ctx)
    assert "# downloaded from http://h/x" in out


# --- curl save path keeps placeholder ------------------------------------


def test_curl_save_path_ignores_fetcher():
    ctx = _ctx(fetch_content=make_fetcher("SCRIPT"))
    code, out, err = _run("curl", ["-o", "/tmp/y", "http://h/y"], ctx)
    assert code == 0
    # File content is the placeholder, not the fetched body.
    body = ctx.fs.readtext("/tmp/y")
    assert body.startswith("# downloaded from")
    assert "SCRIPT" not in body


# --- wget -O - uses the fetcher; wget save keeps placeholder --------------


def test_wget_dash_O_dash_uses_fetcher():
    ctx = _ctx(fetch_content=make_fetcher("BODY"))
    code, out, err = _run("wget", ["http://h/p", "-O", "-"], ctx)
    assert code == 0
    assert "BODY for http://h/p" in out


def test_wget_save_keeps_placeholder():
    ctx = _ctx(cwd="/tmp", fetch_content=make_fetcher("BODY"))
    code, out, err = _run("wget", ["http://h/p.bin"], ctx)
    assert code == 0
    body = ctx.fs.readtext("/tmp/p.bin")
    assert body.startswith("# downloaded from")


# --- curl | sh with a fetched script actually executes -------------------


def test_curl_pipe_sh_runs_fetched_script():
    from honeyshell.shell.interpreter import Interpreter

    async def fetch(url: str):
        return b"id\n"  # a real command, not a comment

    ctx = _ctx(fetch_content=fetch)
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    # ctx.fetch_content survives; interpreter wires run_line for sh.
    code = asyncio.run(interp.execute("curl http://h/i.sh | sh"))
    assert "uid=0(root)" in out.getvalue()


# --- ContentFetcher unit: cache + resilience -----------------------------


class _FakeClient:
    def __init__(self, body="hello", fail=False):
        self.body = body
        self.fail = fail
        self.calls = 0

    async def chat(self, messages):
        self.calls += 1
        if self.fail:
            raise LLMUnavailable("down")
        return LLMResult(content=self.body, model="fake")


def test_fetcher_caches_same_url():
    client = _FakeClient(body="print('x')")
    f = ContentFetcher(client=client)
    a = asyncio.run(f("http://h/a"))
    b = asyncio.run(f("http://h/a"))
    assert a == b
    assert client.calls == 1  # second call served from cache


def test_fetcher_strips_code_fences():
    client = _FakeClient(body="```sh\necho hi\n```")
    f = ContentFetcher(client=client)
    data = asyncio.run(f("http://h/s.sh"))
    assert data == b"echo hi"


def test_fetcher_returns_none_on_model_error():
    client = _FakeClient(fail=True)
    f = ContentFetcher(client=client)
    assert asyncio.run(f("http://h/x")) is None


def test_fetcher_returns_none_on_empty_body():
    client = _FakeClient(body="   ")
    f = ContentFetcher(client=client)
    assert asyncio.run(f("http://h/x")) is None


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
