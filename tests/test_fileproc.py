"""Tests for the file-processing builtins (batch 4).

sort, cut, sed  -> text processing over stdin/files (compose in pipelines)
find            -> walks the VFS tree
tar             -> extract materialises a believable tree in the VFS
dd              -> copies bytes into the VFS

Runnable two ways:
    python -m pytest tests/test_fileproc.py
    python tests/test_fileproc.py
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


def _run(name, tail, ctx=None, stdin=""):
    ctx = ctx or _ctx()
    cls = resolve(name)
    assert cls is not None, f"{name} not registered"
    out, err = StringWriter(), StringWriter()
    code = asyncio.run(cls(ctx, [name, *tail], StringReader(stdin), out,
                           err).run())
    return code, out.getvalue(), err.getvalue()


def _pipe(line, ctx=None):
    ctx = ctx or _ctx()
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute(line))
    return code, out.getvalue(), err.getvalue(), ctx


# --- sort ----------------------------------------------------------------


def test_sort_basic():
    _, out, _ = _run("sort", [], stdin="banana\napple\ncherry\n")
    assert out == "apple\nbanana\ncherry\n"


def test_sort_reverse():
    _, out, _ = _run("sort", ["-r"], stdin="a\nb\nc\n")
    assert out == "c\nb\na\n"


def test_sort_numeric():
    _, out, _ = _run("sort", ["-n"], stdin="10\n2\n1\n30\n")
    assert out == "1\n2\n10\n30\n"


def test_sort_unique():
    _, out, _ = _run("sort", ["-u"], stdin="b\na\na\nb\n")
    assert out == "a\nb\n"


# --- cut -----------------------------------------------------------------


def test_cut_field_delimited():
    ctx = _ctx()
    _, out, _, _ = _pipe("cat /etc/passwd | cut -d: -f1", ctx)
    assert "root" in out and ":" not in out


def test_cut_multiple_fields():
    _, out, _ = _run("cut", ["-d,", "-f1,3"], stdin="a,b,c,d\n")
    assert out == "a,c\n"


def test_cut_char_range():
    _, out, _ = _run("cut", ["-c1-3"], stdin="abcdef\n")
    assert out == "abc\n"


def test_cut_field_range_open():
    _, out, _ = _run("cut", ["-d:", "-f2-"], stdin="a:b:c:d\n")
    assert out == "b:c:d\n"


# --- sed -----------------------------------------------------------------


def test_sed_substitute_first():
    _, out, _ = _run("sed", ["s/a/X/"], stdin="aaa\n")
    assert out == "Xaa\n"


def test_sed_substitute_global():
    _, out, _ = _run("sed", ["s/a/X/g"], stdin="aaa\n")
    assert out == "XXX\n"


def test_sed_alternate_delimiter():
    _, out, _ = _run("sed", ["s|/usr|/opt|"], stdin="/usr/bin\n")
    assert out == "/opt/bin\n"


def test_sed_unsupported_script_passthrough():
    # A non-substitution script must not error; it passes input through.
    _, out, _ = _run("sed", ["1d"], stdin="keep\n")
    assert out == "keep\n"


def test_sed_in_pipeline():
    _, out, _, _ = _pipe("echo hello world | sed s/world/there/")
    assert out == "hello there\n"


# --- find ----------------------------------------------------------------


def test_find_by_name():
    _, out, _, _ = _pipe("find /etc -name passwd", _ctx(cwd="/"))
    assert "/etc/passwd" in out


def test_find_type_dir_maxdepth():
    _, out, _, _ = _pipe("find / -type d -maxdepth 1", _ctx(cwd="/"))
    assert "/etc" in out and "/tmp" in out
    # a file at depth 1 should not appear under -type d
    assert "/etc/passwd" not in out


def test_find_missing_start_errors():
    code, out, err = _run("find", ["/no/such"], _ctx(cwd="/"))
    assert code != 0 and "No such file" in err


# --- tar -----------------------------------------------------------------


def test_tar_extract_materialises_tree():
    ctx = _ctx()
    _, out, _ = _run("tar", ["-xzf", "payload.tar.gz"], ctx)
    assert ctx.fs.exists("/tmp/package/install.sh")


def test_tar_extract_verbose_lists():
    ctx = _ctx()
    _, out, _ = _run("tar", ["-xzvf", "p.tar.gz"], ctx)
    assert "package/install.sh" in out


def test_tar_create_writes_archive():
    ctx = _ctx()
    ctx.fs.write_file("/tmp/a", b"x", "/tmp")
    _, out, _ = _run("tar", ["-czf", "out.tar", "a"], ctx)
    assert ctx.fs.exists("/tmp/out.tar")


def test_tar_list():
    _, out, _ = _run("tar", ["-tzf", "x.tar.gz"], _ctx())
    assert "package/" in out


# --- dd ------------------------------------------------------------------


def test_dd_writes_vfs_from_zero():
    ctx = _ctx()
    _, out, err = _run("dd", ["if=/dev/zero", "of=/tmp/block", "bs=1k",
                              "count=2"], ctx)
    assert ctx.fs.exists("/tmp/block")
    assert "records out" in err


def test_dd_copies_file():
    ctx = _ctx()
    ctx.fs.write_file("/tmp/src", b"payload", "/tmp")
    _, out, err = _run("dd", ["if=/tmp/src", "of=/tmp/dst"], ctx)
    assert ctx.fs.readtext("/tmp/dst") == "payload"


def test_dd_missing_input_errors():
    code, out, err = _run("dd", ["if=/tmp/nope", "of=/tmp/x"], _ctx())
    assert code != 0 and "No such file" in err


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
