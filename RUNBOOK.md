# easypot 實測 RUNBOOK

> 目的：把「單機版 miss rate 實驗」與「docker 多台 + 共享 LLM 池實驗」拆成兩條
> **獨立、不可同時跑**的流程，照著做即可，不用回想細節。
>
> **最重要的一條鐵則**：兩個實驗都吃**同一個宿主機 Ollama**。**絕對不要同時跑**，
> 否則搶 GPU、數字互相污染。分不同時段跑。

目錄：
1. 名詞與拓撲（先看懂再動手）
2. 共用前提檢查（每次跑前都做）
3. 實驗 A：單機版全量 miss rate
4. 實驗 B/C：docker 多台分流 + per-source
5. 出報告（analyzer）
6. 常見故障排除（照症狀查）
7. 血淚教訓速查表

---

## 1. 名詞與拓撲

```
實驗 A（單機）
  input.csv → replay → 1 台蜜罐(:2222) → /tmp/audit.jsonl → analyze
                            └── 宿主機 Ollama ──┐
                                                ├── 同一個！不可同時！
實驗 B/C（docker）                               │
  input.csv → replay 分流 → host1(:2201)+host2(:2202)
                          → collector 合併 _merged.jsonl → analyze
                            └── 宿主機 Ollama ──┘
```

- **hit / miss**：命令被規則 registry 接住 = hit；沒接住 = miss，走 LLM 生成。
  audit 裡 `"hit": false` 就是 miss。
- **miss ≠ LLM 呼叫數**：低 impact 的 miss 命令生成一次後會被 cache，重複命令
  走 cache 不打 LLM（論文 §3.4 的設計）。所以 miss rate 是「規則覆蓋缺口」，
  不是「實際 LLM 呼叫次數」。
- **session 是原子單位**：一條 session = 一條完整攻擊鏈。replay 分流時整條 session
  落同一台，不切分。

---

## 2. 共用前提檢查（每次跑前都做）

### 2.1 Ollama 必須在跑，而且綁 0.0.0.0（docker 實驗才需 0.0.0.0）

```bash
# 看 Ollama 在不在、綁哪個位址
ss -tlnp | grep 11434
```

- 單機實驗 A：綁 `127.0.0.1:11434` 就夠（replay 在宿主機上跑）。
- docker 實驗 B/C：**必須**綁 `*:11434` 或 `0.0.0.0:11434`，否則容器連不到。

若需要改成 0.0.0.0（docker 用）：

```bash
# 若 systemd 管理 ollama：
sudo systemctl edit ollama
#   在編輯器貼入（兩個變數一起設，見 2.1.1 說明 KEEP_ALIVE）：
#   [Service]
#   Environment="OLLAMA_HOST=0.0.0.0"
#   Environment="OLLAMA_KEEP_ALIVE=-1"
sudo systemctl daemon-reload
sudo systemctl restart ollama

# 若手動跑（注意：pkill 後常被自動重啟蓋掉，確認 pid 有換）：
pkill -f "ollama"
OLLAMA_HOST=0.0.0.0 OLLAMA_KEEP_ALIVE=-1 nohup ollama serve > /tmp/ollama.log 2>&1 &

# 驗證（要看到 *:11434 或 0.0.0.0，不是 127.0.0.1）
ss -tlnp | grep 11434
```

### 2.1.1 GPU 常駐與延遲（實驗前務必確認）

**背景（實測結論，別再照舊假設走）**：qwen2.5:14b 在 RTX 4070 上**本來就跑在 GPU**，
延遲由「LLM 生成多少 token」主導，不是 GPU 有沒有啟用、也不是模型大小。實測：

| 情境 | 生成量 | 延遲 |
|---|---|---|
| 短回應（say hi）| ~8 token | 0.8s |
| 蜜罐純輸出（帶 system prompt 約束）| ~40 token | **1.6s** |
| 裸問無約束（LLM 自由解釋）| ~400 token | 14.5s |
| idle unload 後第一次（冷啟動含載入 9.5GB）| — | ~9.6s |

兩個要點：

