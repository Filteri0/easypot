"""Tests for the privilege/persistence builtins (batch 3).

chmod, chown  -> really mutate the VFS (new fs.chmod/fs.chown API)
sudo, su, passwd -> interactive credential capture onto the event bus
crontab       -> persistence table stored in the VFS

Interactive commands are driven with a fake read_prompt (scripted password
input) and a real EventBus to assert credentials are captured. Commands that
run a sub-command (sudo/su -c) use a real Interpreter so the sub-run actually
executes.

Runnable two ways:
    python -m pytest tests/test_priv.py
    python tests/test_priv.py
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
from honeyshell.core.event_bus import EventBus  # noqa: E402
from honeyshell.shell.interpreter import Interpreter  # noqa: E402
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402

discover()


def _bus():
    captured = []
    bus = EventBus()
    bus.subscribe(lambda e: captured.append((e.username, e.password, e.success)),
                  None)
    return bus, captured


def _ctx(username="root", bus=None, prompts=None):
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/root",
                       username=username)
    if bus is not None:
        ctx.event_bus = bus
    if prompts is not None:
        it = iter(prompts)

        async def fake_prompt(text, hide=False):
            try:
                return next(it)
            except StopIteration:
                return None
        ctx.read_prompt = fake_prompt
    return ctx


def _run(name, tail, ctx, stdin=""):
    cls = resolve(name)
    assert cls is not None, f"{name} not registered"
    out, err = StringWriter(), StringWriter()
    code = asyncio.run(cls(ctx, [name, *tail], StringReader(stdin), out,
                           err).run())
    return code, out.getvalue(), err.getvalue()


def _run_interp(ctx, line):
    out, err = StringWriter(), StringWriter()
    interp = Interpreter(ctx, stdout=out, stderr=err)
    code = asyncio.run(interp.execute(line))
    return code, out.getvalue(), err.getvalue()


# --- chmod / chown -------------------------------------------------------


def test_chmod_octal_mutates_vfs():
    ctx = _ctx()
    ctx.fs.write_file("/root/s.sh", b"#!/bin/sh", "/root")
    _run("chmod", ["755", "/root/s.sh"], ctx)
    assert ctx.fs.stat("/root/s.sh").perm == 0o755


def test_chmod_symbolic_plus_x():
    ctx = _ctx()
    ctx.fs.write_file("/root/f", b"x", "/root")  # starts 0o644
    _run("chmod", ["+x", "/root/f"], ctx)
    assert ctx.fs.stat("/root/f").perm == 0o755


def test_chmod_missing_file_errors():
    code, out, err = _run("chmod", ["755", "/root/nope"], _ctx())
    assert code != 0 and "No such file" in err


def test_chown_changes_owner():
    ctx = _ctx()
    ctx.fs.write_file("/root/f", b"x", "/root")
    _run("chown", ["1000:1000", "/root/f"], ctx)
    st = ctx.fs.stat("/root/f")
    assert st.uid == 1000 and st.gid == 1000


# --- sudo ----------------------------------------------------------------


def test_sudo_root_runs_without_password():
    ctx = _ctx(username="root")
    code, out, err = _run_interp(ctx, "sudo id")
    assert "uid=0(root)" in out


def test_sudo_nonroot_prompts_records_and_runs():
    bus, captured = _bus()
    ctx = _ctx(username="alice", bus=bus, prompts=["s3cret"])
    code, out, err = _run_interp(ctx, "sudo whoami")
    assert out.strip() == "alice"
    assert ("alice", "s3cret", True) in captured   # credential captured


def test_sudo_runs_command_that_mutates_vfs():
    ctx = _ctx(username="root")
    _run_interp(ctx, "sudo mkdir /opt/persist")
    assert ctx.fs.exists("/opt/persist")


def test_sudo_exit_does_not_close_session():
    ctx = _ctx(username="root")
    _run_interp(ctx, 'sudo sh -c "exit 0"')
    assert ctx.should_exit is False


# --- su ------------------------------------------------------------------


def test_su_dash_c_runs_as_target_and_restores():
    bus, captured = _bus()
    ctx = _ctx(username="bob", bus=bus, prompts=["pw"])
    code, out, err = _run_interp(ctx, "su -c whoami root")
    assert out.strip() == "root"          # ran as root
    assert ctx.username == "bob"           # identity restored
    assert ("root", "pw", True) in captured


def test_su_root_no_password_needed():
    ctx = _ctx(username="root")
    code, out, err = _run_interp(ctx, "su -c whoami alice")
    assert out.strip() == "alice"


# --- passwd --------------------------------------------------------------


def test_passwd_root_sets_successfully():
    bus, captured = _bus()
    ctx = _ctx(username="root", bus=bus, prompts=["newpw", "newpw"])
    code, out, err = _run("passwd", [], ctx)
    assert code == 0 and "updated successfully" in out
    assert any(p == "newpw" for _, p, _ in captured)


def test_passwd_mismatch_fails():
    ctx = _ctx(username="root", prompts=["a", "b"])
    code, out, err = _run("passwd", [], ctx)
    assert code != 0 and "do not match" in err


def test_passwd_nonroot_asks_current_first():
    bus, captured = _bus()
    ctx = _ctx(username="alice", bus=bus, prompts=["oldpw", "newpw", "newpw"])
    code, out, err = _run("passwd", [], ctx)
    assert code == 0
    # both the current and the new password are captured
    caught = [p for _, p, _ in captured]
    assert "oldpw" in caught and "newpw" in caught


# --- crontab -------------------------------------------------------------


def test_crontab_install_and_list():
    ctx = _ctx()
    _run("crontab", ["-"], ctx, stdin="* * * * * /tmp/evil.sh\n")
    code, out, err = _run("crontab", ["-l"], ctx)
    assert "/tmp/evil.sh" in out


def test_crontab_list_empty():
    code, out, err = _run("crontab", ["-l"], _ctx())
    assert code != 0 and "no crontab" in err


def test_crontab_remove():
    ctx = _ctx()
    _run("crontab", ["-"], ctx, stdin="0 0 * * * backup\n")
    _run("crontab", ["-r"], ctx)
    code, out, err = _run("crontab", ["-l"], ctx)
    assert "no crontab" in err


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


# --- read permission (cat/head/grep /etc/shadow; < redirect) -------------


def _user_ctx(username="alice", uid=1001):
    """A non-root context with a resolved login uid, cwd in the user's home."""
    ctx = ShellContext(fs=build_sample_fs(hostname="svr04"),
                       cwd="/home/alice", username=username)
    ctx.login_uid = uid
    return ctx


