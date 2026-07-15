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

from honeyshell.transport import (  # noqa: E402
    INTERRUPT,
    ServerConfig,
    ShellSession,
    TerminalWriter,
)


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


# --- Ctrl-C / INTERRUPT sentinel -----------------------------------------


def test_interrupt_redraws_single_prompt_and_continues():
    """A reader that yields INTERRUPT (Ctrl-C) must not run a command and must
    resume the loop with exactly one more prompt — no storm, no exit."""
    # sequence: Ctrl-C, then a real command, then EOF
    sess, out = _session([INTERRUPT, "whoami\n", None])
    asyncio.run(sess.run_interactive())
    text = out.value()
    # whoami still ran after the interrupt
    assert "root" in text
    # the interrupt itself produced no "command not found" or output line
    assert "command not found" not in text
    # prompt count: initial + after-interrupt + after-whoami = 3 prompts,
    # then logout on EOF. Count occurrences of the prompt symbol.
    assert text.count("root@") >= 2  # at least the pre- and post-interrupt ones
    assert text.rstrip().endswith("logout")


def test_interrupt_does_not_execute_pending_text():
    """INTERRUPT is distinct from an empty line: nothing is dispatched."""
    sess, out = _session([INTERRUPT, None])
    asyncio.run(sess.run_interactive())
    # only prompts + logout, no command effects
    assert "logout" in out.value()


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


def test_audit_jsonl_path_defaults_none():
    # Standalone/bare runs stay quiet: no JSONL sink unless a path is set.
    assert ServerConfig().audit_jsonl_path is None


def test_audit_jsonl_path_configurable():
    cfg = ServerConfig(audit_jsonl_path="/data/audit/events.jsonl")
    assert cfg.audit_jsonl_path == "/data/audit/events.jsonl"


if __name__ == "__main__":
    raise SystemExit(_run_standalone())


# --- user provisioning consistency (demo-found tells) --------------------


def test_provision_unknown_user_is_consistent():
    """未知帳號登入:uid 唯一(非硬編 1000)、寫入 passwd、家目錄以該 uid 建立。
    修的是 id / grep passwd / ls -l owner 互相矛盾的指紋。"""
    config = ServerConfig()
    out = FakeWriter()
    sess = ShellSession(config, FakeReader([]), out, username="attacker")
    ctx = sess.ctx
    # uid must not be the old hardcoded 1000 (which collided with phil)
    assert ctx.uid != 1000 and ctx.uid >= 1000
    # passwd must now contain the account, matching id's uid
    passwd = ctx.fs.readtext("/etc/passwd")
    assert any(ln.startswith("attacker:") and f":{ctx.uid}:" in ln
               for ln in passwd.splitlines())
    # home exists and is owned by that uid
    st = ctx.fs.stat("/home/attacker")
    assert st.uid == ctx.uid


def test_provision_known_user_reuses_passwd_uid():
    """已在 passwd 的帳號(mchen=1002)登入應沿用該 uid,不另配。"""
    config = ServerConfig()
    out = FakeWriter()
    sess = ShellSession(config, FakeReader([]), out, username="mchen")
    assert sess.ctx.uid == 1002


def test_session_clock_and_boot_time_wired():
    """session 應注入模擬時鐘與 boot_time,讓 date/uptime 一致。"""
    config = ServerConfig()
    out = FakeWriter()
    sess = ShellSession(config, FakeReader([]), out, username="root")
    assert sess.ctx.clock is not None
    assert sess.ctx.boot_time is not None
    assert sess.ctx.now() > sess.ctx.boot_time


def test_session_shifts_fs_timeline_to_present():
    """載入後 fs 最新 mtime 應被平移到接近現在(不再停在 2024)。"""
    import time
    config = ServerConfig()
    out = FakeWriter()
    sess = ShellSession(config, FakeReader([]), out, username="root")
    newest = sess.ctx.fs._max_mtime(sess.ctx.fs.root)
    # newest file should be within the last ~30 days, not years ago
    assert time.time() - newest < 30 * 86400


def test_runtime_files_owned_by_login_user():
    """user 建立的檔案 owner 應是 user,不是 root(demo-found bug)。"""
    config = ServerConfig()
    out = FakeWriter()
    sess = ShellSession(config, FakeReader([]), out, username="alice")
    uid = sess.ctx.uid
    sess.ctx.fs.write_file("/home/alice/f.txt", "hi", "/home/alice")
    st = sess.ctx.fs.stat("/home/alice/f.txt")
    assert st.uid == uid and st.uid != 0
