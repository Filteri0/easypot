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
    lines = out.strip().split("\n")
    assert set(lines) == {"hostname", "os-release", "passwd"}


def test_ls_missing_path_errors():
    discover()
    code, _, err, _ = _run(resolve("ls"), ["ls", "/nope"])
    assert code == 1 and "No such file or directory" in err


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
