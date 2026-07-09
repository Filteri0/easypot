"""End-to-end test against a real local Ollama server.

Skipped automatically when localhost:11434 is unreachable (or httpx/qwen2.5
aren't available), so CI and offline dev stay green.

    python -m pytest tests/test_ollama_integration.py
    python tests/test_ollama_integration.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from honeyshell.backends import ChainResolver, OllamaClient  # noqa: E402
from honeyshell.core import HoneypotConfig  # noqa: E402


def _server_up(client: OllamaClient) -> bool:
    try:
        return asyncio.run(client.is_available())
    except Exception:  # noqa: BLE001
        return False


def _skip(reason: str):
    try:
        import pytest
        pytest.skip(reason)
    except ImportError:
        print(f"SKIP: {reason}")
    return True


def test_ollama_uname_roundtrip():
    client = OllamaClient()  # qwen2.5:7b @ localhost:11434 by default
    if not _server_up(client):
        _skip("ollama not reachable at localhost:11434")
        return
    cfg = HoneypotConfig()
    cfg.system.hostname = "svr04"
    resolver = ChainResolver(client=client, config=cfg)
    res = asyncio.run(resolver.resolve(["uname", "-a"], "/root"))
    assert res is not None, "resolver returned None (LLM unavailable?)"
    # We can't assert exact wording from a live model, only that we got a
    # non-empty, plausible response and a valid impact score.
    assert isinstance(res.output, str) and res.output.strip() != ""
    assert 0 <= res.impact <= 4
    print("model output:", repr(res.output[:120]))


if __name__ == "__main__":
    try:
        test_ollama_uname_roundtrip()
        print("PASS (or skipped)")
    except AssertionError as e:
        print(f"FAIL: {e}")
        raise SystemExit(1)