1. **設 `OLLAMA_KEEP_ALIVE=-1`（見 2.1）讓模型常駐**，消除 idle unload 後的冷啟動。
   否則實驗中 miss 間隔一拉長，每次都要重載 9.5GB 進顯存 → 冒出 ~9.6s 的假延遲。
2. 蜜罐的 system prompt 會強制「純 stdout、無解釋」→ 輸出天然很短 → 延遲穩定 1-2s。
   裸 `ollama run` 測到的 14.5s **不是** bug，是沒帶那套約束、LLM 進了「助教模式」。

```bash
# 確認 GPU 有在跑、模型有常駐
nvidia-smi                    # 生成當下 GPU-Util 應跳動、顯存吃到 ~9.5GB
ollama ps                     # 應見 qwen2.5:14b、PROCESSOR=100% GPU、UNTIL=Forever
                              #（設了 KEEP_ALIVE=-1 才會是 Forever）

# 預熱一次，讓模型先駐留再開始實驗（避免第一個 session 吃到冷啟動）
ollama run qwen2.5:14b "warmup"

# 熱推論 + 蜜罐風格約束的延遲基準（應 ~1-2s）
time ollama run qwen2.5:14b 'You are a Linux terminal. Output ONLY the raw stdout, no explanation, no markdown. Command: vmstat'
```

> ⚠️ 別看到 `nvidia-smi` 顯示 GPU-Util 0% 就以為沒用 GPU——模型 idle 被 unload 時本來就是 0%。
> 要在**生成當下**看，或直接看 `ollama ps` 的 PROCESSOR 欄。真相以 `journalctl -u ollama | grep -i gpu`
> 的 `offloaded N/N layers to GPU` 為準，不要看 `/tmp/ollama.log`（systemd 版那個檔是空的）。

### 2.2 模型已拉

```bash
curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"'
# 要看到 qwen2.5:14b（compose 預設）。沒有就：
ollama pull qwen2.5:14b
```

### 2.3 確認沒有另一個實驗在跑

```bash
# 有沒有殘留的單機蜜罐 / replay？
ps -ef | grep -E "honeyshell|replay_cowrie" | grep -v grep
# docker 蜜罐在不在？
docker compose -f ~/easypot/deploy/docker-compose.yml ps 2>/dev/null
```
要跑 A 就確認 docker 是停的；要跑 B/C 就確認單機蜜罐/replay 沒在跑。

---

## 3. 實驗 A：單機版全量 miss rate

**產出**：乾淨的全量 miss rate（報告目標二）。

### A0. 【防呆】先備份並清掉舊 audit

> **為什麼**：audit 是 append 模式，不清會把舊資料疊上去，miss rate 算重複。
> 之前停在 1880 的那份又髒又不完整，務必清掉重跑。

```bash
# 備份舊的（不是刪，保險）
[ -f /tmp/audit.jsonl ] && mv /tmp/audit.jsonl /tmp/audit_old_$(date +%m%d_%H%M).jsonl
# 確認乾淨
ls -la /tmp/audit.jsonl 2>/dev/null && echo "還在！沒清乾淨" || echo "OK 已清空"
```

### A1. 確認 docker 是停的（別搶 Ollama）

```bash
cd ~/easypot/deploy && docker compose down 2>/dev/null
docker compose ps    # 應該空的
```

### A2. 起單機蜜罐（另開一個終端，保持前景）

```bash
cd ~/easypot
python -m honeyshell --port 2222 --hostname happydog --llm \
    --audit-jsonl /tmp/audit.jsonl --log-level INFO 2>&1 | tee /tmp/honey.log
```

> - `--log-level INFO`（不是 DEBUG，DEBUG 會狂刷拖慢）。
> - **這個終端別關**，關了蜜罐就死，replay 會全部失敗。

### A3. 【防呆】先小量試跑，確認資料有進去

另開終端：

```bash
cd ~/easypot
# 先打 20 個 session 試水
python -m honeyshell.replay_cowrie ./input.csv --limit 20 --concurrency 2

# 確認 audit 有寫入
wc -l /tmp/audit.jsonl    # 應該 > 0
tail -3 /tmp/audit.jsonl  # 看有沒有 command 事件
```

沒問題再全量。

