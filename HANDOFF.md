# HANDOFF — easypot（honeyshell）專案交接（合併版 v6）

> 這份取代所有舊 HANDOFF（v1–v5）。讀完這一份就能無縫接手，不需回溯先前對話或舊交接。
> Repo: https://github.com/Filteri0/easypot（使用者自行同步）。
>
> **⚠️ 最新進度在 §35–§39（v6 增補）**，v5 增補在 §24–§34。
> **測試 465 → 487 passed, 1 skipped**（命令數 60 → 61）。
> **✅ §30 的「GPU 未啟用」已證實為誤判並更正（見 §36.4）**：GPU 從頭正常，延遲真根因
> 是 LLM 輸出長度；營運設定（keep-alive）已入 RUNBOOK §2.1.1。**接手勿再照 §30 修 GPU。**
> 導覽：最新一輪 → **§35–§39**（awk / DeferToLLM / 時間注入修復 / GPU 更正 / 擬真度題庫）；
> v5 這輪 → §24–§34；要跑實驗 → **先看 RUNBOOK.md**（§27）+ §38；
> 報告要證明什麼 → §21 + §28 現況數字 + §37.5 擬真度洞察；概念釐清（hit/miss vs 品質）→ §32；
> Docker 部署 → §26；架構/命令/設計 → §2–§12（仍有效）。

---

## 0. 一句話

用 **Python + asyncssh + asyncio** 復刻 Cowrie 的 shell 部分，抽成乾淨架構，
整合 **HoneyGPT 論文**（LLM 生成回應 + SR/H/FL 記憶 + Memory Pruning），
本地用 **Ollama（qwen2.5:14b）**。目前是**功能完整的互動式 SSH 蜜罐 + 完整實驗
工具鏈 + 雙台 Docker 部署**：**61 個內建命令**、LLM 動態內容生成、互動式憑證捕獲、
命令替換、fd 重導向、子 shell 隔離、tab 補全、Docker 資料鏈（雙台 host1/host2 共享
LLM 池 + collector）、真實流量 replay 分流、稽核聚合 analyzer（miss rate + 情報 +
LLM 成本對照 §4.6）。**測試全綠（487 passed, 1 skipped；本地有 Ollama 時 488）。**
**已用真實 Cowrie 資料跑到 46%，miss rate 收斂於 11.26%（見 §28）。**

> ⚠️ **接手先讀 v6（§35 起）**：v6 補了 awk 內建（命令數 **60 → 61**）+ DeferToLLM
> 機制、修復 resolver 時間注入缺陷、**更正了 §30 的 GPU 誤判**（GPU 一直正常，延遲
> 真根因是輸出長度，別再照 §30 修 GPU），並建置擬真度題庫（目標一）。§0 以下多數
> 章節維持 v5 狀態，數字以 v6（§35-39）為準。

### 定位（多輪討論過的結論，接手者該知道）
- **安全模型正確**：攻擊者命令**不在真實 OS 執行**（都經 parser → 規則模擬或 LLM
  生成假輸出），本地 Ollama 無資料外送。grep `eval|exec(|os.system|subprocess`
  應乾淨——這是「假 shell 安全、真系統危險」的分界，本專案站在安全側。
- **互動層級**：不是純高互動，是 **規則為主（60 命令，毫秒級）+ LLM 補盲** 的混合。
- **能騙到誰**：自動化腳本/低階攻擊者 → 能，且比 Cowrie 留得久（論文貢獻點）；
  高階針對性攻擊者 → 現階段任何 LLM 蜜罐都騙不過（timing、跨命令一致性、角色測試），
  但**被識破前收集的行為本身就是情報**。定位是「研究級混合蜜罐」，適合**隔離環境
  做威脅情報 POC**，不是主力防禦資產。
- **實務部署前提**：必須網路隔離（獨立 VLAN/DMZ、封 outbound 到內網），因為蜜罐是
  故意被打的機器，爆炸半徑要限制。這是部署層的事，非本專案程式範疇。

### 報告脈絡（重要，v4 補充）
**本專案是實習計畫的最後一步，報告受眾是實習主管，不是論文審稿人。** 報告主軸是
「這一個月我學到什麼、如何規劃、做出什麼成果」，不是「這個蜜罐學術上多強」。因此
工具鏈（analyzer/replay）的價值在於**把成果變成可展示的數字**：混合架構的 miss rate
（證明設計取捨聰明）、情報產出（證明理解蜜罐的目的）。詳見 §21。

---

## 1. 使用者約束（務必遵守）

- **語言**：Python，核心 **asyncssh + asyncio**。**不擅自換技術**，要換先解釋理由。
- **LLM**：本地 **Ollama**，預設模型 **qwen2.5:14b**，HTTP 用 **httpx**（惰性 import）。
- **回覆語言**：預設**繁體中文**，精簡、技術、實務導向。
- **工作節奏**：**一次一個 module / 一批**。完成後：1) 說明修改 2) 提供測試方式
  3) **停下等使用者指示**。寫 code 前先給架構 / 實作計畫，等確認。
- **交付慣例**：每輪同時給 (a) 完整 `easypot.tar.gz`，(b) 該輪新增/修改的每一支檔
  （含 `__init__.py` 與被小改的檔）。**別漏 `__init__.py`**（早期出過包）。
- **基準紀律（重要）**：以**使用者最新上傳的 tar** 為唯一真實來源。接手前先解壓、
  `pip install -e '.[transport,dev]'`、`pytest` 對數量，不確定就請使用者重新上傳。
  使用者也會自己動手改 code，別假設檔案內容跟你上次離開時一樣。
  **注意**：git repo 通常嚴重落後 tar（曾見 git 停在早期 commit），**別看 git，看 tar**。
- **每輪交付前跑到綠**。測試失敗先判斷「測試預期過時」還是「程式 bug」——兩者都常遇到。

---

## 2. 架構全貌與模組狀態（全部 ✅）

```
easypot/
├── pyproject.toml            # 專案根（早期曾遺失/錯位，現已就位）
├── honeyshell/
│   ├── __main__.py           ✅ python -m honeyshell 啟動；--llm/--hostname/--port/--fs/--audit-jsonl...
│   ├── analyze.py            ✅ 【v4】稽核聚合器：讀 _merged.jsonl → miss rate/session/情報
│   ├── replay_cowrie.py      ✅ 【v4】Cowrie input.csv replay bridge：真實流量餵蜜罐
│   ├── core/                 ✅ 設定 + 稽核事件匯流排（零外部相依）
│   │   ├── config.py         #   Principles(P)/SystemProfile(S)/LLMSettings/MemorySettings
│   │   ├── events.py         #   Event 階層（Session/Login/Command/Download/LLM/Error）
│   │   └── event_bus.py      #   EventBus（同步 pub/sub）+ LoggingSink + JSONLSink
│   ├── backends/             ✅ LLM 後端（httpx 惰性 import）
│   │   ├── client.py         #   LLMClient 協定 + OllamaClient（json_format 可切）
│   │   ├── prompt_builder.py #   Question Enhancement（三子問 CoT + Table1）+ 冷酷 bash 約束
│   │   ├── cache.py          #   ResponseCache（命令模擬用）
│   │   ├── resolver.py       #   ChainResolver：cache→LLM hybrid + emit LLMEvent
│   │   ├── llm_command.py    #   LLMCommand：把 (A,C,F) 包成 Command
│   │   ├── fs_applier.py     #   C_i 回寫 VFS（LLM 說建檔就真的建）
│   │   └── content_fetcher.py ✅ curl/wget stdout 內容 LLM 生成（session cache）
│   ├── memory/               ✅ 多輪記憶 + Memory Pruning（零外部相依）
│   │   ├── session_memory.py #   SessionMemory：SR/H/FL 三平行結構
│   │   └── pruner.py         #   Weaken Factor(0.8) 衰減 + 按最小 F 裁剪
│   ├── commands/             ✅ 命令框架（借鑑 Cowrie）+ 60 內建命令（一檔一命令）
│   │   ├── base.py context.py registry.py streams.py
│   │   └── impl/             #   見 §3 命令清單；_ 開頭是共享 helper（不註冊）
│   ├── fs/                   ✅ 虛擬檔案系統（JSON，非 pickle）
│   │   ├── filesystem.py     #   VirtualFS；chmod/chown/access(權限)/clock/shift_mtimes
│   │   ├── loader.py import_cowrie.py build_sample_fs.py
│   ├── shell/                ✅ 直譯器 + 語言處理
│   │   ├── parser.py         #   結構解析 + fd 重導向（2>/2>&1/>&/&>）
│   │   ├── expand.py         #   $VAR/${VAR}/$?/~ 展開
│   │   ├── cmdsubst.py       #   $(...)/反引號 命令替換（pre-parse pass）
│   │   ├── shell_builtins.py #   賦值/no-op builtin/控制關鍵字「止血層」
│   │   └── interpreter.py    #   parse→cmdsubst→展開→dispatch→pipeline/重導向→VFS
│   ├── transport/            ✅ SSH 前端
│   │   ├── config.py terminal.py session.py
│   │   ├── completion.py     ✅ 【v3 漏記→v4 補】tab 補全（命令名 + VFS 路徑），純函式
│   │   └── ssh_server.py     #   唯一 import asyncssh；建 resolver/content_client/event_bus
│   │                         #   + 傳 src_ip/src_port 給 session（netstat 用）
│   └── data/fs.json          # DB 人設，已含 /proc/*、apt-get 工具（v3 重生）
├── deploy/                   ✅ 【v3】Docker 部署（2 蜜罐 + collector）
│   ├── Dockerfile docker-compose.yml README.md
│   └── collector/collect.py Dockerfile
└── tests/                    # 全部雙模式（pytest 或 python tests/xxx.py）
```

