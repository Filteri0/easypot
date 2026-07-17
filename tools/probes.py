"""探測題庫（目標一：擬真度 SALC/FALC 對照）—— 題目定義與來源標註。

公信力設計（HANDOFF §33）
------------------------
學界沒有「權威欽定」的蜜罐探測題庫，所以公信力不來自「用了某份清單」，而來自
**出題方法可辯護、可複現、且來源與受測系統（easypot）隔離**：

  1. 題目來源皆為公開、與 easypot 無關的第三方標準：
     * MITRE ATT&CK 技術編號（業界公認公開框架；論文 §4.5.2 Table 7 亦用它分類）；
     * 真實 Cowrie 公開資料集[37][38]的高頻偵察 idiom（真實攻擊者實際打的命令）；
     * 蜜罐指紋文獻[30]（Bitter Harvest）描述的識破手法（公開的攻擊者思維）。
  2. 出題時**不看 easypot 會不會過**，並**主動納入預期 easypot 會輸的題**
     （見 ``expect_easypot_pass=False`` 的題：錯誤擬真、掛載表、跨命令狀態一致性），
     避免「只拿修過的 bug 當考卷」的選擇偏誤。
  3. ground truth 以**真實 Linux** 的輸出為準（tools/capture_ground_truth.sh 採集），
     而非以 easypot 自己的輸出為基準。

判定看的是**格式/結構/OS 邏輯擬真**（欄位、表頭、錯誤字串、跨命令一致性），
不是數值相等——所以 ground truth 跑在哪台真 Linux 都可以，具體數值不同不影響 SALC/FALC。

SALC/FALC（論文 §4.2）
---------------------
  * SALC = 成功攻擊且符合 OS 邏輯（輸出結構像真機、命令「成功」推進攻擊）。
  * SALNLC = 成功但不符 OS 邏輯（有輸出但結構/邏輯錯，會露餡）。
  * FALC = 失敗但符合 OS 邏輯（該失敗時給出真機式的正確錯誤）。
  * FALNLC = 失敗且不符 OS 邏輯（最糟：假成功或亂噴）。
本題庫每題標 ``ideal_class``（真機在此題「應該」落在哪類）當對照基準。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Probe:
    id: int
    command: str                 # 送進三方（easypot / Cowrie / 真機）的命令
    attack_technique: str        # ATT&CK 編號 + 名稱
    source: str                  # 題目出處（公開、與 easypot 無關）
    checkpoint: str              # 考點：這題在測什麼擬真面向
    ideal_class: str             # 真機在此題應落的類別（SALC / FALC）
    expect_easypot_pass: bool    # 誠實預測 easypot 會不會過（不藏；避免選擇偏誤）
    # 可接受的通過類別集合。多數題只有一種真機正解（= {ideal_class}，由
    # __post_init__ 自動填）。少數命令有**多種同樣合法**的真機結果，例如
    # crontab -l：有排程 → SALC、無排程 → FALC（"no crontab for" exit 1）都是
    # 真機該有的行為。這類題把兩者都列入，避免把合法真機行為誤判為失分（見
    # 校準討論：Q19 的 real 曾被判 FALC != ideal SALC 而失分）。判定器用
    # ``predicted in accept_classes`` 決定 passed，故對只有單一正解的題行為不變。
    accept_classes: frozenset = field(default=frozenset())
    # 判定該題「符合 OS 邏輯」的必要結構特徵（真機輸出應包含的欄位/關鍵字/樣式）。
    # 判定器用它做結構比對，而非數值相等。
    must_contain: list[str] = field(default_factory=list)
    # 正向完整性要求：真機**必然**具備、缺了就代表輸出不完整的結構。與
    # must_contain 的差別在嚴格度——must_contain 是「該有的特徵」，must_have_all
    # 是「任何真實 Linux 都鐵定有、缺一即露餡」的硬結構。針對 LLM 輸出的判定要嚴：
    # 「沒有明顯幻覺」不等於「完整」，一個真人 recon 看到 mount 缺根掛載/proc 一樣
    # 起疑。故對這類題補正向檢查，把「不完整」也判為不符邏輯。
    must_have_all: list[str] = field(default_factory=list)
    # 是否以「逐命令」模式送 easypot：對用 ; 串接的複合命令（如 Q10 的
    # date;sleep;date），設 True 讓 runner 把每段**各自獨立**呼叫 resolver，
    # 精確模擬真實蜜罐的逐命令、無跨命令狀態處理——這才能真測「跨命令狀態一致性」，
    # 而非讓 LLM 一次看到整條、照著 sleep 2 生出假一致的時間戳。
    per_command: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        # frozen dataclass：預設 accept_classes = {ideal_class}。未顯式指定的題
        # 沿用單一正解語意，判定行為與加此欄位前完全一致（向後相容）。
        if not self.accept_classes:
            object.__setattr__(
                self, "accept_classes", frozenset({self.ideal_class})
            )


PROBES: list[Probe] = [
    Probe(
        id=1,
        command="uname -a",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；真實流量高頻",
        checkpoint="格式擬真：核心資訊欄位順序（kernel name / hostname / "
                   "release / version / machine）齊全且順序正確",
        ideal_class="SALC",
        expect_easypot_pass=True,
        must_contain=["Linux"],
        notes="LLM 通常能過；作為 baseline 正例。",
    ),
    Probe(
        id=2,
        command="cat /proc/cpuinfo | head -30",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；論文 §4.5.2 Table 7（lspci/CPU 探測）",
        checkpoint="關鍵欄位存在性：processor / vendor_id / model name / "
                   "cpu MHz / flags 等真機必有欄位",
        ideal_class="SALC",
        expect_easypot_pass=True,
        must_contain=["processor", "model name", "flags"],
    ),
    Probe(
        id=3,
        command="cat /proc/cpuinfo | grep 'model name' | head -1 | awk '{print $4}'",
        attack_technique="T1082 System Information Discovery",
        source="真實 Cowrie 資料集[37][38]高頻 pipe idiom",
        checkpoint="跨工具管線一致性：cat→grep→awk 串起來，最終欄位提取結果"
                   "須與 Q2 的 model name 欄位自洽（考狀態/邏輯一致，非各自亂生）",
        ideal_class="SALC",
        expect_easypot_pass=True,
        must_contain=[],
        notes="awk 已內建處理 {print $N}（見 commands/impl/awk.py），"
              "但整條 pipe 的前段 cat /proc/cpuinfo 走 LLM；考兩者接得起來。",
    ),
    Probe(
        id=4,
        command="free -h",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；真實流量高頻",
        checkpoint="表頭與欄位格式：total/used/free/shared/buff/cache/available "
                   "欄位齊全，Mem: 與 Swap: 兩列，帶人類可讀單位",
        ideal_class="SALC",
        expect_easypot_pass=True,
        must_contain=["total", "used", "free", "Mem:"],
    ),
    Probe(
        id=5,
        command="ip addr",
        attack_technique="T1016 System Network Configuration Discovery",
        source="ATT&CK T1016；論文 §4.5.2 Table 7（arp/網路探測）",
        checkpoint="介面/位址格式：至少 lo + 一個實體介面，含 inet 行、"
                   "MAC（link/ether）、編號前綴（1: 2:）",
        ideal_class="SALC",
        expect_easypot_pass=True,
        must_contain=["lo", "inet", "link/"],
        # 真機必有：loopback 介面 + 至少一個實體介面的 IPv4（inet 需≥2）。
        must_have_all=["lo", "link/loopback"],
    ),
    Probe(
        id=6,
        command="cat /etc/resolv.conf",
        attack_technique="T1016 System Network Configuration Discovery",
        source="論文 §4.5.2 Table 7（明列的 DNS resolver 探測）",
        checkpoint="檔案內容擬真：nameserver 行格式正確",
        ideal_class="SALC",
        expect_easypot_pass=True,
        must_contain=["nameserver"],
    ),
    Probe(
        id=7,
        command="ps aux | head -5",
        attack_technique="T1057 Process Discovery",
        source="ATT&CK T1057；真實流量高頻（miner 偵察前置）",
        checkpoint="表頭欄位順序：USER PID %CPU %MEM VSZ RSS TTY STAT "
                   "START TIME COMMAND；且第一列通常是 root 的 PID 1",
        ideal_class="SALC",
        expect_easypot_pass=True,
        must_contain=["USER", "PID", "COMMAND"],
        # 真機必有：PID 1 的 init/systemd（第一列必為長期系統行程）。
        must_have_all=["/sbin/init"],
    ),
    Probe(
        id=8,
        command="cat /nonexistent_probe_file_xyz",
        attack_technique="—（錯誤擬真探測）",
        source="指紋文獻[30] Bitter Harvest：真機錯誤字串一致性",
        checkpoint="錯誤擬真：真機應回精確錯誤 "
                   "'cat: <path>: No such file or directory' 且 exit≠0；"
                   "easypot 的 LLM 可能過度熱心假裝成功或亂編內容 → 露餡",
        ideal_class="FALC",  # 真機此題「應該失敗且符合邏輯」
        expect_easypot_pass=False,  # 誠實預測：LLM 可能不報錯 → 預期會輸
        must_contain=["No such file or directory"],
        notes="主動納入的 easypot 預期失敗題（避免選擇偏誤）。",
    ),
    Probe(
        id=9,
        command="mount | head -10",
        attack_technique="T1497 Virtualization/Sandbox Evasion",
        source="指紋文獻[30]；ATT&CK T1497",
        checkpoint="掛載表擬真：真機應見 proc/sysfs/devpts/tmpfs 等偽檔案系統 "
                   "+ 根 / 掛載；蜜罐常給不出真實掛載結構 → 露餡",
        ideal_class="SALC",  # 真機：成功且結構乾淨（proc/sysfs/zfs 等真實掛載）
        expect_easypot_pass=False,  # 誠實預測：LLM 難生成一致的真實掛載表，
                                    # 常編幻覺掛載點（判定器負面檢查會抓到）
        must_contain=["on", "type"],
        # 真機必有：根掛載 + proc + sys。任何真實 Linux 都鐵定有這三者；
        # 缺任一 = 輸出不完整（即使沒有明顯幻覺，真人也會起疑）。
        must_have_all=["on / type", "/proc type proc", "/sys type sysfs"],
        notes="主動納入的 easypot 預期失敗題。判定器 _detect_llm_artifacts 會抓"
              "幻覺掛載點（如 /dev/.mapper、nvdm），故 easypot 生的假 mount 會被"
              "正確判為不符邏輯，即使含 on/type 關鍵字。",
    ),
    Probe(
        id=10,
        command="date +%s; sleep 2; date +%s",
        attack_technique="T1497 Virtualization/Sandbox Evasion",
        source="指紋文獻[30]：時間一致性 / 跨命令狀態",
        checkpoint="跨命令狀態一致性（§6 process model）：第二個時間戳應比第一個"
                   "大約 2（±1）。考蜜罐能否維持時間流動一致，而非兩次憑空生成"
                   "無關數字。這是 easypot 單命令無狀態設計最可能輸的題。",
        ideal_class="SALC",
        expect_easypot_pass=False,  # 誠實預測：無跨命令時間狀態 → 預期會輸
        must_contain=[],
        per_command=True,  # 逐命令跑：date、sleep、date 各自獨立 resolve，
                           # 暴露 easypot 單命令無狀態的真實行為（第二個 date
                           # 不知道第一個回了什麼）。這是反真人的結構性弱點。
        notes="主動納入的 easypot 預期失敗題；判定器對此題做數值差檢查（1<=Δ<=3）。"
              "逐命令模式下，easypot 兩次 date 各自生成、無關聯，時間差幾乎不可能"
              "落在 ~2s，故會誠實暴露『無跨命令狀態記憶』——對應論文 SR/H 記憶機制"
              "尚未涵蓋時間維度。報告可據此說明：對防腳本足夠，對防真人此為已知限制。",
    ),

    # ===== 擴充題 Q11–Q30（30 題完整版）=====
    # 來源同上：ATT&CK / 真實 Cowrie 流量 / 指紋文獻[30]。刻意維持約 6:4 的
    # 過:輸比例，並持續納入 easypot 預期會輸的題（跨命令狀態、系統特定表格、
    # 錯誤擬真、生成穩定性），避免選擇偏誤。

    Probe(
        id=11, command="id",
        attack_technique="T1033 System Owner/User Discovery",
        source="ATT&CK T1033；真實流量高頻（提權前確認身分）",
        checkpoint="格式：uid=0(root) gid=0(root) groups=... 樣式",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["uid=", "gid="],
    ),
    Probe(
        id=12, command="whoami",
        attack_technique="T1033 System Owner/User Discovery",
        source="ATT&CK T1033；真實流量最高頻之一",
        checkpoint="單行回傳當前使用者名（root）",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["root"],
    ),
    Probe(
        id=13, command="cat /etc/passwd | head -5",
        attack_technique="T1087 Account Discovery",
        source="ATT&CK T1087；真實流量高頻",
        checkpoint="格式：user:x:uid:gid:comment:home:shell 七欄冒號分隔；"
                   "第一列必為 root:x:0:0",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["root:", "/bin/"],
        must_have_all=["root:x:0:0"],
    ),
    Probe(
        id=14, command="uptime",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；指紋文獻[30]（時間一致性）",
        checkpoint="格式：當前時間 + up 時長 + users + load average；"
                   "up 時長須與模擬時鐘一致（時間注入修復後應合理）",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["load average", "up"],
    ),
    Probe(
        id=15, command="df -h",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；真實流量高頻",
        checkpoint="表頭 Filesystem Size Used Avail Use% Mounted；"
                   "必有根 / 掛載列",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["Filesystem", "Size", "Use%"],
        must_have_all=["Mounted on"],
    ),
    Probe(
        id=16, command="lscpu",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；真實流量（硬體偵察，挖礦前置）",
        checkpoint="Architecture / CPU(s) / Model name / 欄位齊全",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["Architecture", "CPU(s)", "Model name"],
    ),
    Probe(
        id=17, command="env",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；真實流量",
        checkpoint="環境變數 KEY=VALUE 逐行；必有 PATH、HOME",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["PATH="],
        must_have_all=["HOME="],
    ),
    Probe(
        id=18, command="netstat -tlnp",
        attack_technique="T1049 System Network Connections Discovery",
        source="ATT&CK T1049；真實流量（找開放服務）",
        checkpoint="表頭 Proto Recv-Q Send-Q Local Address；監聽埠格式",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["Proto", "Local Address", "LISTEN"],
    ),
    Probe(
        id=19, command="crontab -l",
        attack_technique="T1053 Scheduled Task/Job",
        source="ATT&CK T1053；真實流量（持久化偵察）",
        checkpoint="列出 cron 條目（SALC），或空/無 crontab 訊息（FALC）",
        # crontab -l 有兩種同樣合法的真機結果：有排程 → 列出條目、exit 0（SALC）；
        # 無排程（乾淨機的常態）→ "no crontab for <user>"、exit 1（FALC）。兩者
        # 都是真機該有的行為，故 accept 兩類。（校準：真機 ground truth 為無排程，
        # 原本 ideal=SALC 會把正確的 FALC 判成失分。）
        ideal_class="SALC", expect_easypot_pass=True,
        accept_classes=frozenset({"SALC", "FALC"}),
        must_contain=[],
    ),
    Probe(
        id=20, command="cat /etc/os-release",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；真實流量",
        checkpoint="NAME / VERSION / ID 欄位；須與 uname 宣稱的發行版自洽",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["NAME=", "VERSION"],
    ),
    # ---- 以下多為 easypot 預期會輸或高風險題 ----
    Probe(
        id=21, command="ls -la /root",
        attack_technique="T1083 File and Directory Discovery",
        source="ATT&CK T1083；真實流量高頻",
        checkpoint="ls -l 格式：權限/連結數/擁有者/群組/大小/日期/名；"
                   "必有 . 與 .. 目錄項",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["total", "drwx"],
        must_have_all=["."],
    ),
    Probe(
        id=22, command="dmesg | head -10",
        attack_technique="T1082 System Information Discovery",
        source="指紋文獻[30]；ATT&CK T1082",
        checkpoint="核心環形緩衝：[時間戳] 訊息 格式；真機開機訊息序列一致",
        ideal_class="SALC", expect_easypot_pass=False,  # 開機訊息序列難生成一致
        must_contain=[],
        notes="預期輸：dmesg 是高度系統特定的核心訊息，LLM 難生成連貫序列。",
    ),
    Probe(
        id=23, command="cat /proc/meminfo | head -5",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；真實流量",
        checkpoint="MemTotal/MemFree/MemAvailable 欄位 + kB 單位；"
                   "數值須與 free -h（Q4）自洽",
        ideal_class="SALC", expect_easypot_pass=False,  # 跨命令數值一致性難
        must_contain=["MemTotal", "kB"],
        must_have_all=["MemFree"],
        notes="預期輸：與 free -h 的跨命令數值一致性是無狀態設計的弱點。",
    ),
    Probe(
        id=24, command="ls -la /tmp; touch /tmp/probe_marker; ls -la /tmp",
        attack_technique="T1070 Indicator Removal / 狀態一致性",
        source="指紋文獻[30]：跨命令檔案系統狀態",
        checkpoint="touch 後第二次 ls 應出現 probe_marker（考跨命令 FS 狀態）",
        ideal_class="SALC", expect_easypot_pass=False,  # 無跨命令 FS 狀態
        must_contain=[],
        per_command=True,
        notes="預期輸：逐命令無狀態，第二次 ls 不會反映第一次 touch 的檔案。"
              "與 Q10 同類，測 FS 維度的跨命令狀態。",
    ),
    Probe(
        id=25, command="hostname",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；真實流量",
        checkpoint="單行主機名；須與 uname -a（Q1）宣稱的主機名一致",
        ideal_class="SALC", expect_easypot_pass=False,  # 跨命令主機名一致性
        must_contain=[],
        notes="預期輸/風險：hostname 須與 uname 的主機名一致，無狀態下兩命令"
              "可能各生不同名。考跨命令識別一致性。",
    ),
    Probe(
        id=26, command="cat /etc/shadow",
        attack_technique="T1003 OS Credential Dumping",
        source="ATT&CK T1003；真實流量（憑證竊取）",
        checkpoint="root 應可讀；格式 user:$hash:... ；或真機式權限錯誤",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=["root:"],
        notes="高風險題：root 讀 shadow 應成功；考 LLM 會不會過度謹慎拒絕"
              "（安全政策誤觸）而非扮演成功。",
    ),
    Probe(
        id=27, command="w",
        attack_technique="T1033 System Owner/User Discovery",
        source="ATT&CK T1033；指紋文獻[30]（登入時間一致性）",
        checkpoint="表頭 USER TTY FROM LOGIN@ IDLE；登入時間須與模擬時鐘一致",
        ideal_class="SALC", expect_easypot_pass=False,  # 登入 session 狀態
        must_contain=["USER", "TTY"],
        notes="預期輸：w 需要真實登入 session 狀態，無狀態難維持一致。",
    ),
    Probe(
        id=28, command="last | head -5",
        attack_technique="T1033 System Owner/User Discovery",
        source="ATT&CK T1033；真實流量",
        checkpoint="登入歷史：user tty host 時間範圍；時間須合理且遞減",
        ideal_class="SALC", expect_easypot_pass=False,  # 登入歷史序列
        must_contain=[],
        notes="預期輸：登入歷史是狀態性資料，LLM 難生成時間連貫的序列。",
    ),
    Probe(
        id=29, command="cat /proc/version",
        attack_technique="T1082 System Information Discovery",
        source="ATT&CK T1082；指紋文獻[30]（跨來源版本一致性）",
        checkpoint="核心版本字串；須與 uname -a（Q1）的 kernel 版本完全一致",
        ideal_class="SALC", expect_easypot_pass=False,  # 跨命令版本一致性
        must_contain=["Linux version"],
        notes="預期輸：/proc/version 的 kernel 版本須與 uname 一致，無狀態下"
              "兩命令可能各生不同版本號。指紋文獻[30]的典型交叉驗證手法。",
    ),
    Probe(
        id=30, command="sudo -l",
        attack_technique="T1069 Permission Groups Discovery",
        source="ATT&CK T1069；真實流量（提權偵察）",
        checkpoint="列出 sudo 權限；root 應顯示 (ALL) ALL 或類似",
        ideal_class="SALC", expect_easypot_pass=True,
        must_contain=[],
        notes="考 LLM 對 sudo -l 的合理模擬（root 全權限）。",
    ),
]


def summary() -> str:
    n = len(PROBES)
    expect_pass = sum(p.expect_easypot_pass for p in PROBES)
    return (f"{n} 題；預期 easypot 過 {expect_pass}、"
            f"預期輸 {n - expect_pass}（主動納入的失敗題，避免選擇偏誤）")


if __name__ == "__main__":
    print(summary())
    for p in PROBES:
        flag = "會過" if p.expect_easypot_pass else "預期輸"
        print(f"Q{p.id:2d} [{flag}] {p.attack_technique:45s} {p.command}")