### A4. 全量 replay（掛著跑，可下班跑）

```bash
python -m honeyshell.replay_cowrie ./input.csv --concurrency 4
```

> - 7731 session，開 LLM 會較久（可能 1～2 小時+）。
> - 想中斷：Ctrl+C 停 replay（**別關蜜罐終端**），已跑的 audit 保留。
> - 想加速：`--concurrency 8` 或 `16`（asyncssh 是 async，開多幾乎零成本）。

### A5. 跑完 → 出報告（見第 5 節）

```bash
python -m honeyshell.analyze /tmp/audit.jsonl -f console   # 先看數字
python -m honeyshell.analyze /tmp/audit.jsonl -f md -o report_single.md
```

### A6. 收工

Ctrl+C 關掉蜜罐終端即可。

---

## 4. 實驗 B/C：docker 多台分流 + per-source

**產出**：證明「同一設計、多台部署、共享 LLM 池」（報告目標三 / §21），
並拿到 host1 vs host2 的 per-source 對比。

### B0. 【防呆】前提檢查

```bash
# 1. Ollama 綁 0.0.0.0（見 2.1）
ss -tlnp | grep 11434         # 要 *:11434，不是 127.0.0.1
# 2. 模型在（見 2.2）
curl -s http://localhost:11434/api/tags | grep qwen2.5:14b
# 3. 單機實驗沒在跑
ps -ef | grep -E "honeyshell|replay" | grep -v grep    # 應該空
```

### B1. 【防呆】確認機器上的 code 是最新的

> **為什麼**：改過的 compose（host1/host2 + LLM env）、Dockerfile（裝 httpx）、
> __main__.py（env fallback）如果沒更新到機器，會用到舊 image 出各種怪問題。

```bash
cd ~/easypot
# compose 是 host1/host2 且有 LLM env？
grep -E "HONEYPOT_HOSTNAME|EASYPOT_LLM:" deploy/docker-compose.yml
#   要看到 host1 / host2 / EASYPOT_LLM: "1"
# Dockerfile 裝 httpx？
grep "transport,llm" deploy/Dockerfile
#   要看到 '.[transport,llm]'
```
任一不對 → 先把最新 tar 解壓覆蓋：`tar xzf ~/easypot.tar.gz`

### B2. 【防呆】清掉舊 volume（含手動測試的髒 audit）

> **為什麼**：手動 ssh 測試打的命令（lscpu/vmstat…）會留在 audit，污染 C 的統計。
> 而且改過 volume 名/uid 時，殘留舊 volume 會出權限雷。

```bash
cd ~/easypot/deploy
docker compose down -v
# 確認清乾淨（列出的 easypot_* volume 應該不見）
docker volume ls | grep easypot
```

### B3. 無快取重建 + 起服務

```bash
docker compose build --no-cache      # 確保 httpx 真的裝進 image
docker compose up -d --force-recreate
docker compose ps                    # host1/host2/collector 三個都要 Up
                                     # collector 若 Restarting → 見 6.4 權限雷
```

### B4. 【防呆】驗證 LLM 真的通（三道確認）

```bash
# (1) httpx 進 image 了嗎
docker compose exec host1 python -c "import httpx; print('httpx', httpx.__version__)"

# (2) 容器連得到宿主機 Ollama 嗎（用 python，容器沒 wget/curl）
docker compose exec host1 python -c \
"import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags', timeout=5).read()[:80])"

# (3) 手動 ssh 打一個「真命令但沒內建」測 LLM 生成
ssh -p 2201 alice@127.0.0.1     # 密碼隨便
#   在裡面打：vmstat   （有延遲 + 像樣輸出 = LLM 通了）
#   別用 foobar123 測！它是亂碼，LLM 會正確回 not found，會誤導你以為壞了
#   exit 離開
```

> 若 (3) 的 vmstat 回 command not found，查蜜罐 log：
> `docker compose logs host1 | grep -i "unavailable\|httpx"`
> 出現 `httpx is not installed` → image 是舊的，回 B3 重 build。

### B5. 【防呆】驗證完，再清一次 audit（把 B4 手動測試筆清掉）

