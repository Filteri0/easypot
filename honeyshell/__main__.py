"""Run the honeypot SSH server: ``python -m honeyshell [options]``."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

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


def resolve_llm_settings(
    *,
    cli_enable: bool,
    cli_model: "str | None",
    cli_url: "str | None",
    env: "dict[str, str] | None" = None,
) -> "tuple[bool, str, str]":
    """決定最終 (enable, model, base_url)。純函式，好單測。

    優先序：CLI flag > 環境變數 > 內建預設。與 EASYPOT_AUDIT_JSONL 的解析
    對稱，讓 docker compose 能全用 env 控制 LLM 而不必改 CMD。
    """
    e = env if env is not None else os.environ
    enable = cli_enable or (e.get("EASYPOT_LLM", "").strip().lower()
                            in {"1", "true", "yes", "on"})
    model = cli_model or e.get("EASYPOT_LLM_MODEL") or "qwen2.5:14b"
    url = cli_url or e.get("EASYPOT_LLM_URL") or "http://localhost:11434"
    return enable, model, url


def main() -> None:
    ap = argparse.ArgumentParser(description="honeyshell SSH honeypot")
    ap.add_argument("--host", default="")
    ap.add_argument("--port", type=int, default=2222)
    ap.add_argument("--hostname", default="svr04")
    ap.add_argument("--fs", dest="fs_path", default=None)
    ap.add_argument("--host-key", dest="host_key_path", default=None)
    ap.add_argument("--motd", default="")
    ap.add_argument("--llm", dest="llm_enable", action="store_true",
                    help="answer unknown commands with a local Ollama model. "
                         "Env: EASYPOT_LLM=1.")
    ap.add_argument("--llm-model", default=None,
                    help="Ollama model name (default: qwen2.5:14b). "
                         "Env: EASYPOT_LLM_MODEL.")
    ap.add_argument("--llm-url", dest="llm_base_url", default=None,
                    help="Ollama base URL (default: http://localhost:11434). "
                         "Env: EASYPOT_LLM_URL.")
    ap.add_argument("--log-level", default="INFO",
                    help="logging level: DEBUG/INFO/WARNING (default: INFO). "
                         "DEBUG shows each LLM answer's impact and fs_ops count.")
    ap.add_argument("--audit-jsonl", dest="audit_jsonl_path", default=None,
                    help="append structured audit events (commands, errors, "
                         "credentials) as JSON lines to this file; the log "
                         "collector tails it. Env: EASYPOT_AUDIT_JSONL.")
    args = ap.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    # LLM 設定：CLI flag 優先，否則讀環境變數（與 EASYPOT_AUDIT_JSONL 對稱，
    # 方便 docker compose 全用 env 控制而不必改 CMD）。
    llm_enable, llm_model, llm_base_url = resolve_llm_settings(
        cli_enable=args.llm_enable,
        cli_model=args.llm_model,
        cli_url=args.llm_base_url,
    )

    kwargs = dict(
        host=args.host,
        port=args.port,
        hostname=args.hostname,
        host_key_path=args.host_key_path,
        motd=args.motd,
        login_logger=_log_login,
        llm_enable=llm_enable,
        llm_model=llm_model,
        llm_base_url=llm_base_url,
    )
    if args.fs_path:
        kwargs["fs_path"] = args.fs_path
    # Audit feed: CLI flag wins, else EASYPOT_AUDIT_JSONL env (handy in Docker).
    audit_path = args.audit_jsonl_path or os.environ.get("EASYPOT_AUDIT_JSONL")
    if audit_path:
        kwargs["audit_jsonl_path"] = audit_path
    config = ServerConfig(**kwargs)

    try:
        asyncio.run(_run(config))
    except KeyboardInterrupt:
        log.info("shutting down")


if __name__ == "__main__":
    main()
