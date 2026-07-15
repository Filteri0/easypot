"""__main__ CLI 設定解析測試（雙模式：pytest 或 python tests/test_main_cli.py）。

聚焦 resolve_llm_settings 的優先序（CLI > env > 預設），這是 docker compose
用 EASYPOT_LLM* 環境變數控制 LLM 的接線。純函式，不起 server。
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from honeyshell.__main__ import resolve_llm_settings  # noqa: E402


def test_defaults_when_nothing_set():
    enable, model, url = resolve_llm_settings(
        cli_enable=False, cli_model=None, cli_url=None, env={})
    assert enable is False
    assert model == "qwen2.5:14b"
    assert url == "http://localhost:11434"


def test_cli_flag_enables():
    enable, _, _ = resolve_llm_settings(
        cli_enable=True, cli_model=None, cli_url=None, env={})
    assert enable is True


def test_env_enables_when_no_cli():
    # docker compose 走這條：EASYPOT_LLM=1
    enable, model, url = resolve_llm_settings(
        cli_enable=False, cli_model=None, cli_url=None,
        env={"EASYPOT_LLM": "1",
             "EASYPOT_LLM_URL": "http://host.docker.internal:11434"})
    assert enable is True
    assert url == "http://host.docker.internal:11434"
    assert model == "qwen2.5:14b"  # 未給則預設


def test_env_boolean_variants():
    def en(v):
        return resolve_llm_settings(
            cli_enable=False, cli_model=None, cli_url=None,
            env={"EASYPOT_LLM": v})[0]
    assert en("1") and en("true") and en("YES") and en("on")
    assert not en("0") and not en("false") and not en("") and not en("nope")


def test_cli_overrides_env():
    # CLI --llm-url 應蓋過 env
    _, _, url = resolve_llm_settings(
        cli_enable=True, cli_model=None, cli_url="http://cli:9999",
        env={"EASYPOT_LLM_URL": "http://env:11434"})
    assert url == "http://cli:9999"


def test_env_model_and_url_applied():
    _, model, url = resolve_llm_settings(
        cli_enable=False, cli_model=None, cli_url=None,
        env={"EASYPOT_LLM": "1",
             "EASYPOT_LLM_MODEL": "llama3:8b",
             "EASYPOT_LLM_URL": "http://x:1234"})
    assert model == "llama3:8b"
    assert url == "http://x:1234"


# --------------------------------------------------------------------------- #
# standalone runner
# --------------------------------------------------------------------------- #

def _run_standalone() -> int:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {exc!r}")
    total = len(fns)
    print(f"\n{total - failed}/{total} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_standalone())
