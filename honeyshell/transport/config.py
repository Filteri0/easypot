"""Configuration for the SSH honeypot server.

Kept deliberately small and dependency-free so it can be unit-tested and reused
by the session layer without importing asyncssh.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

_DEFAULT_FS = Path(__file__).resolve().parent.parent / "data" / "fs.json"

# Login attempt logger: (username, password, peer, accepted) -> None
LoginLogger = Callable[[str, str, object, bool], None]


def _default_environ() -> dict[str, str]:
    return {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "TERM": "xterm",
        "SHELL": "/bin/bash",
        "LANG": "en_US.UTF-8",
    }


@dataclass
class ServerConfig:
    host: str = ""            # "" binds all interfaces
    port: int = 2222
    fs_path: str = str(_DEFAULT_FS)
    hostname: str = "svr04"
    default_user: str = "root"
    motd: str = ""            # printed once at interactive login
    host_key_path: Optional[str] = None   # persist for a stable fingerprint
    server_version: str = "SSH-2.0-OpenSSH_8.4p1 Debian-5"

    # auth policy
    accept_all: bool = True
    valid_credentials: dict[str, str] = field(default_factory=dict)
    login_logger: Optional[LoginLogger] = None

    base_environ: dict[str, str] = field(default_factory=_default_environ)

    # LLM backend (paper §3): when enabled, registry-missed commands are
    # answered by a local Ollama model instead of "command not found". Kept
    # off by default so the honeypot runs standalone without a model; the
    # transport builds the resolver only when this is True.
    llm_enable: bool = False
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str = "http://localhost:11434"

    def accept(self, username: str, password: str) -> bool:
        if self.accept_all:
            return True
        return self.valid_credentials.get(username) == password

    def log_login(self, username: str, password: str, peer: object, ok: bool) -> None:
        if self.login_logger is not None:
            self.login_logger(username, password, peer, ok)
