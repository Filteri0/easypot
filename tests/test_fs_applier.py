"""fs_applier unit tests — structured C_i applied to the VirtualFS.

Covers the "C_i 回寫 VFS" milestone in isolation (no LLM): given a list of
fs_ops, does the VirtualFS end up in the right state, and does a bad op skip
silently without raising?

Dual-mode (HANDOFF §6):
    pytest tests/test_fs_applier.py
    python tests/test_fs_applier.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeyshell.backends.fs_applier import (  # noqa: E402
    apply_fs_ops,
    normalise_fs_ops,
)
from honeyshell.fs import VirtualFS  # noqa: E402


def _fs() -> VirtualFS:
    fs = VirtualFS()
    fs.makedirs("/tmp")
    fs.makedirs("/home/user")
    return fs


# --- normalise -----------------------------------------------------------

def test_normalise_coerces_shapes():
    assert normalise_fs_ops(None) == []
    assert normalise_fs_ops("bad") == []
    # single dict -> wrapped in a list
    assert normalise_fs_ops({"op": "touch", "path": "a"}) == [
        {"op": "touch", "path": "a"}
    ]
    # non-dict / missing "op" entries dropped
    mixed = [{"op": "mkdir", "path": "a"}, 42, {"no_op": 1}]
    assert normalise_fs_ops(mixed) == [{"op": "mkdir", "path": "a"}]


# --- happy path per op ---------------------------------------------------

def test_mkdir_creates_dir():
    fs = _fs()
    rep = apply_fs_ops(fs, "/root", [{"op": "mkdir", "path": "/tmp/newdir"}])
    assert fs.is_dir("/tmp/newdir")
    assert rep.changed and rep.impact == 1


def test_mkdir_is_idempotent():
    fs = _fs()
    rep = apply_fs_ops(fs, "/", [{"op": "mkdir", "path": "/tmp"}])  # exists
    # makedirs won't raise on an existing dir; still counts as applied.
    assert fs.is_dir("/tmp") and rep.changed


def test_touch_creates_empty_file_relative_to_cwd():
    fs = _fs()
    rep = apply_fs_ops(fs, "/home/user", [{"op": "touch", "path": "run.sh"}])
    assert fs.is_file("/home/user/run.sh")
    assert fs.readtext("/home/user/run.sh") == ""
    assert rep.impact == 1


def test_write_file_stores_content():
    fs = _fs()
    rep = apply_fs_ops(fs, "/root", [
        {"op": "write_file", "path": "/tmp/x.sh", "content": "#!/bin/sh\necho hi\n"},
    ])
    assert fs.readtext("/tmp/x.sh") == "#!/bin/sh\necho hi\n"
    assert rep.impact == 2  # a write modifies -> Table 1 = 2


def test_rm_removes_recursively():
    fs = _fs()
    fs.makedirs("/tmp/tree")
    fs.write_file("/tmp/tree/f", "data")
    rep = apply_fs_ops(fs, "/", [{"op": "rm", "path": "/tmp/tree"}])
    assert not fs.exists("/tmp/tree")
    assert rep.impact == 4  # delete -> top of the rubric


def test_mv_renames():
    fs = _fs()
    fs.write_file("/tmp/a", "hello")
    rep = apply_fs_ops(fs, "/", [{"op": "mv", "src": "/tmp/a", "dst": "/tmp/b"}])
    assert not fs.exists("/tmp/a") and fs.readtext("/tmp/b") == "hello"
    assert rep.impact == 2


def test_cp_copies_file():
    fs = _fs()
    fs.write_file("/tmp/a", "payload")
    rep = apply_fs_ops(fs, "/", [{"op": "cp", "src": "/tmp/a", "dst": "/tmp/copy"}])
    assert fs.readtext("/tmp/a") == "payload"
    assert fs.readtext("/tmp/copy") == "payload"
    assert rep.impact == 1


def test_impact_is_max_across_ops():
    fs = _fs()
    rep = apply_fs_ops(fs, "/", [
        {"op": "touch", "path": "/tmp/a"},          # 1
        {"op": "rm", "path": "/tmp/a"},             # 4
    ])
    assert rep.impact == 4  # highest wins, for pruner ranking


# --- resilience: bad ops skip silently, never raise ----------------------

def test_rm_missing_path_skips_without_raising():
    fs = _fs()
    rep = apply_fs_ops(fs, "/", [{"op": "rm", "path": "/tmp/does-not-exist"}])
    assert not rep.changed and rep.failed == 1  # skipped, no crash


def test_unknown_op_skipped():
    fs = _fs()
    rep = apply_fs_ops(fs, "/", [{"op": "chmod", "path": "/tmp"}])
    assert not rep.changed and rep.failed == 1


def test_missing_required_field_skipped():
    fs = _fs()
    rep = apply_fs_ops(fs, "/", [{"op": "mkdir"}])  # no path
    assert not rep.changed and rep.failed == 1


def test_cp_of_directory_is_skipped_not_partial():
    fs = _fs()
    fs.makedirs("/tmp/src")
    rep = apply_fs_ops(fs, "/", [{"op": "cp", "src": "/tmp/src", "dst": "/tmp/dst"}])
    assert not fs.exists("/tmp/dst") and not rep.changed


def test_good_ops_apply_even_when_one_fails():
    fs = _fs()
    rep = apply_fs_ops(fs, "/", [
        {"op": "mkdir", "path": "/tmp/good"},
        {"op": "rm", "path": "/tmp/missing"},   # fails
        {"op": "touch", "path": "/tmp/good/f"},
    ])
    assert fs.is_dir("/tmp/good") and fs.is_file("/tmp/good/f")
    assert len(rep.applied) == 2 and rep.failed == 1


def test_notes_render_applied_ops():
    fs = _fs()
    rep = apply_fs_ops(fs, "/", [{"op": "mkdir", "path": "/tmp/z"}])
    assert "/tmp/z" in rep.notes()


def _run_standalone():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")


if __name__ == "__main__":
    _run_standalone()
