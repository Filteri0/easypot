"""校準守門測試 —— 斷言真機 ground truth 通過**每一題**探測。

為什麼要有這條（治本）
----------------------
擬真度題庫的判定門檻（probes.py 的 must_contain / must_have_all / ideal_class /
accept_classes）是拿來衡量「受測系統像不像真機」的**量尺**。真機（real）是這把
量尺的**校準基準**——依定義，真機必然「像真機」，故真機理應通過自己的每一題。

若真機在某題失分，那**一定是量尺壞了**（題目門檻設錯 / locale 不一致 / ideal_class
標錯），不是真機露餡。歷史上就出過這種 bug：ground truth 採集在 zh_TW locale，df/ls
的欄位被翻譯成「檔案系統」「總用量」，被英文門檻誤判為 SALNLC；crontab -l 無排程回
FALC 卻被標成 ideal SALC 而失分。這些原本只在報告表裡默默呈現，難以察覺。

這條測試把「真機默默失分」變成「校準階段 CI 紅燈」——一改壞門檻就立刻被抓到。

資料來源（對應校準討論選項 1：用真機重採資料當 fixture）
------------------------------------------------------
讀 ``tools/ground_truth.txt``（由 tools/capture_ground_truth.sh 在**英文 locale**
下採集，腳本已強制 LC_ALL=C）。檔案不存在時**自動 skip**（如 ollama_integration
的慣例），讓尚未採集時 CI/離線仍保持綠。採集後把檔案放到 tools/ground_truth.txt
即自動生效。可用環境變數 ``EASYPOT_GROUND_TRUTH`` 指向他處。

跑法：
    python -m pytest tests/test_fidelity_calibration.py
    python tests/test_fidelity_calibration.py
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from tools.probes import PROBES  # noqa: E402
from tools.fidelity_judge import classify  # noqa: E402
from tools.run_probes import parse_ground_truth  # noqa: E402


def _ground_truth_path() -> str:
    return os.environ.get(
        "EASYPOT_GROUND_TRUTH", os.path.join(_ROOT, "tools", "ground_truth.txt")
    )


def _skip(reason: str) -> bool:
    try:
        import pytest
        pytest.skip(reason)
    except ImportError:
        print(f"SKIP: {reason}")
    return True


def _load():
    """回傳 (answers, None) 或 (None, skip_reason)。"""
    path = _ground_truth_path()
    if not os.path.exists(path):
        return None, (
            f"無 ground truth（{path}）：先在英文 locale 真機跑 "
            "tools/capture_ground_truth.sh 2>&1 > ground_truth.txt，"
            "再放到 tools/ground_truth.txt"
        )
    with open(path, encoding="utf-8") as fh:
        answers = parse_ground_truth(fh.read())
    if not answers:
        return None, f"ground truth 解析為空（格式不符？）：{path}"
    return answers, None


def test_ground_truth_covers_all_probes():
    """真機基準必須涵蓋每一題——半套採集會讓校準有盲區。"""
    answers, reason = _load()
    if reason:
        _skip(reason)
        return
    missing = sorted(p.id for p in PROBES if p.id not in answers)
    assert not missing, f"ground truth 缺這些題的真機輸出：{missing}"


def test_real_ground_truth_passes_all_probes():
    """核心守門：真機在每一題都應 passed=True（量尺對自己的基準必須通過）。

    任一題失分 → 該題的判定門檻壞了（見檔頭），修 probes.py / fidelity_judge.py，
    不是真機的問題。
    """
    answers, reason = _load()
    if reason:
        _skip(reason)
        return
    fails = []
    for p in PROBES:
        ra = answers.get(p.id)
        if ra is None:
            continue  # 覆蓋率由上一條測試把關
        j = classify(p, ra.output, ra.exit_code, "real")
        if not j.passed:
            fails.append(
                f"Q{p.id} {p.command!r}: 判為 {j.predicted_class}"
                f"（可接受={sorted(p.accept_classes)}）— {j.reason}"
            )
    assert not fails, (
        "真機應通過每一題（否則是判定門檻壞了，非真機露餡）：\n  "
        + "\n  ".join(fails)
    )


if __name__ == "__main__":
    failed = False
    for fn in (test_ground_truth_covers_all_probes,
               test_real_ground_truth_passes_all_probes):
        try:
            fn()
            print(f"PASS: {fn.__name__}")
        except AssertionError as e:
            print(f"FAIL: {fn.__name__}\n{e}")
            failed = True
        except BaseException as e:  # noqa: BLE001
            # pytest 存在時 pytest.skip() 拋 Skipped（繼承 BaseException，非
            # AssertionError）；standalone 下把它當 skip 呈現，其餘照拋。
            if type(e).__name__ == "Skipped":
                print(f"SKIP: {fn.__name__}: {e}")
            else:
                raise
    raise SystemExit(1 if failed else 0)