**測試現況：440 passed, 1 skipped（本地有 Ollama server 時 ollama_integration 那條會跑，共 441）。**

---

## 3. 內建命令清單（61 個，一檔一命令）— v6：+awk（見 §36.1）

- **基礎**：echo pwd whoami true false cd cat exit(=logout) ls
- **檔案系統（改 VFS）**：mkdir rmdir rm touch mv cp
- **系統資訊**：uname id hostname env
- **文字處理**：head tail wc grep **awk**（awk 只內建 `{print $N}` 子集，複雜語法
  DeferToLLM，見 §36.1/§36.2；含 gawk alias）
- **下載類**：wget curl tftp ftpget（走內建，C_i 回寫 VFS；curl/wget 的 stdout 路徑
  接 LLM 生成內容，存檔路徑用 placeholder；curl `-I` 短路 HTTP headers 不落 body）
- **shell**：sh(=bash=dash)（-c / pipe-in / script 檔；子 shell 隔離 exit 與 cwd）
- **資訊/偵察**：uptime free which groups date sleep df lscpu ps netstat ifconfig ip
  arp lspci stat **top mount ping**（讀 SystemProfile 保持一致；which 接 registry 再查
  VFS $PATH；date/uptime/top 讀模擬時鐘；netstat 顯示攻擊者自己的 src_ip；sleep/ping
  不真阻塞）
- **權限/持久化**：chmod chown sudo su passwd crontab（sudo/su/passwd 互動問密碼、
  echo-off、憑證 emit 到 event bus）
