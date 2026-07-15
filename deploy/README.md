# easypot Docker 部署（2 honeypot + collector，共享 LLM 池）

單機 `docker compose` 拓撲：兩台**完全相同**的蜜罐（同一份 fs.json、同一個
SystemProfile，只差 hostname host1/host2）把結構化事件寫到共享 volume，
collector tail 全部檔案、合併並標記來源。兩台都啟用 `--llm`，共用**宿主機**上
那一個 Ollama（`host.docker.internal`）——這正是論文 §3.4 hybrid + HANDOFF §21
「N 台無狀態蜜罐共享 1 個 LLM 池」的架構展示。

```
host1 (host :2201, --llm) ─┐
                           ├─► audit volume ─► collector ─► _merged.jsonl
host2 (host :2202, --llm) ─┘                                      │
                                                                  ▼
   宿主機 Ollama (qwen2.5:14b) ◄── 兩台 miss 命令共用 ──   honeyshell.analyze
```

**為何兩台一樣？** 目標不是比較不同人設，是證明「同一設計、多台部署、
共享一個 LLM 池」。機器相同 → 兩台 miss rate 應該接近 → 佐證「加台數不改架構、
LLM 負載 ≈ 總命令 × miss_rate」。per-source 對比因此是「一致性驗證」而非「差異比較」。

## 前提：宿主機要先跑 Ollama

兩台蜜罐的 `--llm` 會連宿主機的 Ollama，**compose 起之前**先確認：

```bash
ollama serve            # 另一終端保持執行
ollama pull qwen2.5:14b # 首次要拉模型
curl http://localhost:11434/api/tags   # 確認 Ollama 活著
```

若不想開 LLM（純規則模式，只驗資料鏈），把 compose 裡兩台的
`EASYPOT_LLM: "1"` 改成 `"0"` 即可，其餘不變。

## 起 / 停

```bash
cd deploy
docker compose up --build -d        # 建置並背景啟動
docker compose ps                   # 三個都要 Up（collector 不能是 Restarting）
docker compose logs -f collector    # 看合併後的即時事件流（每行帶 _source）
docker compose down                 # 停止（保留 volume）
docker compose down -v              # 停止並清掉 volume（host key / log 一起清）
```

## 連線測試

```bash
ssh -p 2201 alice@127.0.0.1         # host1，密碼隨便（accept_all）
ssh -p 2202 bob@127.0.0.1           # host2
```

進去打幾個命令（`ls`、`whoami`、`cat /proc/cpuinfo`、沒實作的 `foobar123`…），
collector 那邊會即時吐出對應 JSON 事件；沒實作的命令會走宿主機 Ollama 生成
（`docker compose logs -f host1` 開 DEBUG 可看生成細節）。

## 用真實流量餵兩台（replay 分流 → analyzer 出數字）

這是 B+C 的完整實驗流程。`replay_cowrie` 支援多 `--target`，會把 session
**round-robin 分流**到兩台（一條 session = 一條完整攻擊鏈，整條落同一台，不切分）。

```bash
# 1. 先 dry-run 看分流（不連線）
python -m honeyshell.replay_cowrie ./input.csv \
    --target 127.0.0.1:2201 --target 127.0.0.1:2202 --dry-run
# 會印：分流：127.0.0.1:2201=N session、127.0.0.1:2202=M session

# 2. 小量試跑
python -m honeyshell.replay_cowrie ./input.csv \
    --target 127.0.0.1:2201 --target 127.0.0.1:2202 --limit 20 --delay 0.1

# 3. 全量（量大用 --concurrency 加速；注意別和單機 replay 同時搶 Ollama）
python -m honeyshell.replay_cowrie ./input.csv \
    --target 127.0.0.1:2201 --target 127.0.0.1:2202 --concurrency 4

# 4. 出數字：直接吃 collector 合併好的 _merged.jsonl（帶 _source → 有 per-source 對比）
docker compose exec collector cat /data/audit/_merged.jsonl > /tmp/merged.jsonl
python -m honeyshell.analyze /tmp/merged.jsonl -f md -o report.md
```

analyzer 會自動過濾資料集的互動噪音（passwd 提示等，見 analyze.py），
miss_rate 不被灌高；per-source 區塊會列出 host1 vs host2 的命令量與 miss，
理想上兩台數字接近（一致性驗證）。

> ⚠️ **別和單機版 replay 同時跑**：若你也在跑 `python -m honeyshell`（port 2222）
> 的單機 replay，那台也吃同一個宿主機 Ollama，兩個實驗會搶 GPU、互相拖慢。
> docker 版實驗請單獨找時間跑。

## 事件輸出

- 每台蜜罐寫自己的檔：`/data/audit/host1.jsonl`、`host2.jsonl`（volume `audit`）。
- collector 合併成 `/data/audit/_merged.jsonl`，每行多一個 `_source` 欄位標記
  來源蜜罐（`host1`/`host2`），並同步印到 stdout。
- 事件型別：`CommandEvent`（每條命令，含 hit/miss）、`ErrorEvent`
  （攻擊者觸發的意外）、`LoginEvent`（sudo/su/passwd 憑證捕獲）。
  注意：目前**未 emit SessionStart**，故無 src_ip；session 以 session_id 關聯。

檢視合併結果：

```bash
docker compose exec collector cat /data/audit/_merged.jsonl
docker run --rm -v easypot_audit:/a alpine cat /a/_merged.jsonl   # 從 host 進 volume
```

## Host key（穩定指紋）

每台蜜罐把 SSH host key 存在各自的 `keys-1`/`keys-2` volume（`--host-key`），
重啟後指紋不變，攻擊者不會因 key 變動起疑。清 volume 才會重生。

## ⚠️ Docker volume 權限雷（排錯過，務必記住）

collector 與蜜罐兩個 image **統一 uid 10001**。Docker 建新具名 volume 時
從先初始化的 image 繼承 owner；若兩 image uid 不同，volume 會被一方擁有、
另一方寫不進 → collector crash-loop。**換過 uid 後必須清 volume**：

```bash
docker compose down -v
docker volume rm easypot_audit easypot_keys-1 easypot_keys-2   # 確認清乾淨
docker compose up --build -d
```

collector 另有韌性：開 `_merged.jsonl` 失敗會印錯誤 + 重試（不 crash）。

## host.docker.internal 連不到 Ollama？（Linux 常見）

compose 已為兩台加 `extra_hosts: ["host.docker.internal:host-gateway"]`
（Linux Docker 必須，Mac/Windows 內建）。若 LLM 呼叫失敗（蜜罐 log 出現
連線 refused / 生成退回 command not found），依序查：

1. 宿主機 Ollama 是否在跑、`curl http://localhost:11434/api/tags` 是否通；
2. Ollama 是否只綁 `127.0.0.1`（容器連不到）——需設 `OLLAMA_HOST=0.0.0.0`
   讓它聽所有介面後重啟 `ollama serve`；
3. 宿主機防火牆是否擋掉 docker bridge 到 11434 的流量。

蜜罐對 LLM 失敗是**韌性降級**（回 command not found，不 crash），所以連不到
不會讓蜜罐掛掉，只是 miss 命令沒生成內容——查 log 才會發現。

## 安全提醒

蜜罐是「故意被打」的機器。正式對外前務必：
- 放獨立網段 / VLAN / DMZ，封 outbound 到內網（限制爆炸半徑）；
- 本 compose 為方便把 SSH port 直接映射到 host，對外暴露前請加防火牆規則。

這是**部署層**的事，不在 honeyshell 程式範疇內。
