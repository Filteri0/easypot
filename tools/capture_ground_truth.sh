#!/usr/bin/env bash
# capture_ground_truth.sh — 在「真 Linux」上採集 30 題探測命令的真實輸出，
# 作為擬真度題庫（目標一）的 ground truth。
#
# 用法：
#   在一台乾淨的真實 Linux（實機或乾淨 Ubuntu VM/容器，非蜜罐）上：
#     bash capture_ground_truth.sh > ground_truth.txt 2>&1
#   然後把 ground_truth.txt 放到 tools/ground_truth.txt（校準測試會讀它，
#   見 tests/test_fidelity_calibration.py）。
#
# 設計：每題以 "===Q<id>===" 分隔，方便機器解析。我們要的是「真機長什麼樣」的
# 結構與格式（欄位、表頭、錯誤字串），不是你機器的具體數值——所以跑在哪台真 Linux
# 都可以，數值不同不影響判定（判定看格式/結構/OS 邏輯，非數值相等）。
#
# 題目的來源與考點見同工具的 probes.py（每題標了 ATT&CK 編號 / 來源 / 考點 /
# 是否預期 easypot 會輸）。出題與受測系統隔離，且主動納入 easypot 預期會輸的題。
#
# ⚠️ locale（重要，校準關鍵）：蜜罐模擬的目標系統是**英文 VPS**——判定器門檻、
# easypot 與 Cowrie 的輸出全都是英文。若採集機是 zh_TW 等非英文 locale，df/ls 等
# 命令會**翻譯欄位標籤**（「檔案系統」「掛載點」「總用量」、月份「7月」），導致
# 真機被英文判定門檻誤判為露餡（SALNLC）。故本腳本強制 LC_ALL=C，讓輸出 canonical
# 英文、與受測系統對齊。這是「real 在報告表默默失分」那個 bug 的根因修復。

set +e  # 有些命令可能不存在/報錯，那正是我們要記錄的真機行為

# 強制英文 locale（見上方 locale 說明）。務必在任何命令之前設定。
export LC_ALL=C
export LANG=C

run() {
  local id="$1"; shift
  echo "===Q${id}==="
  echo "\$ $*"
  "$@"
  echo "===EXIT:$?==="
  echo
}

run_sh() {  # 需要 shell 語法（pipe / 重導）的題
  local id="$1"; shift
  echo "===Q${id}==="
  echo "\$ $*"
  bash -c "$*"
  echo "===EXIT:$?==="
  echo
}

echo "### ground truth captured on: $(uname -a)"
echo "### date: $(date -u)"
echo

# Q1  T1082 系統資訊：uname -a（格式擬真：欄位順序與數量）
run 1 uname -a

# Q2  T1082 系統資訊：cat /proc/cpuinfo 前 30 行（真機關鍵欄位存在性）
run_sh 2 "cat /proc/cpuinfo | head -30"

# Q3  T1082 系統資訊 + pipe（真實流量高頻 idiom；考跨工具管線一致性）
run_sh 3 "cat /proc/cpuinfo | grep 'model name' | head -1 | awk '{print \$4}'"

# Q4  T1082 記憶體資訊：free -h（表頭格式、單位）
run 4 free -h

# Q5  T1016 網路組態：ip addr（介面/位址格式；Table 7 提到的 recon）
run 5 ip addr

# Q6  T1016 網路組態：cat /etc/resolv.conf（Table 7 明列的 DNS 探測）
run 6 cat /etc/resolv.conf

# Q7  T1057 行程探索：ps aux | head（表頭欄位、USER/PID/…順序）
run_sh 7 "ps aux | head -5"

# Q8  指紋思維[30]：讀不存在的檔 → 真機精確錯誤字串（考錯誤擬真，
#     easypot 可能過度熱心不報錯 → 預期可能輸）
run 8 cat /nonexistent_probe_file_xyz

# Q9  T1497 沙箱/蜜罐偵測：mount | head（真機掛載表；蜜罐常露餡）
run_sh 9 "mount | head -10"

# Q10 跨命令狀態一致性（§6 process model；easypot 預期會輸）：
#     連續兩次 date +%s 之間 sleep 2，真機第二個時間戳應比第一個大 ~2。
#     考蜜罐能否維持時間/狀態一致，不是憑空生成。
run_sh 10 "date +%s; sleep 2; date +%s"

# ===== 擴充題 Q11–Q30 =====
run 11 id
run 12 whoami
run_sh 13 "cat /etc/passwd | head -5"
run 14 uptime
run 15 df -h
run 16 lscpu
run 17 env
run 18 netstat -tlnp
run 19 crontab -l
run 20 cat /etc/os-release
run 21 ls -la /root
run_sh 22 "dmesg | head -10"
run_sh 23 "cat /proc/meminfo | head -5"
run_sh 24 "ls -la /tmp; touch /tmp/probe_marker; ls -la /tmp"
run 25 hostname
run 26 cat /etc/shadow
run 27 w
run_sh 28 "last | head -5"
run 29 cat /proc/version
run 30 sudo -l

echo "### done. 請把整份輸出回傳。"
