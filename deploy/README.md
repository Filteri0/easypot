# easypot Docker 部署（2 honeypot + collector）

單機 `docker compose` 拓撲：兩台蜜罐把結構化事件寫到共享 volume，collector
tail 全部檔案、合併並標記來源。**尚未加人設 / LLM**（純規則模擬 shell），
之後再依 honeypot 加 `--llm` 與各自的 `--fs` 做差異化。

```
honeypot-a  (host :2201) ─┐
                          ├─► audit volume ─► collector ─► _merged.jsonl + stdout
honeypot-b  (host :2202) ─┘
```

## 起 / 停

```bash
cd deploy
docker compose up --build -d        # 建置並背景啟動
docker compose ps                   # 看狀態
docker compose logs -f collector    # 看合併後的即時事件流
docker compose down                 # 停止（保留 volume）
docker compose down -v              # 停止並清掉 volume（host key / log 一起清）
```

## 連線測試

```bash
ssh -p 2201 alice@127.0.0.1         # honeypot-a（hostname=web01），密碼隨便
ssh -p 2202 alice@127.0.0.1         # honeypot-b（hostname=db01）
```

進去打幾個命令（`ls`、`whoami`、`cat /etc/passwd`、`sudo -i`…），
collector 那邊會即時吐出對應的 JSON 事件。

## 事件輸出

- 每台蜜罐寫自己的檔：`/data/audit/honeypot-a.jsonl`、`honeypot-b.jsonl`
  （volume `audit`）。
- collector 合併成 `/data/audit/_merged.jsonl`，每行多一個 `_source` 欄位標記
  來源蜜罐，並同步印到 stdout（`docker compose logs collector` 看得到）。
- 事件型別目前有 `CommandEvent`（每條命令，含 hit/miss）、`ErrorEvent`
  （攻擊者觸發的意外）、`LoginEvent`（sudo/su/passwd 憑證捕獲）。

檢視合併結果：

```bash
docker compose exec collector cat /data/audit/_merged.jsonl
# 或從 host 進 volume
docker run --rm -v easypot_audit:/a alpine cat /a/_merged.jsonl
```

## Host key（穩定指紋）

每台蜜罐把 SSH host key 存在各自的 `keys-*` volume（`--host-key`），
重啟後指紋不變，攻擊者不會因為 key 變動起疑。清 volume 才會重生。

## 之後要接的（analyzer）

collector 刻意只做「收集 + 合併」，不分析。下一步是獨立 analyzer 讀
`_merged.jsonl` 做結構化聚合（pandas / DuckDB / SQL）——因為事件已被蜜罐標註
`hit`/`resolved_name` 等欄位，聚合先走結構化而非再丟給 LLM（會重複）。

## 安全提醒

蜜罐是「故意被打」的機器。正式對外前務必：
- 放獨立網段 / VLAN / DMZ，封 outbound 到內網（限制爆炸半徑）；
- 本 compose 為方便把 SSH port 直接映射到 host，對外暴露前請加防火牆規則。

這是**部署層**的事，不在 honeyshell 程式範疇內。