def test_cat_shadow_denied_for_user():
    code, out, err = _run("cat", ["/etc/shadow"], _user_ctx())
    assert code != 0
    assert "Permission denied" in err
    assert "REDACTED" not in out  # contents must not leak


def test_cat_shadow_allowed_for_root():
    code, out, err = _run("cat", ["/etc/shadow"], _ctx(username="root"))
    assert code == 0
    assert "root:" in out  # root reads it fine


def test_cat_passwd_still_readable_by_user():
    # /etc/passwd is 0644 — a normal user can read it; only shadow is gated.
    code, out, err = _run("cat", ["/etc/passwd"], _user_ctx())
    assert code == 0 and "root:x:0:0" in out


def test_head_and_grep_shadow_denied_for_user():
    for cmd in ("head", "grep"):
        tail = ["/etc/shadow"] if cmd == "head" else ["root", "/etc/shadow"]
        code, out, err = _run(cmd, tail, _user_ctx())
        assert code != 0, cmd
        assert "Permission denied" in err, cmd
        assert "REDACTED" not in out, cmd


def test_redirect_from_shadow_denied_for_user():
    # `cat < /etc/shadow` as a normal user: the redirect itself is gated.
    code, out, err = _run_interp(_user_ctx(), "cat < /etc/shadow")
    assert "Permission denied" in err
    assert "REDACTED" not in out


def test_redirect_from_shadow_allowed_for_root():
    code, out, err = _run_interp(_ctx(username="root"), "cat < /etc/shadow")
    assert "root:" in out


def test_ls_denied_on_unreadable_dir_for_user():
    # /root is 0700 root:root — a normal user cannot list it.
    code, out, err = _run("ls", ["/root"], _user_ctx())
    assert code != 0
    assert "Permission denied" in err
    assert "cannot open directory '/root'" in err


def test_ls_root_can_list_root_dir():
    # root bypasses the check (dotfiles need -a, but the listing itself works).
    code, out, err = _run("ls", ["-a", "/root"], _ctx(username="root"))
    assert code == 0
    assert "Permission denied" not in err
    assert ".bashrc" in out


