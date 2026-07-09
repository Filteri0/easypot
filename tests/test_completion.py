"""Tab-completion unit tests — pure logic, no asyncssh.

Run:
    python -m pytest tests/test_completion.py
    python tests/test_completion.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.fs import VirtualFS  # noqa: E402
from honeyshell.transport import completion  # noqa: E402

CMDS = ["cat", "cd", "chmod", "echo", "ls", "pwd", "whoami"]


def _fs() -> VirtualFS:
    fs = VirtualFS()
    fs.makedirs("/etc")
    fs.makedirs("/home/user")
    fs.write_file("/etc/passwd", "root:x:0:0")
    fs.write_file("/etc/pam.conf", "")
    fs.makedirs("/etc/ssh")
    return fs


# --- command completion --------------------------------------------------

def test_unique_command_completes_with_space():
    line, pos = completion.complete("who", 3, command_names=CMDS)
    assert (line, pos) == ("whoami ", 7)


def test_ambiguous_command_extends_common_prefix():
    # "c" -> cat/cd/chmod share nothing past "c"; unchanged + bell.
    line, pos = completion.complete("c", 1, command_names=CMDS)
    assert line == "c"
    # "ch" -> only chmod -> completes
    line, pos = completion.complete("ch", 2, command_names=CMDS)
    assert (line, pos) == ("chmod ", 6)


def test_common_prefix_growth():
    # both "cat" and "cd" start with "c"; "ca" -> only cat
    line, _ = completion.complete("ca", 2, command_names=CMDS)
    assert line == "cat "


def test_no_command_match_unchanged():
    line, pos = completion.complete("zzz", 3, command_names=CMDS)
    assert (line, pos) == ("zzz", 3)


# --- path completion -----------------------------------------------------

def test_path_unique_file_gets_space():
    fs = _fs()
    line, pos = completion.complete(
        "cat /etc/pas", 12, command_names=CMDS, fs=fs, cwd="/"
    )
    assert line == "cat /etc/passwd "


def test_path_unique_dir_gets_slash():
    fs = _fs()
    line, _ = completion.complete(
        "ls /ho", 6, command_names=CMDS, fs=fs, cwd="/"
    )
    assert line == "ls /home/"


def test_path_ambiguous_no_growth_unchanged():
    fs = _fs()
    # /etc/passwd and /etc/pam.conf share prefix "pa" (== token) -> no growth,
    # line left unchanged for the user to disambiguate.
    line, pos = completion.complete(
        "cat /etc/pa", 11, command_names=CMDS, fs=fs, cwd="/"
    )
    assert (line, pos) == ("cat /etc/pa", 11)


def test_path_relative_to_cwd():
    fs = _fs()
    line, _ = completion.complete(
        "cat pass", 8, command_names=CMDS, fs=fs, cwd="/etc"
    )
    assert line == "cat passwd "


def test_path_no_fs_leaves_unchanged():
    line, pos = completion.complete("cat /etc/pa", 11, command_names=CMDS)
    assert (line, pos) == ("cat /etc/pa", 11)


def test_bad_dir_no_completion():
    fs = _fs()
    line, pos = completion.complete(
        "cat /nope/x", 11, command_names=CMDS, fs=fs, cwd="/"
    )
    assert (line, pos) == ("cat /nope/x", 11)


def test_completion_preserves_text_after_cursor():
    # cursor in the middle: complete the command, keep the trailing arg
    line, pos = completion.complete("who arg", 3, command_names=CMDS)
    assert line == "whoami  arg"  # "whoami " + " arg"
    assert pos == 7


def test_common_prefix_helper():
    assert completion.common_prefix(["abcd", "abce"]) == "abc"
    assert completion.common_prefix([]) == ""


def _run_standalone():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")


if __name__ == "__main__":
    _run_standalone()