```bash
docker compose exec host1 sh -c "> /data/audit/host1.jsonl"
docker compose exec host2 sh -c "> /data/audit/host2.jsonl"
# collector 的合併檔也清（可選，重跑會重新合併）
docker compose exec collector sh -c "> /data/audit/_merged.jsonl" 2>/dev/null || true
```

### B6. replay 分流打兩台

```bash
cd ~/easypot
# (1) dry-run 先看分流（不連線）
python -m honeyshell.replay_cowrie ./input.csv \
    --target 127.0.0.1:2201 --target 127.0.0.1:2202 --dry-run
#   印：分流：127.0.0.1:2201=N、127.0.0.1:2202=M（大致各半）

# (2) 小量試跑
python -m honeyshell.replay_cowrie ./input.csv \
    --target 127.0.0.1:2201 --target 127.0.0.1:2202 --limit 20 --delay 0.1

# (3) 確認兩台都有資料進去
docker compose exec host1 sh -c "wc -l /data/audit/host1.jsonl"
docker compose exec host2 sh -c "wc -l /data/audit/host2.jsonl"
#   兩個都應 > 0

# (4) 沒問題 → 全量
python -m honeyshell.replay_cowrie ./input.csv \
    --target 127.0.0.1:2201 --target 127.0.0.1:2202 --concurrency 4
```

### B7. 出報告（從 collector 合併檔，帶 _source）

```bash
docker compose exec collector cat /data/audit/_merged.jsonl > /tmp/merged.jsonl
python -m honeyshell.analyze /tmp/merged.jsonl -f console       # 看 per-source
python -m honeyshell.analyze /tmp/merged.jsonl -f md -o report_docker.md
```

> per-source 區塊會列 host1 vs host2 的命令量與 miss。兩台是相同機器，
> **miss rate 應該接近** → 這就是「加台數不改架構」的一致性驗證。

### B8. 收工

```bash
docker compose down        # 停，保留 volume（host key 留著，下次指紋不變）
# 要徹底清：docker compose down -v
```

---

## 5. 出報告（analyzer 通用）

```bash
# 三種格式：
python -m honeyshell.analyze <audit.jsonl> -f console         # 終端看
python -m honeyshell.analyze <audit.jsonl> -f md -o report.md # markdown 檔
python -m honeyshell.analyze <audit.jsonl> -f json -o r.json  # 機器可讀
```

報告會自動：
- **過濾資料集互動噪音**（passwd 提示如 `New password:`），miss rate 不被灌高；
  底部會註明「已濾 N 筆」。
- 算 hit / miss rate、top_misses（最常走 LLM 的命令 = 規則覆蓋缺口）。
- per-source 對比（若資料有 `_source`，即 docker 合併檔才有）。
- 情報：憑證捕獲、session 時間線。

**看報告時記住**：
- `test`、`chpasswd`、`awk`、`vmstat` 等出現在 top_misses 是**真 miss**（真命令沒內建），
  不是噪音，別當錯誤。
- miss rate 是規則覆蓋缺口，不等於實際 LLM 呼叫數（部分 miss 走 cache）。

---

## 6. 常見故障排除（照症狀查）

### 6.1 replay 全部 session 失敗（✗）
蜜罐沒起來或 port 錯。
```bash
docker compose ps                       # 蜜罐 Up？
ssh -p 2201 alice@127.0.0.1             # 手動連得上？
# 單機版：ps -ef | grep honeyshell      # 蜜罐進程還在？
```

### 6.2 命令回 command not found，但該走 LLM
```bash
docker compose logs host1 | grep -i "unavailable\|httpx\|refused"
```
- `httpx is not installed` → image 舊，`docker compose build --no-cache` 重建。
- `refused` / 連線失敗 → Ollama 沒綁 0.0.0.0，見 2.1。
- **沒有任何 warning + 命令有延遲** → 其實正常，LLM 有工作（成功 log 是 DEBUG 級，
  INFO 模式看不到）。用 `foobar123` 測會誤導——它本來就該 not found。