def test_ls_user_can_list_own_readable_dir():
    # /etc is world-readable (0755) — a normal user lists it fine.
    code, out, err = _run("ls", ["/etc"], _user_ctx())
    assert code == 0 and "hostname" in out


# --- rm / cp / mv permission (parent-dir writability) --------------------


def test_rm_denied_without_parent_write():
    # alice can't remove a file in root-owned /root (no write on the dir).
    ctx = _user_ctx()
    code, out, err = _run("rm", ["/root/.bashrc"], ctx)
    assert code != 0 and "Permission denied" in err
    assert ctx.fs.exists("/root/.bashrc")  # still there


def test_rm_f_does_not_bypass_permission():
    # -f silences missing-file errors but must NOT bypass permissions.
    ctx = _user_ctx()
    code, out, err = _run("rm", ["-f", "/root/.bashrc"], ctx)
    assert ctx.fs.exists("/root/.bashrc")


def test_rm_allowed_in_writable_dir():
    ctx = _user_ctx()
    ctx.fs.write_file("/tmp/mine", b"x", "/tmp", uid=1001, gid=1001)
    code, out, err = _run("rm", ["/tmp/mine"], ctx)
    assert code == 0 and not ctx.fs.exists("/tmp/mine")


def test_root_rm_bypasses_permission():
    ctx = _ctx(username="root")
    code, out, err = _run("rm", ["/root/.bashrc"], ctx)
    assert code == 0 and not ctx.fs.exists("/root/.bashrc")


def test_cp_denied_reading_unreadable_source():
    ctx = _user_ctx()
    code, out, err = _run("cp", ["/etc/shadow", "/tmp/s"], ctx)
    assert code != 0 and "Permission denied" in err
    assert not ctx.fs.exists("/tmp/s")


def test_cp_denied_writing_unwritable_dest_dir():
    ctx = _user_ctx()
    # readable source (/etc/hostname is 0644), unwritable dest dir (/root).
    code, out, err = _run("cp", ["/etc/hostname", "/root/h"], ctx)
    assert code != 0 and "Permission denied" in err


def test_cp_allowed_readable_src_writable_dst():
    ctx = _user_ctx()
    code, out, err = _run("cp", ["/etc/hostname", "/tmp/h"], ctx)
    assert code == 0 and ctx.fs.exists("/tmp/h")


def test_mv_denied_without_source_parent_write():
    ctx = _user_ctx()
    code, out, err = _run("mv", ["/etc/hostname", "/tmp/"], ctx)
    assert code != 0 and "Permission denied" in err
    assert ctx.fs.exists("/etc/hostname")  # not moved


def test_mv_denied_without_dest_parent_write():
    ctx = _user_ctx()
    ctx.fs.write_file("/tmp/f", b"x", "/tmp", uid=1001, gid=1001)
    code, out, err = _run("mv", ["/tmp/f", "/root/f"], ctx)
    assert code != 0 and "Permission denied" in err
    assert ctx.fs.exists("/tmp/f")  # still at source


def test_mv_allowed_between_writable_dirs():
    ctx = _user_ctx()
    ctx.fs.write_file("/tmp/f", b"x", "/tmp", uid=1001, gid=1001)
    ctx.fs.mkdir("/tmp/d", uid=1001, gid=1001)
    code, out, err = _run("mv", ["/tmp/f", "/tmp/d/"], ctx)
    assert code == 0 and ctx.fs.exists("/tmp/d/f")


if __name__ == "__main__":
    raise SystemExit(_run_standalone())


# --- su identity switch (demo-found: prompt/uid didn't change) ------------


def test_su_bare_switches_identity_and_uid():
    """su(從非 root)成功後:username=root、uid=0、cwd=/root。
    修的是 demo 中 su 後提示符仍是 user@ 的破綻。"""
    ctx = _ctx(username="mchen", prompts=["whatever"])
    ctx.login_uid = 1002
    ctx.cwd = "/home/mchen"
    code, _, _ = _run("su", [], ctx)
    assert code == 0
    assert ctx.username == "root"
    assert ctx.uid == 0
    assert ctx.cwd == "/root"


def test_su_to_named_user_resolves_passwd_uid():
    """su mchen 應把 login_uid 設成 passwd 中的 1002。"""
    ctx = _ctx(username="root")  # root -> no password needed
    code, _, _ = _run("su", ["mchen"], ctx)
    assert code == 0
    assert ctx.username == "mchen"
    assert ctx.login_uid == 1002
