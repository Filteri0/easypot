"""Tests for the download builtins: wget, curl, tftp, ftpget.

The theme of this batch is the C_i-write-back guarantee: a simulated download
must actually mutate the VirtualFS, so a subsequent ``cat`` reads the file back.
We also pin URL normalisation, output-filename derivation, stdout vs save
behaviour (curl vs wget), and the missing-directory error path.

Runnable two ways:
    python -m pytest tests/test_downloads.py
    python tests/test_downloads.py
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
    resolve,
)
from honeyshell.commands import discover  # noqa: E402
from honeyshell.commands.impl._download import (  # noqa: E402
    normalize_url,
    outfile_from_url,
    placeholder_contents,
)
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402

discover()


def _ctx(cwd: str = "/root") -> ShellContext:
    return ShellContext(fs=build_sample_fs(hostname="svr04"), cwd=cwd,
                        username="root")


def _run(name, argv_tail, ctx=None, stdin_text=""):
    """Resolve ``name``, run with argv = [name, *tail]; return (code, out, err, ctx)."""
    ctx = ctx or _ctx()
    cls = resolve(name)
    assert cls is not None, f"{name} not registered"
    out, err = StringWriter(), StringWriter()
    cmd = cls(ctx, [name, *argv_tail], StringReader(stdin_text), out, err)
    code = asyncio.run(cmd.run())
    return code, out.getvalue(), err.getvalue(), ctx


# --- helper units --------------------------------------------------------


def test_normalize_url_prefixes_scheme():
    u = normalize_url("example.com/a/b.sh")
    assert u is not None
    assert u.scheme == "http" and u.host == "example.com" and u.port == 80
    assert u.path == "/a/b.sh"
    assert u.raw == "http://example.com/a/b.sh"


def test_normalize_url_keeps_explicit_scheme_and_port():
    u = normalize_url("https://h.test:8443/x")
    assert u is not None
    assert u.scheme == "https" and u.port == 8443


def test_normalize_url_rejects_hostless():
    assert normalize_url("http:///nohost") is None


def test_outfile_from_url():
    assert outfile_from_url("/dir/payload.sh") == "payload.sh"
    assert outfile_from_url("/") == "index.html"
    assert outfile_from_url("") == "index.html"
    assert outfile_from_url("bare") == "index.html"  # no slash -> index.html


def test_placeholder_mentions_url():
    data = placeholder_contents("http://h/x")
    assert b"http://h/x" in data


# --- wget ----------------------------------------------------------------


def test_wget_saves_into_vfs_and_cat_reads_back():
    code, out, err, ctx = _run("wget", ["http://1.2.3.4/x.sh", "-O", "/tmp/x.sh"])
    assert code == 0
    # C_i write-back: the file really exists in the VFS now.
    assert ctx.fs.exists("/tmp/x.sh")
    body = ctx.fs.readtext("/tmp/x.sh")
    assert "downloaded from http://1.2.3.4/x.sh" in body
    # Progress output goes to stderr, not stdout.
    assert "Saving to: '/tmp/x.sh'" in err
    assert "saved" in err
    assert out == ""


def test_wget_default_outfile_from_url():
    ctx = _ctx(cwd="/tmp")
    code, out, err, ctx = _run("wget", ["http://h/dir/evil.bin"], ctx=ctx)
    assert code == 0
    assert ctx.fs.exists("/tmp/evil.bin")


def test_wget_index_html_when_no_path():
    ctx = _ctx(cwd="/tmp")
    code, out, err, ctx = _run("wget", ["http://h"], ctx=ctx)
    assert code == 0
    assert ctx.fs.exists("/tmp/index.html")


def test_wget_dash_O_streams_to_stdout():
    code, out, err, ctx = _run("wget", ["http://h/p", "-O", "-"])
    assert code == 0
    assert "downloaded from http://h/p" in out  # body on stdout
    assert not ctx.fs.exists("/p")  # nothing saved


def test_wget_quiet_suppresses_progress():
    code, out, err, ctx = _run("wget", ["-q", "http://h/p", "-O", "/tmp/p"])
    assert code == 0
    assert err == ""
    assert ctx.fs.exists("/tmp/p")


def test_wget_missing_directory_errors():
    code, out, err, ctx = _run("wget", ["http://h/p", "-O", "/nope/here/p"])
    assert code == 1
    assert "Cannot open: No such file or directory" in err
    assert not ctx.fs.exists("/nope/here/p")


def test_wget_no_url_usage_error():
    code, out, err, ctx = _run("wget", [])
    assert code == 1
    assert "missing URL" in err


# --- curl ----------------------------------------------------------------


def test_curl_defaults_to_stdout():
    code, out, err, ctx = _run("curl", ["http://h/script.sh"])
    assert code == 0
    assert "downloaded from http://h/script.sh" in out
    # Nothing written to the VFS on the default path.
    assert not ctx.fs.exists("/root/script.sh")


def test_curl_dash_o_saves_to_vfs():
    code, out, err, ctx = _run("curl", ["-o", "/tmp/y", "http://h/y"])
    assert code == 0
    assert ctx.fs.exists("/tmp/y")
    assert out == ""


def test_curl_dash_O_uses_url_basename():
    ctx = _ctx(cwd="/tmp")
    code, out, err, ctx = _run("curl", ["-O", "http://h/a/thing.sh"], ctx=ctx)
    assert code == 0
    assert ctx.fs.exists("/tmp/thing.sh")


def test_curl_silent_missing_dir():
    code, out, err, ctx = _run("curl", ["-s", "-o", "/nope/z", "http://h/z"])
    assert code == 23
    assert err == ""  # -s silences the warning


# --- tftp ----------------------------------------------------------------


def test_tftp_get_r_saves_to_vfs():
    ctx = _ctx(cwd="/tmp")
    code, out, err, ctx = _run("tftp", ["-g", "-r", "mal.bin", "10.0.0.1"], ctx=ctx)
    assert code == 0
    assert ctx.fs.exists("/tmp/mal.bin")


def test_tftp_c_get_saves_to_vfs():
    ctx = _ctx(cwd="/tmp")
    code, out, err, ctx = _run("tftp", ["-c", "get", "f.sh", "10.0.0.1"], ctx=ctx)
    assert code == 0
    assert ctx.fs.exists("/tmp/f.sh")


def test_tftp_missing_args_usage():
    code, out, err, ctx = _run("tftp", ["-g", "10.0.0.1"])  # no -r
    assert code == 1
    assert "usage: tftp" in err


# --- ftpget --------------------------------------------------------------


def test_ftpget_two_positionals_local_from_remote():
    ctx = _ctx(cwd="/tmp")
    code, out, err, ctx = _run("ftpget", ["host", "get/me.sh"], ctx=ctx)
    assert code == 0
    assert ctx.fs.exists("/tmp/me.sh")


def test_ftpget_three_positionals_explicit_local():
    ctx = _ctx(cwd="/tmp")
    code, out, err, ctx = _run("ftpget", ["host", "local.sh", "remote.sh"], ctx=ctx)
    assert code == 0
    assert ctx.fs.exists("/tmp/local.sh")


def test_ftpget_skips_credential_flags():
    ctx = _ctx(cwd="/tmp")
    code, out, err, ctx = _run(
        "ftpget", ["-u", "user", "-p", "pass", "host", "r.sh"], ctx=ctx
    )
    assert code == 0
    assert ctx.fs.exists("/tmp/r.sh")


def test_ftpget_missing_args_usage():
    code, out, err, ctx = _run("ftpget", ["onlyhost"])
    assert code == 1
    assert "Usage: ftpget" in err


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