### 6.3 容器連不到 Ollama
```bash
# 容器沒有 wget/curl，用 python 測：
docker compose exec host1 python -c \
"import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags',timeout=5).read()[:80])"
```
連不到 → 依序查：
1. `ss -tlnp | grep 11434` 是不是 `127.0.0.1`（要改 0.0.0.0，見 2.1）；
2. compose 有沒有 `extra_hosts: host.docker.internal:host-gateway`（Linux 必須）；
3. 防火牆擋 docker 網段 → `sudo ufw allow from 172.16.0.0/12 to any port 11434`。

### 6.4 collector 一直 Restarting（volume 權限雷）
蜜罐與 collector 兩 image 都是 uid 10001；volume 被不同 uid 先佔會寫不進。
```bash
docker compose down -v
docker volume ls | grep easypot        # 確認殘留的清掉
docker volume rm $(docker volume ls -q | grep easypot) 2>/dev/null
docker compose up --build -d
```

### 6.5 手動 pkill ollama 後又自動復活
systemd 或看門狗在重啟。別硬殺，用 2.1 的 systemctl 方式改設定重啟。
`ss` 看 pid 有沒有換就知道是不是被復活。

### 6.6 miss rate 高得離譜（>15%）
八成是資料集互動噪音沒被過濾（passwd 提示混進命令欄）。
analyzer 已內建過濾——確認你用的是最新 analyze.py：
```bash
grep -c is_interactive_noise ~/easypot/honeyshell/analyze.py   # 應 > 0
```

---

## 7. 血淚教訓速查表

| 症狀 | 根因 | 解法 |
|---|---|---|
| `httpx is not installed` | image 沒裝 httpx | `build --no-cache`（Dockerfile 已修為 `.[transport,llm]`） |
| 容器連不到 Ollama | Ollama 綁 127.0.0.1 | `OLLAMA_HOST=0.0.0.0`（見 2.1） |
| pkill 後 ollama 復活 | systemd 看門狗 | `systemctl edit ollama` 改設定，別 pkill |
| collector Restarting | volume uid 衝突 | `down -v` 清 volume 重來 |
| `foobar123` 一直 not found | 它是亂碼，LLM 正確回 not found | 用 `vmstat`/`lsblk` 測，別用亂碼 |
| miss rate 被灌高 | passwd 互動噪音 | analyzer 已內建過濾，用最新版 |
| audit 數字重複 | append 模式疊加 | 每次跑前清空 audit（A0 / B2 / B5） |
| 兩實驗數字互相污染 | 同時搶 Ollama | 分時段跑，一次只跑一個 |
| 手動測試筆混進統計 | ssh 測試留在 audit | 驗證後清 audit 再正式跑（B5） |

---

## 附：一頁極簡版（熟了以後看這個就好）

**實驗 A（單機）**
```bash
mv /tmp/audit.jsonl /tmp/audit_old.jsonl 2>/dev/null      # 清舊
docker compose -f ~/easypot/deploy/docker-compose.yml down # 別搶 Ollama
python -m honeyshell --port 2222 --hostname happydog --llm \
    --audit-jsonl /tmp/audit.jsonl --log-level INFO &       # 起蜜罐
python -m honeyshell.replay_cowrie ./input.csv --concurrency 4  # 全量
python -m honeyshell.analyze /tmp/audit.jsonl -f md -o report_single.md
```

**實驗 B/C（docker）**
```bash
ss -tlnp | grep 11434                     # 確認 *:11434
cd ~/easypot/deploy
docker compose down -v                    # 清 volume
docker compose build --no-cache && docker compose up -d
docker compose exec host1 python -c "import httpx; print(httpx.__version__)"  # 驗 httpx
docker compose exec host1 sh -c "> /data/audit/host1.jsonl"   # 清手動測試筆
docker compose exec host2 sh -c "> /data/audit/host2.jsonl"
cd ~/easypot
python -m honeyshell.replay_cowrie ./input.csv \
    --target 127.0.0.1:2201 --target 127.0.0.1:2202 --concurrency 4
docker compose -f deploy/docker-compose.yml exec collector \
    cat /data/audit/_merged.jsonl > /tmp/merged.jsonl
python -m honeyshell.analyze /tmp/merged.jsonl -f md -o report_docker.md
```