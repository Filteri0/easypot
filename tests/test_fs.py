"""Tests for honeyshell.fs (filesystem, loader, import_cowrie).

Runnable two ways:
    python -m pytest tests/test_fs.py
    python tests/test_fs.py
"""

from __future__ import annotations

import pickle
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.fs import (  # noqa: E402
    DIR,
    FILE,
    LINK,
    DirectoryNotEmpty,
    FileExists,
    IsADirectory,
    NoSuchFile,
    NotADirectory,
    VirtualFS,
    load_dict,
    load_json,
    save_json,
    to_dict,
)
from honeyshell.fs.filesystem import FSNode  # noqa: E402
from honeyshell.fs.import_cowrie import convert_pickle  # noqa: E402
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402


def _sample_fs() -> VirtualFS:
    # Build the fixture in-memory with a fixed hostname so tests never depend
    # on whatever data/fs.json a deployment may have regenerated (e.g. with a
    # custom --hostname). The on-disk fs.json is a deployment artifact.
    return build_sample_fs(hostname="svr04")


# --- path normalisation --------------------------------------------------


def test_normalize_absolute():
    fs = _sample_fs()
    assert fs.normalize("/etc/../etc/passwd") == "/etc/passwd"


def test_normalize_relative_to_cwd():
    fs = _sample_fs()
    assert fs.normalize("passwd", "/etc") == "/etc/passwd"


def test_normalize_dotdot_past_root():
    fs = _sample_fs()
    assert fs.normalize("../../..", "/etc") == "/"


# --- queries -------------------------------------------------------------


def test_exists_and_types():
    fs = _sample_fs()
    assert fs.exists("/etc/passwd")
    assert fs.is_file("/etc/passwd")
    assert fs.is_dir("/etc")
    assert not fs.exists("/etc/shadow")


def test_listdir_sorted():
    fs = _sample_fs()
    assert fs.listdir("/etc") == ["hostname", "os-release", "passwd"]


def test_listdir_on_file_errors():
    fs = _sample_fs()
    try:
        fs.listdir("/etc/passwd")
    except NotADirectory:
        return
    raise AssertionError("expected NotADirectory")


def test_read_file_contents():
    fs = _sample_fs()
    txt = fs.readtext("/etc/hostname")
    assert txt == "svr04\n"


def test_read_dir_errors():
    fs = _sample_fs()
    try:
        fs.readbytes("/etc")
    except IsADirectory:
        return
    raise AssertionError("expected IsADirectory")


def test_missing_path_errors():
    fs = _sample_fs()
    try:
        fs.readbytes("/nope")
    except NoSuchFile:
        return
    raise AssertionError("expected NoSuchFile")


def test_stat_fields():
    fs = _sample_fs()
    st = fs.stat("/root")
    assert st.is_dir and st.perm == 0o700 and st.size == 4096
    stf = fs.stat("/bin/ls")
    assert stf.is_file and stf.perm == 0o755 and stf.size == 133792


# --- symlinks ------------------------------------------------------------


def test_symlink_followed_in_path():
    fs = _sample_fs()
    # /sbin -> /bin, so /sbin/ls resolves to /bin/ls
    assert fs.is_file("/sbin/ls")
    assert fs.readbytes("/sbin/ls") == b""  # metadata-only file


def test_lstat_does_not_follow():
    fs = _sample_fs()
    st = fs.stat("/sbin", follow=False)
    assert st.is_link and st.target == "/bin"


def test_symlink_loop_guarded():
    fs = VirtualFS()
    fs.symlink("/a", "/b")
    fs.symlink("/b", "/a")
    try:
        fs.readbytes("/a")
    except Exception as e:  # SymlinkLoop is an FSError
        assert "symbolic links" in str(e).lower() or "No such" in str(e)
        return
    raise AssertionError("expected a symlink loop / resolution error")


# --- mutations -----------------------------------------------------------


def test_mkdir_and_write_and_read():
    fs = _sample_fs()
    fs.mkdir("/tmp/work")
    assert fs.is_dir("/tmp/work")
    fs.write_file("/tmp/work/a.txt", "hello\n")
    assert fs.readtext("/tmp/work/a.txt") == "hello\n"
    assert fs.stat("/tmp/work/a.txt").size == 6


def test_mkdir_existing_errors():
    fs = _sample_fs()
    try:
        fs.mkdir("/etc")
    except FileExists:
        return
    raise AssertionError("expected FileExists")


