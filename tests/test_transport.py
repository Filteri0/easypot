"""Unit tests for the transport session loop and terminal writer.

These do NOT require asyncssh. Run:
    python -m pytest tests/test_transport.py
    python tests/test_transport.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.transport import ServerConfig, ShellSession, TerminalWriter  # noqa: E402


class FakeReader:
    def __init__(self, lines):
        self._lines = list(lines)

    async def readline(self):
        if self._lines:
            return self._lines.pop(0)
        return None  # EOF


class FakeWriter:
    def __init__(self):
        self._parts = []

    def write(self, data):
        self._parts.append(data)

    def value(self):
        return "".join(self._parts)


def _session(lines, **cfg):
    config = ServerConfig(**cfg)
    out = FakeWriter()
    sess = ShellSession(config, FakeReader(lines), out, username="root")
    return sess, out


# --- terminal writer -----------------------------------------------------


def test_terminal_lf_to_crlf():
    w = FakeWriter()
    TerminalWriter(w, crlf=True).write("a\nb\n")
    assert w.value() == "a\r\nb\r\n"


def test_terminal_no_double_cr():
    w = FakeWriter()
    TerminalWriter(w, crlf=True).write("x\r\ny")
    assert w.value() == "x\r\ny"


def test_terminal_passthrough_when_off():
    w = FakeWriter()
    TerminalWriter(w, crlf=False).write("a\nb")
    assert w.value() == "a\nb"


# --- session: prompt -----------------------------------------------------


def test_prompt_root_at_home():
    sess, _ = _session([])
    assert sess.prompt() == "root@svr04:~# "


def test_prompt_shows_cwd():
    sess, _ = _session([])
    sess.ctx.cwd = "/etc"
    assert sess.prompt() == "root@svr04:/etc# "


def test_prompt_tilde_compression():
    sess, _ = _session([])
    sess.ctx.cwd = "/root/work"
    assert sess.prompt() == "root@svr04:~/work# "


# --- session: interactive loop -------------------------------------------


def test_interactive_runs_command_and_logs_out_on_eof():
    sess, out = _session(["whoami\n"])  # then EOF
    asyncio.run(sess.run_interactive())
    text = out.value()
    assert "root@svr04:~# " in text
    assert "root\n" in text
    assert text.rstrip().endswith("logout")


def test_exit_terminates_before_next_command():
    sess, out = _session(["exit\n", "echo SHOULD_NOT_RUN\n"])
    asyncio.run(sess.run_interactive())
    assert "SHOULD_NOT_RUN" not in out.value()


def test_exit_with_code_sets_status():
    sess, out = _session(["exit 7\n"])
    status = asyncio.run(sess.run_interactive())
    assert status == 7


def test_multiple_commands_and_state():
    sess, out = _session(["cd /etc\n", "pwd\n", "exit\n"])
    asyncio.run(sess.run_interactive())
    assert "/etc\n" in out.value()


def test_blank_line_just_reprompts():
    sess, out = _session(["\n", "whoami\n", "exit\n"])
    asyncio.run(sess.run_interactive())
    # two command prompts before exit's; blank line should not error
    assert out.value().count("root@svr04:~# ") >= 2
    assert "root\n" in out.value()


# --- session: exec mode --------------------------------------------------


def test_exec_mode_single_command():
    config = ServerConfig()
    out = FakeWriter()
    sess = ShellSession(config, FakeReader([]), out, username="root")
    status = asyncio.run(sess.run_exec("echo hi; whoami"))
    assert out.value() == "hi\nroot\n" and status == 0


def test_fresh_fs_per_session():
    # writing a file in one session must not leak into another
    c = ServerConfig()
    s1 = ShellSession(c, FakeReader([]), FakeWriter(), username="root")
    asyncio.run(s1.run_exec("echo x > /tmp/leak"))
    assert s1.ctx.fs.exists("/tmp/leak")
    s2 = ShellSession(c, FakeReader([]), FakeWriter(), username="root")
    assert not s2.ctx.fs.exists("/tmp/leak")


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
