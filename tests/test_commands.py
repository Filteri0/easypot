"""Tests for honeyshell.commands (base, registry, discovery, starter set).

Runnable two ways:
    python -m pytest tests/test_commands.py
    python tests/test_commands.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.commands import (  # noqa: E402
    Command,
    ShellContext,
    StringReader,
    StringWriter,
    all_commands,
    discover,
    register,
    resolve,
)
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402


def _ctx(cwd: str = "/") -> ShellContext:
    return ShellContext(fs=build_sample_fs(hostname="svr04"), cwd=cwd, username="root")


def _run(cls, argv, ctx=None, stdin_text=""):
    """Instantiate, run, and return (exit_code, stdout, stderr, ctx)."""
    ctx = ctx or _ctx()
    out, err = StringWriter(), StringWriter()
    cmd = cls(ctx, argv, StringReader(stdin_text), out, err)
    code = asyncio.run(cmd.run())
    return code, out.getvalue(), err.getvalue(), ctx


# --- registry ------------------------------------------------------------


def test_discover_populates_registry():
    discover()
    reg = all_commands()
    for name in ("echo", "pwd", "whoami", "cat", "ls", "cd", "true", "false"):
        assert name in reg, name


def test_resolve_by_path_basename():
    discover()
    assert resolve("/bin/echo") is resolve("echo")
    assert resolve("/usr/bin/whoami") is resolve("whoami")
    assert resolve("definitely-not-a-command") is None


def test_register_sets_name():
    @register("frob", "/opt/frob")
    class Frob(Command):
        async def run(self) -> int:
            return 0

    assert Frob.name == "frob"
    assert resolve("/opt/frob") is Frob


# --- base contract -------------------------------------------------------


def test_args_and_prog_split():
    ctx = _ctx()
    cmd = Command(ctx, ["/bin/ls", "-la", "/tmp"])
    assert cmd.prog == "/bin/ls"
    assert cmd.args == ["-la", "/tmp"]


def test_fail_helper_formats_and_returns_code():
    ctx = _ctx()
    out, err = StringWriter(), StringWriter()
    cmd = Command(ctx, ["thing"], None, out, err)
    code = cmd.fail("bad stuff", code=2)
    assert code == 2
    assert err.getvalue() == "thing: bad stuff\n"


# --- starter commands ----------------------------------------------------


def test_echo():
    discover()
    code, out, _, _ = _run(resolve("echo"), ["echo", "hello", "world"])
    assert code == 0 and out == "hello world\n"


def test_echo_no_newline():
    discover()
    _, out, _, _ = _run(resolve("echo"), ["echo", "-n", "hi"])
    assert out == "hi"


def test_pwd_reflects_context():
    discover()
    _, out, _, _ = _run(resolve("pwd"), ["pwd"], ctx=_ctx("/home/svc"))
    assert out == "/home/svc\n"


def test_whoami():
    discover()
    _, out, _, _ = _run(resolve("whoami"), ["whoami"])
    assert out == "root\n"


def test_true_false_exit_codes():
    discover()
    assert _run(resolve("true"), ["true"])[0] == 0
    assert _run(resolve("false"), ["false"])[0] == 1


def test_cd_changes_context_cwd():
    discover()
    ctx = _ctx("/")
    code, _, _, ctx = _run(resolve("cd"), ["cd", "/etc"], ctx=ctx)
    assert code == 0 and ctx.cwd == "/etc"


def test_cd_into_file_errors():
    discover()
    code, _, err, ctx = _run(resolve("cd"), ["cd", "/etc/passwd"], ctx=_ctx())
    assert code == 1 and "Not a directory" in err and ctx.cwd == "/"


def test_cd_missing_errors():
    discover()
    code, _, err, _ = _run(resolve("cd"), ["cd", "/nope"])
    assert code == 1 and "No such file or directory" in err


def test_cat_file():
    discover()
    _, out, _, _ = _run(resolve("cat"), ["cat", "/etc/hostname"])
    assert out == "svr04\n"


def test_cat_missing_file():
    discover()
    code, _, err, _ = _run(resolve("cat"), ["cat", "/nope"])
    assert code == 1 and "No such file or directory" in err


def test_cat_stdin_passthrough():
    # cat with no operands copies stdin -> stdout (pipeline semantics)
    discover()
    _, out, _, _ = _run(resolve("cat"), ["cat"], stdin_text="a\nb\n")
    assert out == "a\nb\n"


def test_ls_dir_hides_dotfiles_by_default():
    discover()
    _, out, _, _ = _run(resolve("ls"), ["ls", "/home/svc"])
    assert out == ""  # only .bashrc exists, hidden by default -> nothing printed


def test_ls_all_shows_dotfiles():
    discover()
    _, out, _, _ = _run(resolve("ls"), ["ls", "-a", "/home/svc"])
    assert ".bashrc" in out


def test_ls_default_cwd():
    discover()
    _, out, _, _ = _run(resolve("ls"), ["ls"], ctx=_ctx("/etc"))
    names = set(out.split())
    # /etc is now DB-persona-populated; assert the key entries are present
    # (subset check, robust to future additions) and dotfiles-only dirs show.
    assert {"hostname", "os-release", "passwd", "shadow",
            "postgresql", "ssh"} <= names


def test_ls_missing_path_errors():
    discover()
    code, _, err, _ = _run(resolve("ls"), ["ls", "/nope"])
    assert code == 1 and "No such file or directory" in err


def test_ls_long_uses_real_mtime_not_hardcoded():
    # §3: ls -l must reflect per-file mtimes, not the old hardcoded
    # "Jan  1 00:00" fingerprint. /etc files date to install (Feb 2024),
    # user/log activity to Jun 2024 — so we should see >1 distinct month
    # and never the old placeholder.
    discover()
    _, out, _, _ = _run(resolve("ls"), ["ls", "-l", "/etc"], ctx=_ctx("/etc"))
    assert "Jan  1 00:00" not in out
    months = {ln.split()[5] for ln in out.splitlines() if len(ln.split()) >= 8}
    assert len(months) >= 2  # not all identical → fingerprint defeated


def test_fmt_time_recent_and_old_forms():
    from honeyshell.commands.impl.ls import _fmt_time, _ref_now
    ref = _ref_now()
    # recent (< 6 months before now): shows clock "HH:MM"
    recent = _fmt_time(ref - 5 * 86400)
    assert ":" in recent and recent.split()[-1].count(":") == 1
    # old (> 6 months): shows the year instead of a clock
    old = _fmt_time(ref - 400 * 86400)
    assert ":" not in old and old.split()[-1].isdigit()


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



# --- option-parsing correctness (Gemini QA: no bogus option tells) -------


def test_ls_unrecognized_long_option():
    discover()
    ls = resolve("ls")
    code, out, err, _ = _run(ls, ["ls", "--fakearg"])
    # Must NOT split "--fakearg" into short flags (the old bug printed
    # "invalid option -- '-'"). GNU coreutils reports the long option verbatim.
    assert code == 2
    assert "unrecognized option '--fakearg'" in err
    assert "invalid option -- '-'" not in err


def test_ls_double_dash_ends_options():
    discover()
    ls = resolve("ls")
    # "--" terminates option parsing; a following "-l" is treated as a name.
    code, _, err, _ = _run(ls, ["ls", "--", "-l"])
    assert "cannot access '-l'" in err  # looked up as a path, not a flag


def test_cat_unknown_short_flag_is_invalid_option():
    discover()
    cat = resolve("cat")
    code, out, err, _ = _run(cat, ["cat", "-Z"])
    # Old bug: "-Z" was treated as a filename ("-Z: No such file...").
    assert code == 2
    assert "invalid option -- 'Z'" in err
    assert "No such file" not in err


def test_cat_number_flag():
    discover()
    cat = resolve("cat")
    ctx = _ctx()
    ctx.fs.write_file("/tmp/x", "a\nb\n")
    code, out, err, _ = _run(cat, ["cat", "-n", "/tmp/x"], ctx=ctx)
    assert code == 0
    assert "     1\ta" in out and "     2\tb" in out


def test_cat_dash_is_stdin_not_flag():
    discover()
    cat = resolve("cat")
    code, out, err, _ = _run(cat, ["cat", "-"], stdin_text="hello\n")
    assert code == 0 and out == "hello\n"


def test_curl_head_prints_headers_not_body():
    discover()
    curl = resolve("curl")
    code, out, err, _ = _run(curl, ["curl", "-I", "https://google.com"])
    assert code == 0
    assert out.startswith("HTTP/1.1 200 OK")
    assert "Server:" in out and "Content-Type:" in out
    # -I must NOT emit the download placeholder body.
    assert "# downloaded from" not in out


def test_curl_head_writes_no_file():
    discover()
    curl = resolve("curl")
    ctx = _ctx()
    _run(curl, ["curl", "-I", "-O", "http://x/y.txt"], ctx=ctx)
    # HEAD short-circuits before any save; no file should appear.
    assert not ctx.fs.exists("/y.txt", ctx.cwd)


if __name__ == "__main__":
    raise SystemExit(_run_standalone())


# --- honeypot fidelity fixes (demo-found tells) --------------------------


def test_ls_d_lists_directory_itself():
    discover()
    _, out, _, _ = _run(resolve("ls"), ["ls", "-ld", "/etc"], ctx=_ctx("/"))
    # -d shows the dir entry, not its contents
    assert "/etc" in out and "passwd" not in out


def test_ls_long_owner_resolved_to_name():
    """ls -l 的 owner/group 應解析成 /etc/passwd 的名字,而非裸 uid 數字。"""
    discover()
    _, out, _, _ = _run(resolve("ls"), ["ls", "-l", "/home"], ctx=_ctx("/"))
    assert "mchen" in out and "deploy" in out
    # the numeric uid should not appear as the owner column
    assert " 1002 " not in out


def test_ls_long_total_is_blocks_not_count():
    """total 應是磁碟區塊估算,不是條目數(4 個目錄的 count=4 太小)。"""
    discover()
    _, out, _, _ = _run(resolve("ls"), ["ls", "-l", "/home"], ctx=_ctx("/"))
    total_line = out.splitlines()[0]
    assert total_line.startswith("total ")
    assert int(total_line.split()[1]) >= 8  # blocks, well above dir count


def test_stat_reports_metadata():
    discover()
    code, out, _, _ = _run(resolve("stat"), ["stat", "/etc/hostname"],
                           ctx=_ctx("/"))
    assert code == 0
    assert "File: /etc/hostname" in out
    assert "regular file" in out and "Modify:" in out


def test_stat_missing_file_errors():
    discover()
    code, _, err, _ = _run(resolve("stat"), ["stat", "/nope"], ctx=_ctx("/"))
    assert code == 1 and "No such file or directory" in err


def test_ls_dir_link_count_reflects_subdirs():
    """目錄 link count 應為 2+子目錄數,而非硬編 1(指紋)。"""
    discover()
    # /home/mchen ships subdirs (.ssh, queries) -> nlink should exceed 2
    _, out, _, _ = _run(resolve("ls"), ["ls", "-la", "/home/mchen"],
                        ctx=_ctx("/"))
    # find the "." entry (the dir itself)
    dot = [l for l in out.splitlines() if l.endswith(" .")]
    assert dot, "no '.' entry in ls -la"
    nlink = int(dot[0].split()[1])
    assert nlink >= 2


# --- permission enforcement (demo-found: no permission model) ------------


def test_user_cannot_cd_into_root_home():
    discover()
    ctx = _ctx("/")
    ctx.username = "user"
    ctx.login_uid = 1001
    code, _, err, _ = _run(resolve("cd"), ["cd", "/root"], ctx=ctx)
    assert code != 0 and "Permission denied" in err


def test_user_cannot_mkdir_in_root_home():
    discover()
    ctx = _ctx("/root")
    ctx.username = "user"
    ctx.login_uid = 1001
    code, _, err, _ = _run(resolve("mkdir"), ["mkdir", "x"], ctx=ctx)
    assert code != 0 and "Permission denied" in err


def test_root_can_cd_into_root_home():
    discover()
    ctx = _ctx("/")  # username defaults to root in _ctx
    code, _, _, _ = _run(resolve("cd"), ["cd", "/root"], ctx=ctx)
    assert code == 0


def test_fs_access_permission_bits():
    from honeyshell.fs.build_sample_fs import build
    fs = build()
    # /root is 0700 owned by root: non-root uid has no access, root does.
    assert fs.access("/root", "x", 1001) is False
    assert fs.access("/root", "x", 0) is True
    # /tmp is world-writable (1777): any uid can write.
    assert fs.access("/tmp", "w", 1001) is True