def test_makedirs_nested():
    fs = _sample_fs()
    fs.makedirs("/var/lib/app/data")
    assert fs.is_dir("/var/lib/app/data")


def test_remove_file():
    fs = _sample_fs()
    fs.write_file("/tmp/x", "y")
    fs.remove("/tmp/x")
    assert not fs.exists("/tmp/x")


def test_remove_nonempty_dir_requires_recursive():
    fs = _sample_fs()
    fs.makedirs("/tmp/d/e")
    try:
        fs.remove("/tmp/d")
    except DirectoryNotEmpty:
        pass
    else:
        raise AssertionError("expected DirectoryNotEmpty")
    fs.remove("/tmp/d", recursive=True)
    assert not fs.exists("/tmp/d")


def test_move_rename():
    fs = _sample_fs()
    fs.write_file("/tmp/a", "1")
    fs.move("/tmp/a", "/tmp/b")
    assert not fs.exists("/tmp/a") and fs.readtext("/tmp/b") == "1"


def test_move_into_directory():
    fs = _sample_fs()
    fs.write_file("/tmp/a", "1")
    fs.mkdir("/tmp/dst")
    fs.move("/tmp/a", "/tmp/dst")
    assert fs.readtext("/tmp/dst/a") == "1"


def test_mutations_are_session_local():
    # two independently loaded trees must not share state
    fs1 = _sample_fs()
    fs2 = _sample_fs()
    fs1.write_file("/tmp/only1", "x")
    assert fs1.exists("/tmp/only1")
    assert not fs2.exists("/tmp/only1")


# --- loader round-trip ---------------------------------------------------


def test_json_roundtrip_preserves_tree():
    fs = _sample_fs()
    d = to_dict(fs)
    fs2 = load_dict(d)
    assert fs2.readtext("/etc/passwd").startswith("root:x:0:0")
    assert fs2.listdir("/") == fs.listdir("/")
    assert fs2.stat("/sbin", follow=False).target == "/bin"


def test_save_and_reload(tmp_path=None):
    fs = _sample_fs()
    fs.write_file("/tmp/note.txt", "persisted\n")
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "fs.json"
        save_json(fs, out)
        fs2 = load_json(out)
        assert fs2.readtext("/tmp/note.txt") == "persisted\n"


def test_binary_contents_roundtrip():
    root = FSNode("/", DIR)
    fs = VirtualFS(root)
    fs.write_file("/blob", bytes([0, 1, 2, 255, 254]))
    d = to_dict(fs)
    # non-utf8 must serialise as base64
    blob = [c for c in d["children"] if c["name"] == "blob"][0]
    assert "contents_b64" in blob
    fs2 = load_dict(d)
    assert fs2.readbytes("/blob") == bytes([0, 1, 2, 255, 254])


# --- Cowrie pickle converter (synthetic, format-faithful) ----------------


def _make_cowrie_pickle(path: Path) -> None:
    # inode layout: [name, type, uid, gid, size, mode, ctime, contents, target]
    passwd = ["passwd", 2, 0, 0, 32, 0o100644, 0, b"root:x:0:0::/root:/bin/sh\n"]
    empty = ["ls", 2, 0, 0, 1000, 0o100755, 0, None]
    link = ["rc.local", 0, 0, 0, 0, 0o120777, 0, None, "/etc/init.d/rc.local"]
    etc = ["etc", 1, 0, 0, 4096, 0o40755, 0, [passwd, link]]
    bind = ["bin", 1, 0, 0, 4096, 0o40755, 0, [empty]]
    root = ["/", 1, 0, 0, 4096, 0o40755, 0, [etc, bind]]
    with open(path, "wb") as fh:
        pickle.dump(root, fh)


def test_convert_pickle_structural_inference():
    with tempfile.TemporaryDirectory() as d:
        pk = Path(d) / "fs.pickle"
        _make_cowrie_pickle(pk)
        tree = convert_pickle(str(pk))
        fs = load_dict(tree)

        assert fs.is_dir("/etc") and fs.is_dir("/bin")
        # file with embedded bytes -> readable text
        assert fs.readtext("/etc/passwd").startswith("root:x:0:0")
        # metadata-only file -> lists but empty, correct size preserved
        assert fs.is_file("/bin/ls") and fs.stat("/bin/ls").size == 1000
        # symlink detected via index-8 target, not via type enum
        st = fs.stat("/etc/rc.local", follow=False)
        assert st.is_link and st.target == "/etc/init.d/rc.local"
        # perm stripped to lower 12 bits
        assert fs.stat("/etc/passwd").perm == 0o644


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
