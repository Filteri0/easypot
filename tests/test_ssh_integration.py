"""End-to-end tests over a real asyncssh connection.

Boots the honeypot on an ephemeral port and connects as a client, exercising
auth + exec + interactive paths through the whole stack. Skipped automatically
if asyncssh is not installed.

    python -m pytest tests/test_ssh_integration.py
    python tests/test_ssh_integration.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import asyncssh
except ImportError:  # pragma: no cover
    asyncssh = None

from honeyshell.transport import ServerConfig  # noqa: E402


async def _boot():
    from honeyshell.transport import start_server

    logins = []
    config = ServerConfig(
        host="127.0.0.1",
        port=0,  # OS-assigned
        login_logger=lambda u, p, peer, ok: logins.append((u, p, ok)),
    )
    server = await start_server(config)
    port = server.sockets[0].getsockname()[1]
    return server, port, logins


async def _exec_case():
    server, port, logins = await _boot()
    try:
        async with asyncssh.connect(
            "127.0.0.1", port, username="root", password="hunter2",
            known_hosts=None,
        ) as conn:
            result = await conn.run("echo hi; whoami; pwd")
        assert result.stdout == "hi\nroot\n/root\n", repr(result.stdout)
        assert ("root", "hunter2", True) in logins
    finally:
        server.close()


async def _interactive_case():
    server, port, logins = await _boot()
    try:
        async with asyncssh.connect(
            "127.0.0.1", port, username="admin", password="x", known_hosts=None,
        ) as conn:
            proc = await conn.create_process(term_type="xterm", term_size=(80, 24))
            proc.stdin.write("whoami\n")
            proc.stdin.write("cd /etc\n")
            proc.stdin.write("pwd\n")
            proc.stdin.write("exit\n")
            out = await asyncio.wait_for(proc.stdout.read(), timeout=10)
        # lenient on CR/echo; just check behaviour is present and ordered
        clean = out.replace("\r", "")
        assert "admin" in clean
        assert "/etc" in clean
        assert "logout" in clean
    finally:
        server.close()


async def _reject_case():
    server, port, logins = await _boot()
    server_cfg_rejects = None
    try:
        # a server that only accepts specific creds
        from honeyshell.transport import start_server

        cfg = ServerConfig(host="127.0.0.1", port=0, accept_all=False,
                           valid_credentials={"root": "toor"})
        s2 = await start_server(cfg)
        p2 = s2.sockets[0].getsockname()[1]
        try:
            failed = False
            try:
                async with asyncssh.connect(
                    "127.0.0.1", p2, username="root", password="wrong",
                    known_hosts=None,
                ):
                    pass
            except asyncssh.PermissionDenied:
                failed = True
            assert failed, "expected auth to be rejected"
        finally:
            s2.close()
    finally:
        server.close()


def test_exec_over_ssh():
    if asyncssh is None:
        print("skip: asyncssh not installed")
        return
    asyncio.run(_exec_case())


def test_interactive_over_ssh():
    if asyncssh is None:
        print("skip: asyncssh not installed")
        return
    asyncio.run(_interactive_case())


def test_auth_rejection():
    if asyncssh is None:
        print("skip: asyncssh not installed")
        return
    asyncio.run(_reject_case())


def _run_standalone() -> int:
    if asyncssh is None:
        print("asyncssh not installed - skipping integration tests")
        return 0
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
