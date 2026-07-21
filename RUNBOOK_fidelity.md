# RUNBOOK — 擬真度實驗（目標一）從零到定稿

三方對照：**real（真機基準）/ easypot / Cowrie**，同一份 30 題（`tools/probes.py`）、
同一個判定器（`tools/fidelity_judge.py`）。產出報告核心表。

> **資料檔不進 git/tar**：`tools/ground_truth.txt`、`cowrie_out.txt` 是實驗資料，
> 每次更新程式碼 tar 都不含它們，需自行採集（本文件步驟 1、2）。若 run_probes 報
> `FileNotFoundError: tools/ground_truth.txt`，就是還沒跑步驟 1。

---

## 前置

| 需求 | 位置 | 說明 |
|---|---|---|
| Ollama + qwen2.5:14b | Linux 那台 | easypot 欄要打 LLM |
| Cowrie | 任一台（Docker 即可） | 步驟 2 用 |
| 真 Linux | 任一台（PVE 主機可） | 步驟 1 用，**非蜜罐** |

```bash
cd ~/easypot
pip install -e '.[transport,dev]'
python -m pytest -q          # 應 487 passed（+2 skip 是尚未採集 ground truth）
```

---

## 步驟 1：採集 real 基準（ground_truth.txt）

在**真 Linux**上跑。腳本已強制 `LC_ALL=C`，輸出 canonical 英文，與蜜罐模擬的英文
VPS 對齊（不加會因 zh_TW 翻譯 `df`/`ls` 欄位而被誤判失分）。

```bash
cd ~/easypot
bash tools/capture_ground_truth.sh > tools/ground_truth.txt 2>&1
```

**立刻驗證校準**（這步是地基，沒過就不要往下走）：

```bash
python -m pytest tests/test_fidelity_calibration.py -q
# 應 2 passed（不是 skipped）
```

> 這條測試斷言真機在**每一題**都通過。real 是量尺本身，定義上必須 100% 通過自己
> 的題；任一題失分代表**判定門檻壞了**（不是真機露餡），要修 probes/judge 而非
> 改資料。

快速確認語系正確：

```bash
grep -m1 Filesystem tools/ground_truth.txt   # 有輸出 = 英文，正確
```

---

## 步驟 2：採集 Cowrie（cowrie_out.txt）

Cowrie 跑在哪台都行，`capture_cowrie.py` 從外面用 SSH 打 30 題。

**2a. 啟動 Cowrie**（若還沒跑）

```bash
docker run -d --name my-cowrie -p 22222:2222 cowrie/cowrie:latest
```

**2b. 採集**（在連得到 Cowrie 的機器上）

```bash
python -m tools.capture_cowrie --host localhost --port 22222 \
    --user rootroot --password 0000 \
    --out cowrie_out.txt --verbose
```

- Cowrie 在別台 → `--host <那台IP>`（記得放行防火牆）
- 在 Windows 上跑 → 需 `pip install asyncssh`，且要帶著 `tools/probes.py`
  （腳本會 import 題庫），跑完把 `cowrie_out.txt` 傳回 Linux
- 出現 `⚠ 這些題收到空輸出` → 手動 SSH 進去打那題確認：**Cowrie 真的回空**（照實
  記，算它失分）還是**抽取邏輯漏接**（工具 bug，要修）。兩者意義完全不同，別把
  自己的 bug 當成對手的失分。

**2c. 確認檔案在 Linux 那台**

```bash
ls -l cowrie_out.txt && grep -c '===Q' cowrie_out.txt   # 應為 30
```

---

## 步驟 3：產出三欄對照表（定稿）

需要 Ollama 在跑（easypot 欄）。

```bash
curl -s localhost:11434/api/tags > /dev/null && echo "ollama OK"

python -m tools.run_probes \
    --ground-truth tools/ground_truth.txt \
    --cowrie cowrie_out.txt \
    --repeat 10 \
    --out fidelity_table.md \
    --detail-out fidelity_detail.md
```

- `--repeat 10`：easypot 走 LLM 有隨機性，跑 10 次取通過率；real / cowrie 是靜態
  輸出，判一次即定（`--repeat` 不影響那兩欄）。
- 30 題 × 10 次 ≈ 300 次 LLM 呼叫，依機器約需數分鐘。
- 加 `--verbose` 可看逐題進度。

**先驗管線再燒 LLM**（可選，不連 LLM）：

```bash
python -m tools.run_probes --ground-truth tools/ground_truth.txt \
    --cowrie cowrie_out.txt --dry-run
```

---

## 產出物

| 檔案 | 內容 |
|---|---|
| `fidelity_table.md` | 三欄對照表（報告核心表） |
| `fidelity_detail.md` | 逐題實際輸出與判定理由（附錄／檢查失分用） |

---

## 判讀重點

**1. real 必須 30/30。** 不是就停下修判定器，別動資料。

**2. easypot 欄測的是「LLM 補盲層」，不是攻擊者實際體驗。**
runner 直接呼叫 `ChainResolver.resolve()`，而 `resolve()` 內部只有 `cache → LLM`，
**不查 registry**——所以 30 題全被強制走 LLM，繞過 61 個內建命令。但這 30 題多數
有內建實作，攻擊者實際連進來走的是內建路徑。

故此表 = **「假設全部 miss」的最壞情況壓力測試**，是 easypot 的**下界**。報告要
講清楚，否則會低估自己的系統。（實測範例：Q5 `ip addr`、Q16 `lscpu` 在此表 0/10，
但走內建路徑輸出完整正確。）

**3. hit/miss ≠ 擬真度。** hit/miss（目標二）是 easypot 內部「規則接住 vs 掉到
LLM」的架構指標；Cowrie 無 LLM 補盲層，不對等。與 Cowrie 比的是**擬真度**
（SALC/FALC），這把尺同時涵蓋「支不支援該命令」與「支援時像不像真機」。

**4. 判定器對兩邊一視同仁。** 「模擬器壞掉」規則（`invalid option` /
`cannot execute binary file` 等）對 easypot 與 Cowrie 同樣適用。加嚴後分數下降是
好事——誠實數字比虛高數字有說服力。

---

## 已知基準（校準後）

- **real 30/30**
- **Cowrie 15/30（50%）**，四類結構性破綻：
  | 類別 | 題數 | 代表 |
  |---|---|---|
  | `head -N` 不支援 | 6 | Q2/Q3/Q7/Q13/Q23/Q28 |
  | 假檔案系統不能執行 | 3 | mount / df / dmesg |
  | 工具根本沒有 | 1 | `ip addr` |
  | 罐頭輸出細節不對 | 5 | os-release 空、`ls` 缺 `total`、`lscpu` 缺 Model name、`sudo -l` illegal option、`date +%s` 不支援 |
- **easypot**：LLM-only 路徑，跑完填入。

---

## 疑難排解

| 症狀 | 原因 / 處理 |
|---|---|
| `FileNotFoundError: tools/ground_truth.txt` | 沒跑步驟 1（更新 tar 不含實驗資料） |
| 校準測試 skipped 而非 passed | 同上，`ground_truth.txt` 不存在 |
| 校準測試 FAIL | 判定門檻壞了。看失敗訊息的題號與理由，修 `probes.py` / `fidelity_judge.py`，**不要改 ground truth** |
| ground_truth 出現中文欄位 | 用了舊版 capture 腳本（無 `LC_ALL=C`），重採 |
| easypot 欄全空 | Ollama 沒跑或 `--base-url` 不對 |
| Cowrie 欄全空 | `--cowrie` 路徑錯，或檔案格式不符（應含 30 個 `===Q<id>===`） |
