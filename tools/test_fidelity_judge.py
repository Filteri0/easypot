"""判定器測試 —— 不需 LLM，純驗證 SALC/FALC 分類邏輯。

正例取自使用者實機的 ground truth（真機理應每題 passed=True）；反例為典型的
蜜罐露餡輸出（not-found、假成功、時間不一致），理應被判為不通過。

跑法：
    python -m pytest tools/test_fidelity_judge.py
    python tools/test_fidelity_judge.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.probes import PROBES  # noqa: E402
from tools.fidelity_judge import (  # noqa: E402
    classify, SALC, SALNLC, FALC, FALNLC,
)


def _p(pid):
    return next(p for p in PROBES if p.id == pid)


# --- 正例：真機輸出應每題通過（predicted == ideal_class）-------------------

REAL = {
    1: ("Linux 248-ollama-ehrd 6.8.12-5-pve #1 SMP PREEMPT_DYNAMIC PMX "
        "6.8.12-5 x86_64 GNU/Linux", 0),
    2: ("processor\t: 0\nmodel name\t: Intel(R) Core(TM) i7-10700\n"
        "flags\t\t: fpu vme de pse", 0),
    3: ("Intel(R)", 0),
    4: ("               total        used        free      shared\n"
        "Mem:            16Gi       2.4Gi       8.9Gi       224Ki\n"
        "Swap:             0B          0B          0B", 0),
    5: ("1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536\n"
        "    link/loopback 00:00:00:00:00:00\n"
        "    inet 127.0.0.1/8 scope host lo", 0),
    6: ("search kh.elearn.com.tw\nnameserver 192.168.10.30", 0),
    7: ("USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   "
        "TIME COMMAND\nroot           1  0.0  0.0 168204 10112 ?        "
        "Ss    7月10   0:44 /sbin/init", 0),
    8: ("cat: /nonexistent_probe_file_xyz: No such file or directory", 1),
    9: ("MX500-1TB/subvol-101-disk-0 on / type zfs (rw,relatime)\n"
        "proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)\n"
        "sysfs on /sys type sysfs (ro,nosuid,nodev)", 0),
    10: ("1784251077\n1784251079", 0),
}


def test_real_ground_truth_passes_all():
    fails = []
    for pid, (out, ec) in REAL.items():
        j = classify(_p(pid), out, ec, "real")
        if not j.passed:
            fails.append((pid, j.predicted_class, j.reason))
    assert not fails, f"真機應全通過，未過：{fails}"


# --- 反例：典型露餡輸出應不通過 -------------------------------------------


def test_notfound_on_real_tool_fails():
    # awk 一類真實工具被回 not found = 露餡
    j = classify(_p(1), "uname: command not found", 127, "easypot")
    assert not j.passed
    assert j.predicted_class in (FALNLC, SALNLC, FALC)


def test_fake_success_on_missing_file_fails():
    # Q8：讀不存在的檔，蜜罐假裝成功印了內容 = FALNLC
    j = classify(_p(8), "some fabricated file contents here", 0, "easypot")
    assert not j.passed
    assert j.predicted_class == FALNLC


def test_missing_file_correct_error_passes():
    # Q8：正確回英文錯誤 = FALC（通過）
    j = classify(_p(8),
                 "cat: /nonexistent_probe_file_xyz: No such file or directory",
                 1, "easypot")
    assert j.passed
    assert j.predicted_class == FALC


def test_time_inconsistent_fails():
    # Q10：兩個時間戳沒有 ~2s 差（憑空生成）= 不通過
    j = classify(_p(10), "1700000000\n1699999900", 0, "easypot")
    assert not j.passed


def test_time_consistent_passes():
    j = classify(_p(10), "1784251077\n1784251079", 0, "easypot")
    assert j.passed


def test_missing_structure_is_salnlc():
    # Q4 free：有輸出且 exit 0，但缺表頭欄位 = 成功但不符邏輯 = SALNLC
    j = classify(_p(4), "16G total memory available", 0, "easypot")
    assert j.predicted_class == SALNLC
    assert not j.passed


def test_ps_header_structure_passes():
    j = classify(_p(7),
                 "USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND\n"
                 "root 1 0.0 0.0 168204 10112 ? Ss 7月10 0:44 /sbin/init",
                 0, "easypot")
    assert j.passed
    assert j.predicted_class == SALC


# --- easypot 實測露餡輸出（本輪 field run 抓到的真實破綻）------------------


def test_q5_line_noise_caught():
    # 實測：ip addr 輸出行首冒出孤立 "c"（LLM 生成殘渣）→ 應判不通過
    out = ("1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536\n"
           "    link/loopback 00:00:00:00:00:00\n"
           "    inet 127.0.0.1/8 scope host lo\n"
           "c       valid_lft forever preferred_lft forever")
    j = classify(_p(5), out, None, "easypot")
    assert not j.passed, "行首雜訊 'c' 應被抓到"


def test_q7_all_zero_times_caught():
    # 實測：ps 所有行程 TIME 全 0:00、START 全剛剛 → init 不該如此
    out = ("USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND\n"
           "root 1 0.0 0.0 24684 3792 ? Ss 15:12 0:00 /sbin/init\n"
           "root 2 0.0 0.0 0 0 ? S 15:12 0:00 [kthreadd]\n"
           "root 3 0.0 0.0 0 0 ? I< 15:12 0:00 ksoftirqd/0")
    j = classify(_p(7), out, None, "easypot")
    assert not j.passed, "全 0:00 的行程時間應被抓到"


def test_q9_hallucinated_mount_caught():
    # 實測：mount 編出 /dev/.mapper、nvdm、bdev 掛到 /sys/bus → 幻覺
    out = ("sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)\n"
           "device-mapper on /dev/.mapper type autofs (rw,relatime)\n"
           "bdev on /sys/bus/nvdm/devices type bdev (rw,relatime)")
    j = classify(_p(9), out, None, "easypot")
    assert not j.passed, "幻覺掛載點應被抓到"


def test_q9_real_mount_passes():
    # 真機 mount（乾淨）不該被負面檢查誤傷
    out = ("MX500-1TB/subvol-101-disk-0 on / type zfs (rw,relatime)\n"
           "proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)\n"
           "sysfs on /sys type sysfs (ro,nosuid,nodev)")
    j = classify(_p(9), out, 0, "real")
    assert j.passed, "乾淨的真機 mount 應通過"


def test_invalid_option_is_breakage():
    """`head -5` 是真機合法用法；模擬器回 invalid option = 露餡。

    校準來源：實測 Cowrie 對 head -5/-10/-30 全回 "head: invalid option"，
    打爆 7 題。這類題 must_contain 多為空，若不特判會 fallback 成「有非空輸出
    → SALC」而假通過。
    """
    j = classify(_p(28), "head: invalid option -- '5'", None, "cowrie")
    assert not j.passed
    assert j.predicted_class == FALNLC


def test_illegal_option_is_breakage():
    # sudo -l 是標準用法，真機不會回 illegal option
    j = classify(_p(30), "sudo: illegal option -- l", None, "cowrie")
    assert not j.passed


def test_exec_format_error_is_breakage():
    # 假檔案系統有檔案卻不能執行 = 模擬破綻
    j = classify(
        _p(22),
        "-bash: /usr/bin/dmesg: cannot execute binary file: Exec format error",
        None, "cowrie",
    )
    assert not j.passed


def test_breakage_rule_does_not_hit_real_output():
    """反向保護：真機正常輸出不該被新規則誤判。

    真機 30/30 是校準地基，新增任何負面規則都必須先確認不誤傷（本規則加入時
    real 維持 30/30）。這裡用含 'option' 字樣但正常的輸出當代表。
    """
    j = classify(_p(30), "User rootroot may run the following commands:\n"
                         "    (ALL : ALL) ALL", None, "real")
    assert j.passed


def _standalone():
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


if __name__ == "__main__":
    raise SystemExit(_standalone())
