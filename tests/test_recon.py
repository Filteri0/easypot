"""Tests for the info/recon builtins (batch 1 + 2).

batch 1 (simple info): uptime, free, which, groups, date, sleep, df, lscpu, ps
batch 2 (network recon): netstat, ifconfig, ip, arp, lspci

These are mostly output commands, so we pin: registration, a couple of stable
output markers per command, SystemProfile-driven consistency (free/lscpu/netstat
reflect the profile), and the two behaviours that reflect real state
(which -> registry, sleep -> validate-but-don't-block).

Runnable two ways:
    python -m pytest tests/test_recon.py
    python tests/test_recon.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from honeyshell.commands import (  # noqa: E402
    ShellContext,
    StringReader,
    StringWriter,
    discover,
    resolve,
)
from honeyshell.core.config import SystemProfile  # noqa: E402
from honeyshell.fs.build_sample_fs import build as build_sample_fs  # noqa: E402

discover()


def _ctx(system=None, username="root"):
    return ShellContext(fs=build_sample_fs(hostname="svr04"), cwd="/root",
                        username=username, system=system)


def _run(name, tail, ctx=None):
    ctx = ctx or _ctx()
    cls = resolve(name)
    assert cls is not None, f"{name} not registered"
    out, err = StringWriter(), StringWriter()
    code = asyncio.run(cls(ctx, [name, *tail], StringReader(""), out, err).run())
    return code, out.getvalue(), err.getvalue()


# --- registration --------------------------------------------------------


def test_all_registered():
    for name in ("uptime", "free", "which", "groups", "date", "sleep", "df",
                 "lscpu", "ps", "netstat", "ifconfig", "ip", "arp", "lspci"):
        assert resolve(name) is not None, name


# --- batch 1 -------------------------------------------------------------


def test_uptime_shows_load_average():
    _, out, _ = _run("uptime", [])
    assert "load average:" in out and "up" in out


def test_free_reads_profile_memory():
    prof = SystemProfile(hostname="svr04", memory_mb=2048)
    _, out, _ = _run("free", ["-m"], _ctx(system=prof))
    # total column reflects the profile (2048 MiB)
    assert "2048" in out
    assert "Mem:" in out and "Swap:" in out


def test_free_human_readable():
    prof = SystemProfile(hostname="svr04", memory_mb=8192)
    _, out, _ = _run("free", ["-h"], _ctx(system=prof))
    assert "Gi" in out


def test_which_resolves_registered_command():
    _, out, _ = _run("which", ["ls"])
    assert out.strip() == "/bin/ls"


def test_which_unknown_is_silent_nonzero():
    code, out, _ = _run("which", ["definitely-not-real"])
    assert out == "" and code == 1


def test_which_finds_vfs_tool_on_path():
    # §2: which now walks the emulated $PATH in the VFS, so tools that ship as
    # metadata-only binaries (python3/git/psql in /usr/bin) resolve — keeping
    # tool presence consistent with the LLM's "assume installed" behaviour.
    for tool, expect in (("python3", "/usr/bin/python3"),
                         ("git", "/usr/bin/git"),
                         ("psql", "/usr/bin/psql")):
        code, out, _ = _run("which", [tool])
        assert code == 0 and out.strip() == expect, tool


def test_which_registry_beats_vfs():
    # A registered builtin resolves via the registry (canonical /bin path),
    # not the VFS walk, even though /bin/ls also exists on disk.
    _, out, _ = _run("which", ["ls"])
    assert out.strip() == "/bin/ls"


def test_groups_root_vs_user():
    _, out_root, _ = _run("groups", [], _ctx(username="root"))
    assert out_root.strip() == "root"
    _, out_user, _ = _run("groups", [], _ctx(username="alice"))
    assert "sudo" in out_user


def test_date_default_and_format():
    _, out, _ = _run("date", [])
    assert len(out.strip()) > 0
    _, out2, _ = _run("date", ["+%Y"])
    assert out2.strip().isdigit()


def test_sleep_validates_but_returns_immediately():
    code, out, err = _run("sleep", ["5"])
    assert code == 0 and out == "" and err == ""


def test_sleep_bad_interval_errors():
    code, out, err = _run("sleep", ["abc"])
    assert code != 0 and "invalid time interval" in err


def test_sleep_missing_operand():
    code, out, err = _run("sleep", [])
    assert code != 0 and "missing operand" in err


def test_df_shows_root_mount():
    _, out, _ = _run("df", [])
    assert "/dev/sda1" in out and "Mounted on" in out


def test_lscpu_reads_profile():
    prof = SystemProfile(hostname="svr04", cpu_count=8,
                         cpu_model="AMD EPYC 7742")
    _, out, _ = _run("lscpu", [], _ctx(system=prof))
    assert "AMD EPYC 7742" in out
    assert "CPU(s):" in out and "8" in out


def test_ps_bare_and_full():
    _, out_bare, _ = _run("ps", [])
    assert "PID" in out_bare and "CMD" in out_bare
    _, out_full, _ = _run("ps", ["aux"])
    assert "/sbin/init" in out_full and "USER" in out_full


# --- batch 2 -------------------------------------------------------------


def test_netstat_reflects_open_ports():
    prof = SystemProfile(hostname="svr04", open_ports=[22, 443, 8080])
    _, out, _ = _run("netstat", ["-tlnp"], _ctx(system=prof))
    assert "0.0.0.0:22" in out
    assert "0.0.0.0:443" in out
    assert "0.0.0.0:8080" in out
    assert "LISTEN" in out


def test_ifconfig_shows_eth_and_lo():
    _, out, _ = _run("ifconfig", [])
    assert "eth0" in out and "lo:" in out
    assert "inet 10.0.0.24" in out


def test_ip_addr_and_route():
    _, out_a, _ = _run("ip", ["addr"])
    assert "eth0" in out_a and "10.0.0.24/24" in out_a
    _, out_r, _ = _run("ip", ["route"])
    assert "default via 10.0.0.1" in out_r


def test_ip_unknown_subcommand_is_quiet():
    code, out, _ = _run("ip", ["neigh"])
    assert code == 0 and out == ""


def test_arp_shows_neighbours():
    _, out, _ = _run("arp", ["-a"])
    assert "10.0.0.1" in out


def test_lspci_shows_gpu_when_profile_has_one():
    prof = SystemProfile(hostname="svr04", gpu="NVIDIA GeForce RTX 3090")
    _, out, _ = _run("lspci", [], _ctx(system=prof))
    assert "RTX 3090" in out


def test_lspci_no_gpu_by_default():
    _, out, _ = _run("lspci", [])
    assert "Host bridge" in out
    assert "RTX" not in out


# --- standalone runner ---------------------------------------------------


def _run_standalone() -> int:
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



# --- batch 3: top / mount / ping + MAC de-virtualization -----------------


def test_new_commands_registered():
    for name in ("top", "mount", "ping"):
        assert resolve(name) is not None, name


def test_top_header_consistent_with_uptime():
    code, out, _ = _run("top", [])
    assert code == 0
    assert out.startswith("top -")
    assert "load average: 0.08, 0.03, 0.01" in out
    assert "Tasks:" in out and "MiB Mem" in out
    assert "PID USER" in out


def test_top_memory_reflects_profile():
    prof = SystemProfile(hostname="svr04", memory_mb=2048)
    _, out, _ = _run("top", [], _ctx(system=prof))
    # 2048 MiB total shows up in the mem line.
    assert "2048.0 total" in out


def test_mount_lists_root_ext4():
    code, out, _ = _run("mount", [])
    assert code == 0
    assert "/dev/sda1 on / type ext4" in out
    assert "on /proc type proc" in out


def test_mount_agrees_with_proc_mounts():
    # mount just reformats /proc/mounts; the same device/target pairs appear.
    _, mout, _ = _run("mount", [])
    ctx = _ctx()
    _, cout, _ = _run("cat", ["/proc/mounts"], ctx=ctx)
    assert "/dev/sda1" in mout and "/dev/sda1" in cout


def test_ping_reports_success_stats():
    code, out, _ = _run("ping", ["-c", "3", "8.8.8.8"])
    assert code == 0
    assert "PING 8.8.8.8" in out
    assert "3 packets transmitted, 3 received, 0% packet loss" in out
    assert "rtt min/avg/max/mdev" in out
    assert out.count("icmp_seq=") == 3


def test_ping_requires_host():
    code, out, err = _run("ping", ["-c", "2"])
    assert code != 0 and "Destination address required" in err


def test_ping_count_capped():
    _, out, _ = _run("ping", ["-c", "999", "example.com"])
    # never emit an unbounded stream (cap = 20).
    assert out.count("icmp_seq=") == 20


def test_ifconfig_no_kvm_mac():
    _, out, _ = _run("ifconfig", [])
    assert "52:54:00" not in out          # QEMU/KVM OUI gone
    assert "00:1a:a0:3f:7c:12" in out     # bare-metal Dell OUI


def test_ip_and_ifconfig_share_mac():
    _, ifc, _ = _run("ifconfig", [])
    _, ipa, _ = _run("ip", ["a"])
    assert "00:1a:a0:3f:7c:12" in ifc
    assert "00:1a:a0:3f:7c:12" in ipa      # single source of truth



# --- package-manager AI-tell fixes (yum/dnf absent, no helpful-AI voice) --


def test_yum_dnf_command_not_found():
    for name in ("yum", "dnf"):
        code, out, err = _run(name, ["install", "foo"])
        assert code == 127, name
        assert f"bash: {name}: command not found" in err, name
        # The AI tell we're killing: no "using apt-get instead" helpfulness.
        assert "apt-get" not in (out + err).lower(), name
        assert "instead" not in (out + err).lower(), name


def test_which_reports_yum_dnf_absent():
    # `which yum` must agree the host doesn't ship it (else it contradicts the
    # `yum -> command not found` behaviour).
    for name in ("yum", "dnf"):
        code, out, _ = _run("which", [name])
        assert code == 1 and out.strip() == "", name


if __name__ == "__main__":
    raise SystemExit(_run_standalone())


def test_netstat_shows_attacker_own_ip():
    """netstat 的 established 連線應顯示攻擊者自己的 src_ip,而非硬編陌生 IP。"""
    ctx = _ctx()
    ctx.src_ip = "185.220.101.47"
    ctx.src_port = 51900
    _, out, _ = _run("netstat", [], ctx=ctx)
    assert "185.220.101.47:51900" in out
    assert "10.0.0.9" not in out  # old hardcoded stranger gone


# --- 擬真度探測抓到的破綻（回歸鎖定）-------------------------------------
# 以下三條對應題庫 Q10 / Q7 / Q2 的失分修復。這些破綻都是「輸出看起來合理、
# 但攻擊者一比對就露餡」的類型,單看程式碼不易察覺,靠 30 題探測才量出來。


def test_sleep_advances_emulated_clock():
    """Q10 (ATT&CK T1497 沙箱偵測):`date; sleep 2; date` 必須看到時間前進。

    sleep 不真的阻塞(會被攻擊者拿來佔住 session,本身也是 timing tell),
    但若時鐘完全不動,兩個時間戳會一模一樣 —— 真機不可能如此。
    """
    ctx = _ctx()
    before = ctx.now()
    _run("sleep", ["2"], ctx=ctx)
    assert ctx.time_offset == 2.0
    assert ctx.now() - before >= 2.0


def test_sleep_accepts_units_and_multiple_operands():
    ctx = _ctx()
    _run("sleep", ["1m"], ctx=ctx)
    assert ctx.time_offset == 60.0
    ctx2 = _ctx()
    _run("sleep", ["1", "2"], ctx=ctx2)   # GNU sleep 累加多個運算元
    assert ctx2.time_offset == 3.0


def test_sleep_rejects_bad_interval():
    code, _, err = _run("sleep", ["abc"])
    assert code != 0 and "invalid time interval" in err


def test_ps_aux_uses_bsd_header_not_sysv():
    """Q7:`ps aux` 是 BSD 格式,表頭必須有 COMMAND/STAT/RSS,不是 -ef 的 CMD/PPID。

    先前實作把 aux 與 -ef 混為一談,`ps aux | head -5` 少了攻擊者會 grep 的
    COMMAND 欄 —— ps aux 是最常見的偵察命令之一,錯了代價很高。
    """
    _, out, _ = _run("ps", ["aux"])
    header = out.splitlines()[0]
    for col in ("USER", "%CPU", "%MEM", "VSZ", "RSS", "STAT", "COMMAND"):
        assert col in header, f"ps aux 表頭缺 {col}: {header}"
    assert "PPID" not in header  # 那是 -ef 的欄位


def test_ps_ef_keeps_sysv_header():
    _, out, _ = _run("ps", ["-ef"])
    header = out.splitlines()[0]
    for col in ("UID", "PID", "PPID", "STIME", "CMD"):
        assert col in header, f"ps -ef 表頭缺 {col}: {header}"


def test_ps_processes_have_accumulated_cpu_time():
    """全部行程 TIME 都是 0:00 也是破綻:真機長跑的 init/journald 會累積 CPU 時間。"""
    _, out, _ = _run("ps", ["aux"])
    times = [ln.split()[9] for ln in out.splitlines()[1:] if len(ln.split()) > 9]
    assert any(t != "0:00" for t in times), f"所有 TIME 皆為 0:00: {times}"


def test_cpuinfo_has_flags_field():
    """Q2:攻擊者會 grep /proc/cpuinfo 的 flags(查 hypervisor/AES-NI/AVX)。"""
    ctx = _ctx()
    _, out, _ = _run("cat", ["/proc/cpuinfo"], ctx=ctx)
    assert "flags" in out and "fpu" in out
    for field in ("cpu family", "stepping", "bogomips", "cache size"):
        assert field in out, f"/proc/cpuinfo 缺 {field}"


def test_sudo_list_privileges():
    """Q30:`sudo -l` 是標準權限枚舉(ATT&CK T1069),必須列出 sudoers 摘要。

    先前 sudo 把 `-l` 當成「要用 root 執行的命令」,產出
    `bash: -l: command not found` —— 真機不可能如此,是明顯破綻。
    """
    code, out, _ = _run("sudo", ["-l"])
    assert code == 0
    assert "may run the following commands" in out
    assert "(ALL : ALL) ALL" in out
    assert "command not found" not in out


def test_sudo_flag_forms_do_not_execute_flags():
    """-V/-h/-k 都不該被當成命令執行。"""
    for flag in ("-V", "-h", "-k"):
        code, out, err = _run("sudo", [flag])
        assert "command not found" not in (out + err), flag
    _, out, _ = _run("sudo", ["-V"])
    assert "Sudo version" in out


def test_sudo_still_runs_real_commands():
    """回歸保護:修 flag 處理不能破壞 `sudo <cmd>` 的正常執行路徑。"""
    code, out, _ = _run("sudo", ["whoami"])
    assert "command not found" not in out