- **檔案處理**：sort cut sed(只 s///) find dd tar mktemp
- **不存在但正確回報**：**yum/dnf**（Debian 本就沒有，寫死 `command not found`，
  `absent_from_path=True` 讓 which 一致）

共享 helper（`_` 開頭，discover 匯入但不註冊）：`_download _fileorstdin _fsflags
_sysprofile _credentials _netinfo`。

> v2→v4 命令數演進：55（v2）→ 56（stat）→ +top/mount/ping/yum（v3）= 60。

---

## 4. 關鍵設計決策（別推翻，除非有更好理由）

### 早期奠定（仍有效）
1. **fs 用 JSON 不 pickle**：runtime 永不 unpickle。`import_cowrie.py` 是唯一碰 pickle 處。
2. **coroutine 呼叫堆疊取代 Cowrie cmdstack**：互動命令直接 `await`。
3. **command 框架借鑑 Cowrie**：`@register("ls","/bin/ls")` + `discover()` 掃 impl/。
   **registry miss = LLM 接點**（miss_handler）。
4. **transport 分層**：ShellSession 傳輸無關；asyncssh 只在 ssh_server；惰性載入。
5. **權限儲存但不強制（advisory）**：VFS 是 mechanism，存取控制是 command/interpreter 的 policy。
6. **相依隔離**：httpx 只在 backends、asyncssh 只在 transport，core/memory 零外部相依。
   **v4 延伸**：analyze.py 純 stdlib、replay_cowrie 解析層純 stdlib（asyncssh 惰性）。
7. **LLM 韌性**：LLM 掛掉 → 降級 command not found / placeholder，**蜜罐永不 crash**。

### HoneyGPT 整合
8. **內建 vs LLM 分工**：確定性、會改 VFS 的常見命令 → 內建（真改 VFS 保一致）；
   多樣、沒看過的 → LLM。**這個分工正是 miss rate 要量化的對象（§21）。**
9. **C_i 回寫 VFS**：LLM 回結構化 fs_ops，`fs_applier` 套用到 VirtualFS。
10. **SessionMemory 三平行 list（H/SR/FL）**：貼合論文；pruning 按 index 砍最小 F。
11. **Weaken Factor w=0.8**：論文推導 (0.623,1]，使三步前高權限命令權重 > 新命令。

### 命令 / 互動層（12 輪）
12. **一檔一命令**：`impl/` 每個命令獨立檔，`_` 開頭 helper 不註冊。可單獨改、一目了然。
13. **ctx 的窄介面模式**：需要跨層能力時，在 `ShellContext` 掛一個 callable 欄位，
    由 transport/interpreter 綁定，命令透過它取用。已用此模式加了：
    - `run_line`：sh 遞迴執行子命令（同一 interpreter，共享狀態 + miss_handler）
    - `fetch_content`：curl/wget stdout 內容 LLM 生成
    - `read_prompt`：互動式讀一行（sudo/su/passwd 問密碼），支援 echo-off
    - `event_bus`：憑證捕獲 emit LoginEvent
    - `shell_depth`：子 shell 遞迴深度守衛（上限 8）
14. **下載內容分場景**：stdout 路徑走 LLM 生成、存檔路徑用 placeholder、無 LLM 全退回
    placeholder。ContentFetcher 的 cache 是 **session-scoped**（同 URL 同 session 一致；
    跨 session 會重新生成——這是刻意的）。
15. **子 shell 隔離**：sh 執行子 script 時，`exit`/`logout` 與 `cd` 只在子 shell 內有效。
16. **互動憑證捕獲**：sudo/su/passwd 走完整真實流程（問密碼、echo-off、確認），驗證永遠
    通過（讓攻擊者成功以觀察後續），密碼 emit 成 LoginEvent。
17. **shell 語言止血（階段 A）**：賦值 `VAR=val` 存 environ、no-op builtin 靜默成功、
    控制關鍵字靜默跳過。**只不報錯，不真執行**（階段 B 未做，見 §6）。
18. **命令替換 `$(...)`/反引號**：pre-parse pass（bash 在分詞前求值），遞迴巢狀。
19. **fd 重導向**：`2>` `2>>` `2>&1` `>&2` `1>&2` `&>` `2>/dev/null`。

### 一致性 / 稽核 / 權限
20. **統一模擬時鐘**：ctx.clock + boot_time 是唯一時間源，date/uptime/top/ls/stat/新建檔
    全讀它；載入時 shift_mtimes 把靜態 fs 時間線平移到「現在」。
21. **使用者一致性單一來源**：登入時 _provision_user 決定 uid（passwd 有則沿用、無則
    分配+補 passwd），id / passwd / ls owner / 檔案 owner 四者永遠對得上。
22. **權限 advisory 模型**：VirtualFS.access() 是唯一權限判斷點，**只由命令層呼叫**，
    mutation 方法本身不強制（不擋內部 provisioning 與測試）。root bypass。
    **v3 已收尾**：讀/寫/執行/rm/cp/mv 全走 access()（見 §13.4）。
23. **稽核不拖垮蜜罐**：EventBus.emit 吞掉 listener 例外、同步零延遲分派；JSONLSink
    IO 失敗靜默。稽核壞掉絕不能影響對攻擊者的回應或穩定性。

### 稽核事件的真實範圍（v4 釐清，接手務必知道）
**目前實際 emit 到 JSONL 的只有三種事件**：`CommandEvent`（含 hit/resolved_name）、
`ErrorEvent`、`LoginEvent`（憑證捕獲）。**`SessionStartEvent`/`SessionEndEvent` 從未
被 emit**，因此 **audit 流裡沒有 src_ip**。這直接影響 analyzer：session 只能靠
`session_id` 關聯，per-IP 分析需未來補 SessionStart 的 emit 接線（小工，見 §22）。

---

## 5. 端到端資料流（目前）

```
SSH client → asyncssh(auth，任意帳密放行) → handle_client
  → 建 read_prompt（echo-off）、ContentFetcher（若 --llm）、掛 event_bus
  → ShellSession（掛 memory/pruner/fetch_content/read_prompt/event_bus 到 ctx）
     → Interpreter.execute(line)
        → cmdsubst（$(...) 先求值）→ parse（含 fd 重導向）
        → 每 job/pipeline：_dispatch：
              賦值？→ 存 environ／控制關鍵字？→ 跳過／no-op builtin？→ 成功
              展開 token → registry.resolve
                emit CommandEvent（hit/miss）→ event_bus → JSONLSink 落地
                命中（60 內建）→ Command.run()（讀寫 VFS 前 access() 檢查權限）
                未命中 → miss_handler（LLM factory）→ LLMCommand（C_i 回寫 VFS）
                       → LLM 掛 → command not found（韌性）
        → 逃逸意外被 execute() 頂層兜底 → -bash: internal error + emit ErrorEvent（不斷線）
        → 輸出經 TerminalWriter(LF→CRLF) 回 client

【v4 離線實驗鏈】
Cowrie input.csv → replay_cowrie（解析+分組+SSH replay）→ 蜜罐（上面那條）
  → JSONLSink → (collector 合併加 _source) → _merged.jsonl → analyze.py → 數字
```

每連線一棵全新 VFS（拋棄式），登入時 _provision_user + set_owner + shift_mtimes +
注入 clock/boot_time/src_ip。

---

## 6. 已知延後項 / 隱患（誠實清單，接手優先看）

### shell 語言（階段 B，未做）
- 控制結構只「不報錯」，**不真的執行** if 條件判斷 / for 迴圈展開。
- heredoc（`cat <<EOF`）、算術 `$((...))`、`${VAR:-default}`、process substitution。

### 稽核事件範圍（見 §4 釐清）
- 只 emit Command/Error/Login 三種；**無 SessionStart → 無 src_ip**。
- 空密碼記成 `pass=''`（正確記錄空輸入）；多次嘗試等細節未雕。

### 權限模型（v3 收尾後剩餘近似）
- **已做**：讀/寫/執行/rm/cp/mv 全走 access()，root bypass。
- **待補/近似**：`ls -l` 子項 search 權限、setuid、`sudo -l` 列 sudoers、chmod/chown 後
  行為改變。

### LLM 生成品質（非架構問題）
- curl/wget stdout 內容、未知命令回應，品質取決於 qwen2.5:14b 遵從度。已見雜訊：LLM 把
  假 bash 錯誤編進 script、install.sh 參數不完美。改善方向：調 content_fetcher/prompt_builder
  的 prompt、few-shot。**同 URL 跨 session 不一致是刻意的**（session-scoped cache）。

### fd 重導向剩餘
- fd 3+ 自訂描述符、`exec 3<>`、`>f 2>&1` vs `2>&1 >f` 順序敏感性（目前近似）。

### 其他零星
- `ps` 不反映 attacker 剛跑的命令（無 process model）、與 netstat PID 不交叉。
- `printf`/`kill`/`ln`/`file`/`md5sum`/`nohup` 未註冊（常見，可補）。
- crontab -e 互動編輯器未做。
- **replay 對抗**：部分攻擊者用**固定攻擊序列**，不受回應內容影響（論文 §5 也提），
  對這種 HoneyGPT 也無法延長互動——這是研究限制，不是 bug。

### 時間一致性（已一致，但有近似）
- 時區固定 UTC（很多 server 就是 UTC，非破綻）。stat 三時間由單一 mtime 衍生微差。
  ls link count = 2+子目錄數（近似）。

---

## 7. 程式風格慣例（沿用）

- 檔頭 `from __future__ import annotations`；用 `dataclass`；每模組 `__all__`。
- **docstring 寫清楚**：設計血緣（對應論文哪節 / Cowrie 哪塊 / 哪個 HANDOFF 決策）、
  與 bash 差異、延後項、**刻意不做的範圍**。
- **測試雙模式**：每個 `tests/test_*.py` 同時支援 `pytest` 與 `python tests/test_x.py`
  （底部 `_run_standalone()`；檔頭 `sys.path.insert` 保底）。
- **純函式優先**：能抽成吃字串/list 回值的純函式就抽（analyze/replay/completion 都這樣），
  單元測試不必造暫存檔或 mock。整合測試才起真 server。
- core/memory 零外部相依；httpx 只在 backends 惰性；asyncssh 只在 transport（replay 也惰性）。
- 命令錯誤訊息對齊 bash。**跑到綠才交付。**
- 交付前清 `__pycache__`、`*.egg-info`、`.pytest_cache`，並在全新路徑復驗一次
  （解壓→install→pytest）模擬使用者流程。

---

## 8. 如何跑 / 測 / 部署（單機）

```bash
cd easypot
pip install -e '.[transport,dev]'       # asyncssh + pytest
pip install httpx                       # 只有要用 LLM 才需要
python -m pytest -q                     # 440 passed, 1 skipped（有 Ollama 時 441）
python tests/test_analyze.py            # 單一模組免安裝（雙模式）

# 純蜜罐（無 LLM）
python -m honeyshell --port 2222 --hostname happydog

# 蜜罐 + 本地 Ollama（使用者慣用啟動）
ollama serve                            # 另一終端
ollama pull qwen2.5:14b
python -m honeyshell --port 2222 --hostname happydog --llm --log-level DEBUG 2>&1 | tee /tmp/honey.log

ssh -p 2222 alice@127.0.0.1             # 密碼隨便（accept_all）；非 root 可測 sudo 問密碼

# 重生部署用 fs.json（DB 人設，預設 hostname=happydog）
python -m honeyshell.fs.build_sample_fs --hostname happydog
```

---

## 9. 論文對照速查

| 論文元素 | 落點 |
|---|---|
| P（原則）/ S（軟硬體） | `core/config.py::Principles / SystemProfile` |
| Q_i / A_i | interpreter seam → LLMCommand |
| C_i（狀態變化，回寫 VFS） | `backends/fs_applier.py` |
| F_i（Table1 影響因子） | memory.fl |
| Question Enhancement（三子問 CoT） | `backends/prompt_builder.py` |
| SR_i / H_i | `memory/session_memory.py` |
| Memory Pruning（w=0.8） | `memory/pruner.py` |
| Hybrid 路由 + cache | `backends/resolver.py` + `cache.py` |
| 成本統計（§4.6 token/延遲） | `core/events.py::LLMEvent`（resolver emit） |
| **§4.6 miss rate（1.27%）** | **`analyze.py`（v4，用真實 replay 流量重現）** |
| **§4 baseline replay** | **`replay_cowrie.py`（v4，Cowrie 資料集同源）** |

---

## 10. 進入點速查

- 啟動：`__main__.py` → `transport.start_server`（建共享 resolver/content_client/event_bus）
  → `handle_client`（每連線建 read_prompt、ContentFetcher、掛 ctx）。
- 一行命令怎麼跑：`shell/interpreter.py::Interpreter.execute` → `_execute_inner`。
- **LLM 接點**：`_dispatch_inner` 的 registry miss → `miss_handler`（LLM factory）。
- 新增內建命令：`commands/impl/` 開檔、`@register(...)`，`discover()` 自動載入。
- 改 LLM 生成內容：命令模擬看 `prompt_builder.py`；curl/wget 內容看 `content_fetcher.py`。
- 調記憶參數：`core/config.py::MemorySettings`（w、max_prompt_chars、min_keep）。
- 互動輸入 / 憑證：`ctx.read_prompt`（實作在 ssh_server）+ `impl/_credentials.py`。
- **稽核事件**：發布在 `interpreter.py::_emit`（CommandEvent）與 `execute` 頂層兜底
  （ErrorEvent）；sink 在 `core/event_bus.py`（JSONLSink / LoggingSink）。
- **權限檢查**：`fs/filesystem.py::VirtualFS.access`；呼叫點在 cd/mkdir/interpreter/rm/cp/mv。
- **時間**：`ctx.now()` / `ctx.boot_time`；載入平移 `fs.shift_mtimes`。
- **使用者 provision**：`transport/session.py::_provision_user`。
- **身分切換**：`commands/impl/su.py::_switch_identity`。
- **【v4】tab 補全**：`transport/completion.py`（純函式，命令名 + VFS 路徑）。
- **【v4】聚合分析**：`honeyshell/analyze.py`（`python -m honeyshell.analyze`）。
- **【v4】流量 replay**：`honeyshell/replay_cowrie.py`（`python -m honeyshell.replay_cowrie`）。

---

## 11–12. （v2 歷史紀錄，已摺疊）

§11（v2 當時的下一步）與 §12（DB 人設 + 稽核 + 一致性 + 權限的逐條變更）已被後續
版本吸收。完整逐條紀錄見 v2 原文；接手不需回溯，重點已進 §4 決策與 §13 v3。
關鍵摘要：
- **12.1 DB 人設（happydog）**：SystemProfile 改 DB 機、build_sample_fs 節點 40→175
  （完整 /etc、多使用者誘餌家目錄、metadata-only 工具、真實格式 /var/log）。
- **12.3 結構化稽核**：JSONLSink + ErrorEvent + 每命令 emit CommandEvent（hit/miss）。
- **12.5–12.10**：模擬時鐘（治 1970）、uid/owner 一致、ls/stat 擬真、權限（cd/mkdir/寫檔）、
  su 身分切換、netstat 顯示攻擊者自己 IP。**這些都是使用者手動 demo 撞出來的真 bug。**
- **測試演進**：348 → 378（v2 終點）。

---

# ═══════════════════════════════════════════════════════════════
# HANDOFF v3 — QA 修復 + 讀寫權限收尾 + Docker 部署
# ═══════════════════════════════════════════════════════════════

## 13. v3 變更紀錄（QA 修復 + 權限收尾）

### 13.1 Gemini QA 擬真修復（逐一對照原始碼修）
- **ls 長參數**（`ls --fakearg`）：字元拆分前先攔 `--`，回 GNU 一致的
  `unrecognized option '--fakearg'`。
- **cat 未解析 flag**（`cat -Z`）：加 flag 解析；實作 `-n/-b/-E`。
- **curl -I placeholder**：解析 `-I/--head`，短路輸出擬真 HTTP headers（Date 讀模擬時鐘），
  不落 body。helper `head_response()` 在 `_download.py`。
- **/proc 缺檔**（`cat /proc/uptime`）：build_sample_fs 補 `/proc/uptime`、`/proc/loadavg`、
  `/proc/mounts`。**已重生 data/fs.json**。
- **MAC = KVM 指紋**（`52:54:00`）：新增 `_netinfo.py` 收斂 IP/MAC/GW 單一來源，MAC 改
  Dell 裸機 OUI；ifconfig/ip 共用，杜絕 MAC 漂移。

### 13.2 補「確定性高頻」命令（top/mount/ping）
只補確定性、高頻、LLM 難生成一致的三個內建；apt-get 留給 LLM、yum 另處理。
- `top.py`：一次性快照（等同 `top -bn1`，不進互動迴圈），讀 boot_time+profile+meminfo。
- `mount.py`：讀 /proc/mounts 重格式化，與 df 對齊。
- `ping.py`：靜態成功統計，不真阻塞、封包數上限 20。

### 13.3 yum「熱心 AI」指紋 + apt-get 進 fixture
- **yum 指紋**：LLM 生成 `yum install x` 竟回「using apt-get instead...」——helpful-AI 語氣
  是最大破綻。→ 新增 `yum.py`（register yum/dnf）直接回 `command not found`（exit 127），
  標記 `absent_from_path=True` 讓 which 一致。
- **apt-get 進 fixture**：build_sample_fs 的 /usr/bin 補 apt/apt-get/apt-cache/dpkg。
- **prompt 冷酷 bash 約束**：prompt_builder 系統提示加「Tone — COLD and MACHINE-LIKE」硬規則，
  明列禁止「using X instead」「I'll/let me/here's」等語氣。縱深防禦，效果受模型遵從度影響。

### 13.4 讀權限 + rm/cp/mv 權限（權限模型收尾）
- **讀權限**：`_fileorstdin.py` 加 `check_read()`，一處覆蓋 head/tail/wc/grep/cut/sed/sort；
  cat 與 `<` 重導向各自接。非 root `cat /etc/shadow`(0640) → Permission denied；
  `/etc/passwd`(0644) 仍可讀；root bypass。
- **ls 目錄讀**：列目錄前檢查目錄 r。非 root `ls /root`(0700) → Permission denied。
- **rm/cp/mv**：`_fsflags.py` 加 `parent_writable()`/`path_readable()`。rm 檢查父目錄 w
  （`-f` 不 bypass）；cp 檢查 src 讀+dst 父寫；mv 檢查來源與目標父寫。
- **權限現況**：讀/寫/執行/rm/cp/mv 全走單一 access()，root bypass。仍近似：ls -l 子項
  search 權限、setuid、sudo -l。

## 14. Docker 部署（deploy/）

### 14.1 拓撲
單機 `docker compose`：**2 蜜罐 + 1 collector**，共享 audit volume。
```
honeypot-a (host:2201, hostname=web01) ─┐
                                        ├─► audit volume ─► collector ─► _merged.jsonl + stdout
honeypot-b (host:2202, hostname=db01)  ─┘
```
- 無人設差異化 / 無 LLM（先簡單）：兩台純規則 shell，只 hostname 不同。之後差異化：
  各 honeypot 加 `--llm` + 各自 `--fs`。

### 14.2 檔案
- `deploy/Dockerfile`：蜜罐 image，非 root（uid 10001），host key 持久化。
- `deploy/collector/collect.py`：純 stdlib tailer，poll `*.jsonl`、合併加 `_source`、
  壞行不丟（包 `_raw`/`_value`）、開檔失敗重試不 crash。
- `deploy/collector/Dockerfile`：collector image，**uid 也是 10001**（關鍵，見 14.4）。
- `deploy/docker-compose.yml`、`deploy/README.md`、根 `.dockerignore`。

### 14.3 程式接線
- `ServerConfig.audit_jsonl_path`（transport/config.py）+ `--audit-jsonl` flag +
  `EASYPOT_AUDIT_JSONL` env（__main__.py）。
- `ssh_server.py`：有 audit path 時掛 `JSONLSink`（與 LoggingSink 並存）。預設 None →
  單機執行不受影響。

### 14.4 ⚠️ Docker volume 權限雷（排錯過，務必記住）
**症狀**：collector 一直 Restarting，蜜罐 log PermissionError。
**根因**：collector image 原用 uid 10002、honeypot 用 10001。Docker 建新具名 volume 時把
image 該路徑的 owner/mode 複製進 volume——誰先初始化 owner 就是誰。two uids → 一方寫不進
→ crash-loop。`user:` 只改執行身分，改不了 volume 初始化繼承的 owner。
**根治**：兩 image 統一 uid **10001**。**換 uid 後必須清 volume**：`docker compose down -v`
+ `docker volume rm easypot_audit easypot_keys-a easypot_keys-b`，確認空再 `up --build -d`。
**額外韌性**：collect.py 開 _merged.jsonl 失敗改印錯誤+重試（不 crash）。
**已驗證**：owner=10001、collector Up、憑證捕獲進 merged。

## 15. 部署操作速查
```bash
cd deploy
docker compose up --build -d
docker compose ps                    # 三個都要 Up（collector 不是 Restarting）
ssh -p 2201 alice@127.0.0.1          # web01；密碼隨便
ssh -p 2202 bob@127.0.0.1            # db01
docker compose logs -f collector     # 即時合併事件流（每行帶 _source）
docker compose exec collector cat /data/audit/_merged.jsonl
docker compose down -v               # 停並清 volume
```

## 16. 專案報告怎麼呈現（v3 討論，v4 於 §21 延伸）
**別用「能不能被真的攻破」衡量蜜罐**——那是滲透測試標準。蜜罐價值是「騙得夠久、記得夠全」，
對齊論文三軸：擬真度 / 互動深度 / 彈性 + 資料鏈。
1. **擬真度 before/after 對照**（最有說服力）：拿 §13 修復當實驗結果。探測命令 ×
   (native LLM / 本蜜罐 / 真實 Linux) 輸出對比表。
2. **互動深度 demo**：錄 terminal，模擬偵察流程 + 權限模型（cat /etc/shadow 被擋）。
3. **資料鏈 + 情報產出**：2 honeypot → collector → merged → analyzer 的 session 時間線、
   憑證捕獲、命令頻率。這是蜜罐的**目的**。

## 18. v3 測試演進
378（v2）→ 395（QA）→ 404（讀權限+yum）→ 409（ls 權限+apt fixture+冷酷 prompt）
→ 419（rm/cp/mv）→ 421（audit config wiring）。

---

# ═══════════════════════════════════════════════════════════════
# HANDOFF v4 增補 — 實驗工具鏈（analyzer + replay + 補全）
# ═══════════════════════════════════════════════════════════════

> v4 主軸：把蜜罐從「能跑、能部署」推到「能產出報告數字」。三件事：補記 v3 漏掉的
> tab 補全；做 analyzer（聚合 miss rate/情報）；做 Cowrie replay bridge（用真實攻擊
> 流量餵蜜罐）。**測試 421 → 440 passed, 1 skipped。**

## 19. v4 變更紀錄

### 19.1 tab 補全（`transport/completion.py`）— v3 漏記，v4 補文件
> **注意**：這支在 v3 交接時已存在於 tar 但 v3 文件沒提。接手若比對「v3 說 421、卻有
> test_completion」不用困惑，就是這個。
- 純函式補全邏輯（transport-agnostic，好單測）：首 token 補**命令名**（registry），
  後續 token 補 **VFS 路徑**。
- `tests/test_completion.py`：12 條，全綠。

### 19.2 analyzer（`honeyshell/analyze.py`）— 對應 v3 §17「下一個要做的」
**定位**：單檔、純 stdlib、讀 collector 的 `_merged.jsonl`，輸出三組聚合。**刻意不丟 LLM**
（事件已被蜜罐標註 hit/resolved_name），**不做即時 dashboard**（批次跑一次即可）。

三個聚合器（對齊報告三目標）：
- **`LlmEfficiency`**：`hit=true` vs `hit=false` 比例 = **miss rate**。這是「混合架構值得
  做」的量化辯護，對應論文 §4.6 的 1.27%。含 top_misses（最常走 LLM 的命令 = 覆蓋缺口
  = 未來補命令優先序）、per-source 拆分。
- **`SessionSummary`**：按 session_id 串時間線——幾條 session、各幾命令、憑證數、走多深、
  最活躍 session。**session 來源用 `_source`（哪台蜜罐）表示，非攻擊者 IP**（見 §4 釐清）。
- **`IntelSummary`**：命令頻率 top-N、憑證清單（sudo/su 密碼）、兩蜜罐行為對比、錯誤型別。

輸出三格式：`console`（給你看）、`json`（結構化可再處理）、`md`（直接貼報告，表格排好）。
純函式 `load_events()`/`analyze()` 吃 list 回 Report，好單測；容忍 collector 的壞行包裝
（`_raw`/`_value`）。CLI 有 broken-pipe 防護（管到 head/less 不噴 traceback）。
- `tests/test_analyze.py`：10 條（載入容錯、比例、session 串接、情報、輸出），全綠。

### 19.3 Cowrie replay bridge（`honeyshell/replay_cowrie.py`）
**定位**：把公開 Cowrie 資料集的 `input.csv` replay 進本地 easypot，讓蜜罐正常處理並
emit hit/miss，collector 落地後給 analyzer。**這是 analyzer 的資料來源**——沒有真實流量
analyzer 沒東西算。

- **資料來源**：Kaggle "Medium-interaction SSH honeypot data"（xmlyna/cowrie-honeypot），
  **與論文 §4 Table 3 [38] 同源**（2022 Cowrie 捕獲）。用真實資料 replay = 公信力等同論文。
- **只吃 `input.csv`**（三欄：session/timestamp/input）。sessions.csv 不用——replay 不需要、
  也不該用真實攻擊者 IP（replay 來源本來就是 localhost）。
- **input 整行原樣送，不拆 `;`**：讓蜜罐 parser 自己處理攻擊鏈（wget;chmod;./exec），
  才測得準覆蓋度。實測 fixture 的鏈被正確拆成 wget/chmod/./x/rm/history，3 個真 miss
  （亂數 binary、自訂 ./x、history -c）。
- **一個 Cowrie session = 一條 easypot SSH 連線**（互動式 shell，請求 PTY），時間線對齊。
  收尾用 EOF 關閉，**不送字面 `exit`**（否則被記成一條攻擊命令污染統計）。
- **安全**：命令當文字送，不在本機執行；只連本地 target；不讀不落地真實 IP。**資料集的
  `files/` 是真惡意樣本，replay 完全不碰，接手也別去執行/解壓它。**
- **只依賴 asyncssh**（惰性），解析層純 stdlib。CLI：`--fixture`（免真資料驗 pipeline）、
  `--limit N`（試跑）、`--delay`、`--dry-run`、`--concurrency`。內建 `FIXTURE_CSV` 讓
  測試/CI 免下載就能跑。
- `tests/test_replay_cowrie.py`：9 條。解析層 7（分組/排序/容錯/limit/攻擊鏈保真）+
  **真 in-process SSH server 端到端整合 2**（起真 server → replay fixture → 驗 hit/miss
  事件經真實 `--audit-jsonl` 落地）。整合測試刻意用真 server 非 mock（replay 的價值就在
  命令真的走過蜜罐的 hit/miss 判定）。缺 asyncssh 則 skip。

## 20. v4 實驗操作速查（產報告數字的完整流程）

```bash
# 1. 起蜜罐（加 --audit-jsonl 讓 analyzer 有資料；開 --llm 讓 miss 命令真的生成）
python -m honeyshell --port 2222 --hostname happydog --llm \
    --audit-jsonl /tmp/audit.jsonl --log-level DEBUG 2>&1 | tee /tmp/honey.log

# 2. 另開終端，先 dry-run 看解析出多少（input.csv 約 11MB，session 很多）
python -m honeyshell.replay_cowrie <path>/input.csv --dry-run

# 3. 先跑前 20 個 session 試水
python -m honeyshell.replay_cowrie <path>/input.csv --limit 20 --delay 0.1

# 4. 沒問題全量（量大建議 --concurrency 4 加速）
python -m honeyshell.replay_cowrie <path>/input.csv --concurrency 4

# 5. 出數字（md 直接貼報告）
python -m honeyshell.analyze /tmp/audit.jsonl -f md -o report.md

# 免真資料先驗 pipeline 通：
python -m honeyshell.replay_cowrie --fixture --dry-run
```

**提醒**：
- **開 `--llm` 跑才有擬真度意義**：miss 命令要真的走 Ollama 生成；沒開只會回
  command not found（hit/miss 統計仍正確，但擬真度那塊測不到）。
- Docker 版：collector 會產帶 `_source` 的 `_merged.jsonl`，直接餵 analyzer；單機版
  analyzer 吃單一 audit.jsonl 也行（無 _source，per-source 那塊會併成 unknown）。

## 21. 報告要證明什麼（v4 明確化，對齊實習脈絡）

**核心命題**：「規則為主 + LLM 補盲的混合蜜罐，能用極少的 LLM 呼叫，在擬真度上顯著贏過
純規則蜜罐（Cowrie），同時規模化成本幾乎不隨台數增長。」拆成三個可量測目標：

| 目標 | 產出數字 | 工具 | 對應「學到什麼」 |
|---|---|---|---|
| **一 擬真度** | N 個探測命令中 easypot 對幾個 vs Cowrie（SALC/FALC 對照表） | §16 探測題庫（**未做**） | 對抗性擬真、指紋思維 |
| **二 LLM 效率** | X% 規則命中 / Y% 走 LLM（對照論文 1.27%） | **analyze.py（已做）** | 成本/效能取捨的系統設計 |
| **三 情報產出** | N 個 session、Y 組憑證、命令頻率、攻擊鏈 | **analyze.py（已做）** | 威脅情報怎麼從 raw log 萃取 |

**為什麼 miss rate 是報告核心數字**：它一個數字同時反駁兩個質疑——
(A)「規則都寫好了 LLM 是不是白裝？」→ miss>0 證明真實流量就是有規則沒覆蓋的命令，
靠 LLM 才沒露餡；(B)「每次丟 LLM 不就很慢很貴？」→ hit 佔絕大多數證明 N 台蜜罐的 LLM
負載 ≈ 總命令 × miss_rate，一個共享 LLM 池就吃得下。這正是「我理解為什麼這樣設計」的證明。

**規模化結論（使用者問過）**：能大量部署，但正解是 **N 台無狀態蜜罐（純輕程序）共享
1 個 LLM 池 + 全域 cache**，不是每台一個 GPU。現有架構天生支持（OllamaClient 是 HTTP
client，改 `--llm-url` 指向共享 gateway 即可，程式不用動）。miss rate 實測值直接反推 GPU
池要多大。

## 22. 建議下一步（v4 更新版，停下等指示）

實驗工具鏈（目標二、三）已齊，建議順序：
1. **跑真資料出數字**：照 §20 全量 replay + analyze，拿到真實 miss rate 與情報統計。
   有數字後可請協助**解讀、挑報告該講哪幾個**。
2. **目標一 擬真度題庫（唯一還沒做的目標）**：獨立小工具，跑一組探測命令對比
   easypot vs Cowrie vs 真 Linux，產出 §16/§21 目標一那張對照表。不靠 log，是另一條線。
3. **補 SessionStart emit（小工，解 analyzer 的 IP 限制）**：在 transport 補發
   SessionStartEvent（帶 src_ip），analyzer 就能做 per-IP 分析（目前只能 per-session）。
4. 其他延後（不影響報告）：shell 階段 B、零星命令（printf/kill/ln...）、sudo -i 殘留、
   ls -l search 權限、LLM 生成品質調校。

## 23. v4 測試演進
421（v3 終點）→ 431（analyzer 10 條）→ **440（replay 9 條）**，1 skipped。全綠，每輪
全新路徑復驗（解壓→install→pytest）。deploy 不影響 pytest（collector 純 stdlib、單獨測）。
replay 整合測試起真 in-process server，pytest 總時間增至 ~15s（值得——測到真實 hit/miss 路徑）。

# ═══════════════════════════════════════════════════════════════
# HANDOFF v5 增補 — 噪音/憑證過濾 + replay 分流 + Docker B/C(共享 LLM 池)
#                  + LLMEvent 成本接線 + RUNBOOK + 待辦 GPU 加速
# ═══════════════════════════════════════════════════════════════

## 24. v5 一句話

v4 的工具鏈拿去跑**真實 Cowrie 資料**,過程中發現並修掉三個資料品質 bug、把 docker
部署升級成「雙台 host1/host2 共享宿主機 LLM 池」、並把 LLM 成本數字(對照論文 §4.6)
接進 audit。**測試 440→465,全綠。** ~~唯一未解:GPU 沒被 Ollama 啟用,導致延遲 9.6s/次
(見 §30,是待辦最高優先,修好跑 A 會快近 10 倍)。~~ ← **此 v5 結論已被 v6 §36.4 推翻：
GPU 一直正常，延遲真根因是輸出長度，非 GPU。**

## 25. v5 變更紀錄

### 25.1 analyzer 互動噪音過濾(`analyze.py`)
**問題**:Cowrie 公開資料集的 `input.csv` 把「攻擊者輸入」和「互動程式(passwd)的
輸出提示」混在同一欄。replay 忠實重放整欄 → `New password:`、`Changing password for root`
等提示字串被當命令送進蜜罐、registry 找不到 → 記成 `hit=false`。**實測這類噪音佔 miss
逾三成**(污染 miss rate 從真實 ~11% 灌到 ~16.7%)。
**修法**:分析層加 `is_interactive_noise(raw, resolved_name)` 純函式,精確匹配 +
前綴匹配把提示排除在 miss 統計外。**關鍵:白名單式精確匹配,絕不誤殺真命令**——
`chpasswd`/`awk '...'`/`passwd` 雖同為 `resolved_name=null, hit=false`,但它們是真實
覆蓋缺口(該計入 miss),不匹配任何提示樣式 → 保留。被濾筆數另計 `interactive_noise`
在報告透明呈現。
**為何放分析層不放 replay**:raw log 保留原貌(資料集缺陷本身是情報);過濾規則可迭代,
改規則隨時重算不必重跑 replay;replay 職責是忠實重放,清洗屬分析層(關注點分離)。

### 25.2 analyzer 假憑證過濾(`analyze.py`)— **初步報告揪出的 bug**
**問題**:憑證捕獲被污染。蜜罐把 passwd 互動的**提示字串**(`Enter new UNIX password:`)
和**後續命令**(整條 `cat /proc/cpuinfo | grep name | awk ...`)當成 LoginEvent 的 password
發出來 → 憑證統計灌水(實測「208 組憑證」全是假的)。**根因在蜜罐端**:憑證擷取的邊界
判定沒排除互動噪音。
**修法(分析層止血)**:加 `is_credential_noise(username, password)`,password 命中
以下任一即濾:(1) 是已知 passwd 提示;(2) 看起來是命令而非密碼(含 `| ; & > < 反引號`,
或多 token 長字串)。真憑證(`root:admin`/`root:123456`/`root:P@ssw0rd!`)保留。
**根治(未做,記 known issue)**:改蜜罐憑證擷取的邊界,讓它一開始就不把提示/命令
當憑證發。要改蜜罐 + 重跑才驗得到,故選分析層止血。測試用**初步報告實際跑出的假憑證**
當回歸 fixture。

### 25.3 replay 多 target 分流(`replay_cowrie.py`)
**新增**:`--target` 改可累積(`action="append"`)。給一個 = 舊單機行為(向後相容);
給多個 = **按 session round-robin 分流**到多台。
- `split_targets(sessions, n)` 純函式:**session 為原子單位,不切分單一 session 的命令**
  (一條攻擊鏈如「登入→偵察→植入後門」必須整條落同一台,否則 host1 見 wget、host2 見
  chmod,鏈斷、VFS 狀態不連貫)。用 round-robin 而非前半/後半,兩台流量分布均勻 →
  per-source miss rate 才可公正對比(規模化一致性驗證)。
- `Target` dataclass、`replay_multi()` 協調多 target 各自並行。舊 `replay()` 不動。
- CLI 多 target 時 dry-run 預覽分流、進度標 `→host1`、完成印各台數字。

### 25.4 LLM 設定 env fallback(`__main__.py`)
`resolve_llm_settings(cli, env)` 純函式,優先序 CLI > env > 預設,跟 `EASYPOT_AUDIT_JSONL`
對稱。讀 `EASYPOT_LLM` / `EASYPOT_LLM_MODEL` / `EASYPOT_LLM_URL` → docker compose 全用
env 控制 LLM,不必改 CMD。順手修了 config 預設 `7b` vs `__main__` `14b` 的歧義(以
env/CLI/14b 為準)。

### 25.5 LLMEvent 接進 audit + 成本分析(`ssh_server.py` + `analyze.py`)— **回答「miss rate ≠ 論文 1.27%」**
**根因**:`ssh_server.py` 建 `ChainResolver` 時漏傳 `bus=event_bus` → resolver 的 `_emit`
一進去就 return(bus is None)→ LLMEvent 從沒進 audit。**一行接線遺漏。**
**修法**:`ChainResolver(..., bus=event_bus)`。LLMEvent 現在流進 JSONLSink → audit
(型別 `"type": "llm"`,含 model/prompt_tokens/response_tokens/latency_ms/cached)。
`analyze.py` 加 `LlmCost` 聚合,算出:
- **真打 LLM 率**(cached=False 佔全部命令)← **這才對照論文 §4.6 的 1.27%**
- cache 命中率(cached=True)、平均 prompt/response token、平均延遲。
**關鍵概念(接手&使用者都混淆過,務必懂)**:
```
miss rate(11.26%)= 規則沒接住,含 cache 命中     ← LlmEfficiency
真打 LLM 率(<11.26%)= miss 扣掉 cache,真呼叫模型  ← LlmCost，對照 1.27%
```
`awk`/`w` 這種高頻重複 miss 大量走 cache,不真打 LLM,所以真打率遠低於 miss rate,
接近論文量級。舊資料無 llm 事件時 LlmCost 全 0,報告標「無 LLM 事件」,不炸。

### 25.6 依賴修復:httpx(`pyproject.toml` + `deploy/Dockerfile`)— **docker LLM 啞掉的 bug**
**問題**:docker 蜜罐開了 `--llm`、env 對、連得到 Ollama,但 miss 命令全回 command
not found。log 出現 `httpx is not installed`。**根因**:`OllamaClient` 用 httpx 發請求,
但 httpx 沒被宣告成依賴(核心 `dependencies=[]`,extras 只有 transport/dev),Dockerfile
`pip install '.[transport]'` 沒裝到。本機能跑是因為手動 `pip install httpx` 過。
**修法**:pyproject 加 `llm = ["httpx>=0.24"]` extra;Dockerfile 改 `.[transport,llm]`。
蜜罐對 httpx 缺失是**韌性降級**(回 not found 不 crash),所以 bug 藏得深——查 log 才發現。

## 26. Docker 部署 v5(deploy/,取代 v3 §14 拓撲)

### 26.1 新拓撲:雙台相同蜜罐 + 共享宿主機 LLM 池
```
host1 (host :2201, --llm) ─┐
                           ├─► audit volume ─► collector ─► _merged.jsonl(帶 _source)
host2 (host :2202, --llm) ─┘                                      │
   宿主機 Ollama (qwen2.5:14b) ◄── 兩台 miss 命令共用 ──          ▼  honeyshell.analyze
```
- **兩台完全相同**(同 fs.json、同 SystemProfile),**只差 hostname host1/host2**
  (使用者要求:拿掉 web01/db01 人設差異)。目的不是比較不同人設,是證明「同一設計、
  多台部署、共享 LLM 池」→ 兩台 miss rate 應接近 = 規模化一致性驗證。
- 兩台 `EASYPOT_LLM=1` 指向 `host.docker.internal:11434`(= docker bridge gateway →
  宿主機 Ollama)。這**就是論文 §3.4 + §21「N 台共享 1 LLM 池」的實作**。
- compose 用 YAML anchor `&honeypot-llm` 共用 LLM env;兩台加
  `extra_hosts: ["host.docker.internal:host-gateway"]`(**Linux Docker 必須**,
  Mac/Win 內建)。audit → host1.jsonl/host2.jsonl;keys → keys-1/keys-2 volume。
- collector uid 10001 不動(v3 §14.4 那個 volume 權限雷,別碰)。

### 26.2 Ollama 綁定坑(排錯過)
容器透過 gateway 連宿主機,但 Ollama **預設只綁 `127.0.0.1`**,容器連不到。
- systemd 管理:`sudo systemctl edit ollama` 加 `Environment="OLLAMA_HOST=0.0.0.0"` →
  `daemon-reload && restart`。
- 手動:`OLLAMA_HOST=0.0.0.0 ollama serve`。**注意 pkill 後常被看門狗用舊設定重啟**
  (ss 看 pid 有沒有換就知道)。
- 驗證:`ss -tlnp | grep 11434` 要 `*:11434` 不是 `127.0.0.1`。
- 容器內測連線(**容器沒 wget/curl,用 python**):
  `docker compose exec host1 python -c "import urllib.request;
   print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags',timeout=5).read()[:80])"`

## 27. RUNBOOK.md(新檔,防呆操作手冊)

專案根目錄新增 `RUNBOOK.md`,把兩個實驗拆成獨立、不可同時跑的 checklist:
- **鐵則**:實驗 A(單機 :2222)和實驗 B/C(docker :2201/2202)**共用同一個宿主機
  Ollama,絕不可同時跑**(搶 GPU、數字污染)。分時段跑。
- 內含:共用前提檢查、A/B/C 逐步 checklist、故障排除(照症狀查)、血淚教訓速查表、
  一頁極簡版。清 audit 出現在三處(A0/B2/B5,防 append 疊加 + 手動測試筆污染)。
接手若要跑實驗,**先看 RUNBOOK,不要憑記憶**。

## 28. 報告數字現況(46% 部分資料實跑,已收斂)

用 docker B/C 跑到 ~46%(48869 事件、1558 session)的初步 analyze 結果:
- **hit rate 88.74%**,miss rate **11.26%**(已濾互動噪音 2498 筆;污染前是 16.7%)。
- **per-source 一致**:host1 23139 命令/miss 2625(11.3%)、host2 23019/2573(11.2%)
  → 兩台幾乎一樣 = 規模化一致性鐵證(報告目標三)。
- top_misses:awk 2497、w 1349、chpasswd 1249、apt 59、pacman 39、/bin/eyshcjdmzg 2、
  ./112 1。**awk 是頭號覆蓋缺口**(補一個 awk 內建可再提升 hit rate ~5.4%)。
- 憑證:0 組真憑證 + 已濾假憑證 208 筆(這批攻擊是 passwd 改密+偵察,本就無登入憑證)。
- 攻擊高度同質化(大量固定長度 session,如 SSH 後門植入 `mdrfckr` 腳本)→ 佐證
  cache 高效。錯誤:5 BrokenPipeError。
- **miss rate 已收斂**(15000 筆時 11.9%、42000 筆時 11.4%、48000 筆時 11.26%),
  再跑不會大變 → 部分資料已有代表性。

## 29. 論文 §4.6 對照現況(LLMEvent 已接線,待完整跑)

接線已驗證(手動測 host1 打 vmstat → audit 出
`{"type":"llm",...,"prompt_tokens":1574,"response_tokens":136,"latency_ms":9610,"cached":false}`)。
跑完 A 就能算出真打 LLM 率(對照 1.27%)、cache 率、token、延遲。**注意單次延遲 9.6s**
(見 §30,是 GPU 沒啟用所致,非模型本質)。

## 30. ❌ 已作廢（結論錯誤，見 §36.4 更正）— 原標題「待辦最高優先:GPU 沒被 Ollama 啟用」

> **⚠️ 接手注意：本節結論是錯的，GPU 從頭到尾正常運作，別照本節修 GPU。**
> 真相見 §36.4：延遲真根因是「LLM 輸出長度」，非 GPU。本節誤判源於看了**空的**
> `/tmp/ollama.log` + `nvidia-smi` 剛好抓到 idle unload 瞬間的 0%。保留原文僅供理解
> 「當初如何誤判」（避免重蹈：診斷 Ollama GPU 要看 `journalctl -u ollama | grep gpu`
> 的 `offloaded N/N layers to GPU` 和 `ollama ps` 的 PROCESSOR 欄，不要看 /tmp 那個檔）。
> 營運設定（keep-alive）已寫進 RUNBOOK §2.1.1。以下為原（錯誤）內容：

**現象**:實機是 **i7-10700(16 執行緒)+ RTX 4070(16GB)**,但 `nvidia-smi` 顯示
**GPU-Util 0%、Memory 227MB/16GB** — GPU 幾乎閒置。`qwen2.5:14b` 約需 9-10GB 顯存,
4070 塞得下,但 **Ollama 在用 CPU 跑**,導致單次生成 9.6s。丟上 GPU 預估可到 ~1s(快近 10 倍)。
**這是延遲的真根因,不是模型太大。修好比換小模型更值得(又快又不犧牲 14b 品質)。**

**待接手診斷(指令在機器上跑)**:
1. `cat /tmp/ollama.log | grep -iE "gpu|cuda|nvidia|inference"` — 看 ollama 啟動有沒有
   偵測到 CUDA。出現 `inference compute ... cpu` 或找不到 cuda = 根因確認。
2. 生成時 `watch -n 0.5 nvidia-smi` 看 GPU-Util 有沒有跳、Memory 有沒有吃到 ~9GB。
**常見修法**:確認 ollama 版本夠新(`ollama --version`,舊的 `curl -fsSL
https://ollama.com/install.sh | sh` 更新);重啟 ollama 看啟動 log 是否出現
`found 1 CUDA device / RTX 4070`。驅動 OK(nvidia-smi 顯示 550.107 / CUDA 12.4)。
**報告論述升級**:修好後可寫「中階消費級 GPU(RTX 4070)即可支撐本地 14b LLM 蜜罐,
延遲 ~Xs,無需雲端 API」——比「CPU 很慢是取捨」正面得多。

## 31. 待辦:模型大小 vs 延遲 vs 品質實驗（可選，**優先度已下修** — 見 §36.4）
> 註（v6）：本節前提「GPU 修好後」已不成立（GPU 本來就正常）。且延遲瓶頸是輸出長度
> 非模型大小，故換小模型省的是每 token 時間、代價是擬真度，CP 值不如壓短輸出（prompt
> 約束，零擬真度成本）。除非想做完整權衡實驗當報告加分項，否則不必。以下為原內容：
若 GPU 修好仍想壓延遲,或想做完整權衡實驗:換 7b/3b/1.5b 跑同一組 miss 命令
(vmstat/awk/w/lsblk),比對**延遲**與**輸出品質**。你的 miss 多是格式化系統資訊
(不需深度推理),**小模型很可能品質夠**。這實驗同時是「拟真度品質鑑定」的雛形——
對同一命令比較不同模型輸出像不像真機(SALC/FALC)。是報告加分項(展現部署層工程權衡)。

## 32. 概念釐清:hit/miss vs 品質(使用者混淆過,接手務必懂)

三個**獨立維度**,別混:
- **hit/miss** = 誰處理的(規則 registry vs LLM)。與品質無關。「加 LLM ≠ all hit」——
  hit/miss 在規則層就判定了,LLM 是 miss 的下游備援。走了 LLM 的命令**分類上仍是 miss**
  (`hit=false`),不會因為有 LLM 就變 hit。
- **品質/擬真度** = LLM 輸出像不像真機(論文 SALC/FALC)。要有**輸出內容**才能鑑定——
  目前 audit **未記 LLM 輸出內容**,故拟真度題庫(目標一)還做不了,需先讓 audit 記輸出。
- **情報** = 抓到多少有價值攻擊資訊(憑證、攻擊鏈)。
「拟真度品質鑑定」(使用者想做的)= 對 miss 命令的 LLM 輸出鑑定像不像真機,是**目標一**,
需要先記 LLM 輸出內容(比 §25.5 只記 token/latency 更進一步)。

## 33. 建議下一步(v5,停下等指示)

1. **修 GPU(§30,最高優先)**:修好 Ollama 用 GPU,跑 A 從「熬一晚」變「十幾分鐘」,
   且拿 14b 品質。診斷指令見 §30。
2. **跑 A 完整版拿數字**:GPU 修好(或接受 CPU 慢)後,清 audit → 全量 replay 分流 →
   analyze。一次拿到 miss rate + 真打 LLM 率(對照 1.27%)+ cache 率 + token + per-source
   + 情報(憑證已修)。照 RUNBOOK 跑,別憑記憶。
3. **目標一 拟真度題庫(唯一還沒做的目標)**:見 §32——需先讓 audit 記 LLM **輸出內容**,
   再對 miss 命令做 SALC/FALC 鑑定 + 對真 Linux 比對。公正版設計:題目來源用外部中立
   標準(指紋文獻[30]/論文§4.2/ATT&CK,或直接從真實流量抽探測命令),出題時不看
   easypot 會不會過,**主動納入 easypot 會輸的**(§6 shell 階段 B、process model 等),
   對真機 ground truth 判定。**別只用修過的 bug 當考卷(選擇偏誤)。**
4. **憑證擷取根治(§25.2 known issue)**:改蜜罐邊界判定,從源頭不發假 LoginEvent。
5. 其他延後(不影響報告):模型大小實驗(§31)、SessionStart emit(per-IP)、shell 階段 B、
   零星命令。

## 34. v5 測試演進
440(v4 終點)→ 445(analyzer 噪音 5 條)→ 451(replay 分流 6 條)→ 457(main_cli
env 6 條)→ 462(憑證過濾 5 條)→ **465(LLM 成本 3 條)**,1 skipped。全綠,每輪全新
路徑復驗。transport/ssh 整合測試在 LLMEvent 接線後仍 48 passed(bus 接線沒破 SSH 路徑)。
新測試重點:噪音/憑證過濾都有**防誤殺真命令**的回歸測試(chpasswd/awk 保留、passwd 提示
過濾),用初步報告實際跑出的假資料當 fixture。

# ═══════════════════════════════════════════════════════════════
# HANDOFF v6 增補 — awk 內建 + DeferToLLM 機制 + 時間注入缺陷修復
#                  + §30 GPU 誤判更正 + 擬真度探測題庫（目標一）
# ═══════════════════════════════════════════════════════════════

## 35. v6 一句話

補了 **awk 內建**（§28 頭號覆蓋缺口）並為此新增 **DeferToLLM「命令主動降級到 LLM」
機制**；發現並修復 **resolver 時間注入缺陷**（LLM 憑空編時間的根因）；**更正 §30 的
錯誤結論**（GPU 一直正常，延遲真根因是輸出長度）；建置 **擬真度探測題庫工具鏈**
（目標一，30 題 SALC/FALC 對照，含判定器 + runner + 多次重跑 + 延遲量測）。
**測試 465 → 487 passed, 1 skipped**，全綠零回歸。命令數 **60 → 61**。

## 36. v6 變更紀錄

### 36.1 awk 內建命令（`commands/impl/awk.py`）— 補 §28 頭號缺口

§28 top_misses 第一名是 awk（2497 筆）。真實流量幾乎全是 `{print $N}` 欄位提取
idiom（`cat /proc/cpuinfo | grep name | awk '{print $4}'`）。
- **內建處理**：`{print ...}`（`$N`/`$0`/`$NF`、逗號多欄位、`-F` 分隔、字串字面、
  bare print、越界回空），對齊真實 awk 語意（預設連續空白切分）。範本 `cut.py`，
  基底 `_FileOrStdin`。alias `gawk`。
- **複雜語法降級**：pattern（`/re/{}`）、BEGIN/END、算術、NR/NF、`-v` → raise
  `DeferToLLM`（見 §36.2），交 LLM 生成。
- 補 hit rate 預估 ~5.4%（miss rate 11.26% → ~5.9%），而複雜 awk 仍誠實計入 miss。

### 36.2 DeferToLLM「命令主動降級到 LLM」機制（`commands/base.py` + `shell/interpreter.py`）

**問題**：registry/miss_handler 分工原本代表 hit 命令（有註冊類別）永不走 LLM。但
awk 只能忠實處理其真實行為的子集——常見 `{print $N}` 該內建（確定性），複雜 program
該交 LLM。若讓 awk「hit 卻偷偷呼叫 LLM」會污染 miss rate（報告核心數字，§32）。
**解法（當時討論稱「做法 B」）**：
- `base.py` 加 `DeferToLLM` 例外 + `Command.fallback()`（無 LLM 時的保守輸出）。
- `interpreter.py` 重構 dispatch：**CommandEvent 的 emit 時機從 dispatch 前延後到
  確定命令是否降級之後**。hit 命令 run 若 raise DeferToLLM → 記 `hit=False`（誠實
  miss）→ 走與未註冊命令相同的 miss_handler；無 LLM 時退回該命令 `fallback()`
  （不噴 command not found，因為 binary 存在，那會露餡）。抽出 `_miss()`/
  `_safe_fallback()` helper。
- **此機制可複用**：未來複雜 sed/grep 也能降級。
- ⚠️ 降級命令必須在**寫任何 stdout 前**就判定並 raise，否則會有「部分輸出 + LLM
  重印」的雙重輸出。awk 已遵守（先解析判定、後輸出）。

### 36.3 ⭐ resolver 時間注入缺陷修復（`resolver.py` + `config.py` + `session.py` + `prompt_builder.py`）

**這是 v6 最重要的修復，是實際運行的架構缺陷，不只影響題庫。**

**根因**：`ChainResolver.resolve()` 呼叫 `builder.build()` 時**從沒傳 `now`**，導致
`inject_time=True`（§3.3.1）機制形同虛設——每個走 LLM 的時間相關命令（ps/uptime/
date/w/last）都在憑空亂編時間。實測 ps 的 init 顯示 `START=15:12 TIME=0:00`（全剛
啟動、零 CPU），真機應是 `START=幾天前 TIME=有累積`。

**修法**：
- `config.py` 抽出共用常數 `BOOT_AGE_SECONDS`（開機 ~7 天前）。
- `session.py` 改用共用常數（原本自己寫死 `_BOOT_AGE_SECONDS`，會與 LLM 路徑漂移）。
- `resolver.py` 加 `boot_time` 欄位，resolve 時算「當前模擬時間 + 開機時間」字串傳
  給 builder。
- `prompt_builder.py` 強化時間指引：明確要求 ps/top 的 START/TIME 與開機時間一致
  （長期 daemon 顯示累積 TIME、幾天前 START，不是 00:00/剛剛），date/uptime/who/last
  都用同一時鐘。

**效果**：實測修復後 ps 的 init 顯示 `START=Jul09 TIME=0:05`（合理）。這是報告裡
「發現並修復破綻」的好材料。session 層（uptime/who）與 LLM 補盲路徑現在共用同一時鐘，
不再互相矛盾而露餡。

### 36.4 ⚠️⚠️ §30 更正：GPU 一直正常，延遲真根因是「輸出長度」

**§30 的結論是錯的，接手務必以此為準，別再照 §30 修 GPU。**

§30 說「延遲 9.6s = GPU 沒被 Ollama 啟用、要換版本」。實機診斷證明這是**誤判**：
- `journalctl -u ollama | grep -i gpu` → `offloaded 49/49 layers to GPU`（全上 GPU）。
- `ollama ps` → `qwen2.5:14b  9.5 GB  100% GPU`（模型駐留、100% GPU）。
- **§30 為何誤判**：它看的 `/tmp/ollama.log` 是**空的**（systemd 版那個檔沒內容），
  然後 `nvidia-smi` 剛好抓到 idle unload 後的瞬間（GPU-Util 0%），就腦補成「跑 CPU」。

**延遲真根因 = LLM 生成 token 數**（實測三點，同一台熱機、同模型）：

| 情境 | 生成量 | 延遲 |
|---|---|---|
| say hi | ~8 token | 0.8s |
| vmstat 純輸出（帶 system prompt 約束） | ~40 token | **1.6s** |
| vmstat 自由解釋（無約束，LLM 進「助教模式」） | ~400 token | 14.5s |
| idle unload 後第一次（冷啟動含載入 9.5GB） | — | ~9.6s |

約 **30 token/s**，對 4070 跑 14b 合理。§29 那次 9.6s 是**冷啟動**（idle unload 後
重載模型），不是 GPU 問題。

**兩個營運要點（已寫進 RUNBOOK §2.1.1）**：
1. 設 `OLLAMA_KEEP_ALIVE=-1` 讓模型常駐 → 消除冷啟動。
2. 蜜罐 system prompt 天然壓短輸出（純 stdout、無解釋）→ 延遲穩定 1-2s。

**報告論述**（正面版，取代 §30/§31 的「CPU 慢要換小模型」）：RTX 4070 本地跑 14b，
延遲由輸出長度主導；prompt 約束壓短輸出 + keep-alive 常駐 → 熱推論亞秒級到數秒，
無需雲端 API。**§31「換 7b/3b 壓延遲」優先度可下修**——瓶頸是輸出長度不是模型大小。

### 36.5 prompt_builder 輸出約束加固（`prompt_builder.py`）

在 output 鍵說明 + 冷酷語氣段加固：明確要求純 stdout、不包 markdown/code fence、
不超過真實工具會印的行數、be terse。對齊實機驗證有效的極簡指令（14b 偶爾「話多」，
這降低那機率，對延遲和擬真度雙收益）。結構/JSON schema/few-shot 未動。

## 37. 擬真度探測題庫（目標一，`tools/`）— 唯一還沒完成的報告目標，已建骨架

§32/§33 講的目標一。**架構比 §32 設想的更省**：探測工具直接呼叫
`ChainResolver.resolve()` 拿 LLM 輸出，**不需動 audit/LLMEvent**（題庫是離線工具，
不經事件流）。

### 37.1 檔案清單（`tools/`，全繁中註解）
- `probes.py` — 30 題定義（20 過 / 10 預期輸），每題標 ATT&CK / 來源 / 考點 /
  誠實預測過不過 / `must_contain`（該有特徵）/ `must_have_all`（必有硬結構）/
  `per_command`（是否逐命令跑）。
- `capture_ground_truth.sh` — 實機採真機基準腳本（30 題）。
- `fidelity_judge.py` — SALC/FALC 判定器（結構/OS 邏輯，非數值相等）。
- `run_probes.py` — runner：三方（easypot/cowrie/real）輸出 → 判定 → Markdown
  對照表；支援 `--repeat N`（多次重跑消化 LLM 隨機性）、`--detail-out`（每次原始
  輸出，供人工複核）、延遲量測（每題平均 + 總平均，回答「model 輸出多久」）。
- `test_fidelity_judge.py` — 判定器測試（真機正例 + 露餡反例，12 條，獨立跑）。

### 37.2 公信力設計（§33 核心）
學界無權威欽定題庫，公信力靠**方法**：題目來源皆公開且與 easypot 無關（ATT&CK /
真實 Cowrie 流量 / 指紋文獻[30]），出題不看 easypot 會不會過，**主動納入預期會輸的
題**（跨命令狀態、系統特定表格、錯誤擬真），以真機為 ground truth 判定。

### 37.3 判定器設計（針對 LLM 輸出從嚴）
- **負面檢查**：抓 LLM 露餡——行首雜訊（ip addr 的孤立 `c`）、幻覺掛載點（mount 的
  `/dev/.mapper`/`nvdm`）、ps 全 0:00 時間。
- **正向完整性 `must_have_all`**：真機必有、缺了即露餡的硬結構（mount 必有根掛載
  + proc + sys；passwd 必有 root:x:0:0）。「沒有明顯幻覺 ≠ 完整」——一個真人 recon
  看到 mount 缺根掛載一樣起疑，故缺漏也判不符邏輯。
- ⚠️ **判定器局限（誠實揭露）**：幻覺檢查是白名單式，只抓已知樣式；新型幻覺可能漏
  抓 → 高通過率題須輔以 `--detail-out` 人工複核。

### 37.4 已驗證的 10 題結果（field run，repeat=10）
easypot **5/10**（判定器加嚴後的誠實數字）：
- **穩定過（10/10）**：Q1 uname、Q3 awk pipe、Q4 free、Q6 resolv.conf、Q7 ps
  （時間注入修復後 START/TIME 合理）、Q8 錯誤擬真。
- **穩定輸（0/10，皆可複現的結構性缺陷，非隨機）**：
  - Q2 cpuinfo：LLM 把 flags 展開成 `名稱:yes` 假欄位（格式露餡；判 ❌ 是定案，
    對真人算錯）。
  - Q5 ip addr：每次都生行首 `c` 雜訊（14b 在此格式的確定性 bug）。
  - Q9 mount：缺根掛載 + 幻覺掛載點（LLM 穩定生「不完整」的 mount）。
  - Q10 date;sleep;date：逐命令跑後兩個時間戳差 0（無跨命令狀態，暴露乾淨）。

### 37.5 關鍵洞察（報告用）
1. **擬真度需按威脅模型分層**：對腳本（絕大多數流量，§5 Fixed Attack Sequences），
   easypot 全題有回應、不中斷攻擊鏈，格式雜訊/幻覺/無狀態均不影響腳本推進 → 有效
   擬真度接近滿分，且互動深度勝 Cowrie。對真人，5/10 失分項（生成雜訊、系統特定
   表格幻覺、無跨命令狀態）是 LLM 補盲蜜罐的已知限制。
2. **關鍵差異**：easypot 失分是**可收斂的**（更大模型 / 針對性 few-shot / 記憶機制
   擴展可改善），Cowrie 的靜態回應是**不可收斂的結構性指紋**（文獻[30]已全網識別）。
   easypot 天花板高於 Cowrie，且失分項有明確工程路徑。
3. **擬真度是分布不是定值**：`temperature=0.1`（§3.3.3）下低溫穩定但多樣性低，多次
   重跑才能把偶發（Q2 曾單次生壞）與常態分開。

### 37.6 待辦（目標一收尾）
**30 題已擴充完成**（Q11-Q30 已寫入 probes.py + 採集腳本，涵蓋 12 種 ATT&CK；
20 過 / 10 預期輸）。延遲量測已接線（runner 每次 resolve 計時，報表顯示每題平均 +
總平均，直接回答「model 輸出多久」）。剩餘：
- **重採 30 題 ground truth**（新題 Q11-Q30 需真機基準）→ 校準 Q11-Q30 的
  `must_contain`/`must_have_all`（目前 Q11-Q30 是按常識預設，要拿真機輸出對齊，
  尤其 Q13 passwd、Q15 df、Q18 netstat 的欄位；10 題版 Q1-Q10 已用真機校準過）。
- 跑 30 題 × 10 次拿完整分布 + 延遲數字（`--repeat 10`；設 keep-alive 約 8-15 分）。
- **補 Cowrie 對照欄**（目前對照表 cowrie 欄全空；報告核心賣點是 easypot vs Cowrie，
  需把 30 題餵給 Cowrie 收輸出，格式同 ground_truth，用 runner 的 `--cowrie` 帶入）。
  這是接手最該優先補的一項。

## 38. 建議下一步（v6，取代 §33，停下等指示）

**GPU 已釐清（§36.4），不是待辦。** 報告三目標進度：
- 目標二（miss rate/LLM 效率）→ 已做（§25.5 analyzer + §28 數字），補 awk 後可再降。
- 目標三（情報產出）→ 已做（§28）。
- 目標一（擬真度）→ 骨架完成（§37），待重採基準 + 補 Cowrie 欄 + 跑滿。

建議順序：
1. **重採 30 題 ground truth + 跑滿 30×10**（§37.6）：拿到擬真度完整分布 + 延遲數字。
2. **補 Cowrie 對照欄**（§37.6）：讓對照表變成 easypot vs Cowrie 完整證據。
3. **跑 A 完整版拿目標二/三全量數字**（§33 舊項仍有效）：清 audit → 全量 replay 分流
   → analyze。照 RUNBOOK 跑。補 awk 後 miss rate 會再降，值得重跑。
4. 其他延後（不影響報告）：憑證擷取根治（§25.2）、模型大小實驗（§31，優先度已下修）、
   shell 階段 B。

## 39. v6 測試演進
465（v5 終點）→ **487 passed, 1 skipped**：awk 22 條（tests/test_awk.py，含降級
路徑 + interpreter dispatch 重構回歸防線）。時間注入修復（resolver/config/session/
prompt_builder）零回歸——既有 487 全過，含斷言 builder.build 參數的測試。判定器測試
獨立 12 條（tools/test_fidelity_judge.py，pytest 不收 tools/ 故不計入 487）。每輪全新
路徑復驗（解壓 → install → pytest）。命令數 60 → 61（awk，含 gawk alias）。
