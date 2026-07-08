"""Run the honeypot SSH server: ``python -m honeyshell [options]``."""

from __future__ import annotations

import argparse
import asyncio
import logging

from honeyshell.transport import ServerConfig
from honeyshell.transport import start_server  # lazy asyncssh import

log = logging.getLogger("honeyshell")


def _log_login(user: str, password: str, peer: object, ok: bool) -> None:
    addr = peer[0] if isinstance(peer, tuple) else peer
    log.info("login %s user=%r password=%r from=%s", "OK" if ok else "FAIL",
             user, password, addr)


async def _run(config: ServerConfig) -> None:
    server = await start_server(config)
    for sock in server.sockets:
        log.info("listening on %s", sock.getsockname())
    await asyncio.Event().wait()  # run forever


def main() -> None:
    ap = argparse.ArgumentParser(description="honeyshell SSH honeypot")
    ap.add_argument("--host", default="")
    ap.add_argument("--port", type=int, default=2222)
    ap.add_argument("--hostname", default="svr04")
    ap.add_argument("--fs", dest="fs_path", default=None)
    ap.add_argument("--host-key", dest="host_key_path", default=None)
    ap.add_argument("--motd", default="")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    kwargs = dict(
        host=args.host,
        port=args.port,
        hostname=args.hostname,
        host_key_path=args.host_key_path,
        motd=args.motd,
        login_logger=_log_login,
    )
    if args.fs_path:
        kwargs["fs_path"] = args.fs_path
    config = ServerConfig(**kwargs)

    try:
        asyncio.run(_run(config))
    except KeyboardInterrupt:
        log.info("shutting down")


if __name__ == "__main__":
    main()
