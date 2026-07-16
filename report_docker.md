# easypot 稽核聚合報告

- 事件總數：**48869**（略過壞行 0）

## LLM 效率（混合架構驗證）

| 指標 | 數值 |
|---|---|
| 命令總數 | 46158 |
| 規則命中 | 40960（88.74%） |
| 走 LLM (miss) | 5198（11.26%） |
| 已濾互動噪音 | 2498（資料集 passwd 提示等，不計入） |

> 註：Cowrie 公開資料集把互動程式輸出（如 `New password:`）混入命令欄，本次過濾 **2498** 筆，避免灌高 miss rate。此為資料清洗，raw log 保留原貌。

> N 台蜜罐的 LLM 負載約 = 總命令量 × **11.26%**，證明混合架構規模化成本可控。

**最常走 LLM 的命令（覆蓋缺口 / 未來補命令優先序）：**

| 命令 | 次數 |
|---|---|
| `awk` | 2497 |
| `w` | 1349 |
| `chpasswd` | 1249 |
| `apt` | 59 |
| `pacman` | 39 |
| `/bin/eyshcjdmzg` | 2 |
| `./112` | 1 |
| `history` | 1 |
| `(uname` | 1 |

## Session 時間線

- session 總數：**1558**
- 最活躍 session：`b34da523003f…` （36 命令、42.7s、憑證 0、錯誤 0）

## 情報產出

**攻擊者最常打的命令：**

| 命令 | 次數 |
|---|---|
| `grep` | 7888 |
| `uname` | 4172 |
| `cat` | 3952 |
| `echo` | 2805 |
| `cd` | 2750 |
| `wc` | 2701 |
| `which` | 2701 |
| `awk` | 2497 |
| `chmod` | 1445 |
| `rm` | 1371 |

**捕獲憑證（208 組）：**

| 使用者 | 密碼 | 來源 |
|---|---|---|
| `root` | `Enter new UNIX password: ` | host1 |
| `root` | `cat /proc/cpuinfo | grep name | head -n 1 | awk '{print $4,$5,$6,$7,$8,$9;}'` | host1 |
| `root` | `Enter new UNIX password: ` | host1 |
| `root` | `Enter new UNIX password: ` | host2 |
| `root` | `cat /proc/cpuinfo | grep name | head -n 1 | awk '{print $4,$5,$6,$7,$8,$9;}'` | host1 |
| `root` | `cat /proc/cpuinfo | grep name | head -n 1 | awk '{print $4,$5,$6,$7,$8,$9;}'` | host2 |
| `root` | `Enter new UNIX password: ` | host2 |
| `root` | `cat /proc/cpuinfo | grep name | head -n 1 | awk '{print $4,$5,$6,$7,$8,$9;}'` | host2 |
| `root` | `Enter new UNIX password: ` | host1 |
| `root` | `cat /proc/cpuinfo | grep name | head -n 1 | awk '{print $4,$5,$6,$7,$8,$9;}'` | host1 |
| `root` | `Enter new UNIX password: ` | host2 |
| `root` | `cat /proc/cpuinfo | grep name | head -n 1 | awk '{print $4,$5,$6,$7,$8,$9;}'` | host2 |
| `root` | `Enter new UNIX password: ` | host2 |
| `root` | `cat /proc/cpuinfo | grep name | head -n 1 | awk '{print $4,$5,$6,$7,$8,$9;}'` | host2 |
| `root` | `Enter new UNIX password: ` | host1 |

**各蜜罐對比：**

| 蜜罐 | 命令量 | miss |
|---|---|---|
| host1 | 23139 | 2625 |
| host2 | 23019 | 2573 |

