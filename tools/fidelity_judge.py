"""擬真度判定器 —— 把三方輸出分類為 SALC / SALNLC / FALC / FALNLC。

判定哲學（HANDOFF §33；對齊論文 §4.2）
--------------------------------------
我們**不做**「輸出逐字相等」的比對——真機每次數值都不同（時間戳、記憶體用量、
PID），逐字比對毫無意義。判定看的是**格式/結構/OS 邏輯擬真**：

  * 「符合 OS 邏輯」(Logic Compliant) = 輸出具備真機該有的結構特徵
    （表頭、欄位、關鍵字、錯誤字串樣式），且成功/失敗狀態與真機一致。
  * 「成功」(Successful) = 命令在該情境下「推進了攻擊」——對正常命令是有像樣輸出、
    exit 0；對「本該失敗」的題（如讀不存在的檔）則相反：真機的正解是**失敗**，
    所以蜜罐也該失敗才算對。

四象限（論文 §4.2）：
  * SALC   成功 + 符合邏輯   —— 最佳：像真機且推進攻擊
  * SALNLC 成功 + 不符邏輯   —— 有輸出但結構錯，會露餡
  * FALC   失敗 + 符合邏輯   —— 該失敗時給出真機式正確錯誤（例如 cat 不存在的檔）
  * FALNLC 失敗 + 不符邏輯   —— 最糟：假成功或亂噴

每題在 probes.py 標了 ``ideal_class``（真機在此題應落哪類）當對照基準。判定器
輸出的是**受測系統**（easypot / Cowrie）落在哪類，再與 ideal_class 比對算「通過」。

locale 決定（HANDOFF 對話）
--------------------------
蜜罐模擬的目標系統設定為**英文 locale**（真實 VPS 幾乎皆然）。故錯誤字串以英文
基準（``No such file or directory``）判定；ground truth 採集機若為中文 locale，
其錯誤字串僅供結構參照，不作為蜜罐判定基準。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from tools.probes import Probe

# 四個類別常數（對齊論文 §4.2）
SALC = "SALC"
SALNLC = "SALNLC"
FALC = "FALC"
FALNLC = "FALNLC"


@dataclass
class Judgement:
    probe_id: int
    system: str            # "easypot" / "cowrie" / "real"
    predicted_class: str   # 判定落在哪一象限
    passed: bool           # 是否 == probe.ideal_class（受測系統這題有沒有過）
    reason: str            # 判定依據（可讀，寫進報告用）


# 常見的「命令不存在」樣式：蜜罐若把一個真實工具回成 not found，是擬真度失敗。
_NOT_FOUND_RE = re.compile(
    r"(?:command\s+not\s+found|:\s*not\s+found)\s*$", re.IGNORECASE
)
# 英文 locale 的「檔案不存在」錯誤（Q8 蜜罐基準）。同時接受中文 locale 的等義
# 字串，因為 ground truth 採集機可能是 zh_TW；判定「有沒有給出真機式錯誤」時
# 兩者皆算數（蜜罐仍以英文為目標，但真機基準不該因 locale 被誤判為不通過）。
_NO_SUCH_FILE_RE = re.compile(
    r"No such file or directory|沒有此一?檔案或目錄|沒有此檔案或目錄",
    re.IGNORECASE,
)


def _looks_successful(output: str, exit_code: int | None) -> bool:
    """判斷這次輸出在攻擊者眼中是否「成功」。

    有 exit_code 時以它為主（0 = 成功）。沒有時（例如某些蜜罐不回 exit code）
    退而求其次：有非空輸出、且不是 not-found/錯誤樣式，就當成功。
    """
    if exit_code is not None:
        return exit_code == 0
    text = output.strip()
    if not text:
        return False
    if _NOT_FOUND_RE.search(text):
        return False
    return True


def _is_logic_compliant(probe: Probe, output: str, exit_code: int | None) -> tuple[bool, str]:
    """判斷輸出是否具備真機該有的結構（符合 OS 邏輯）。

    規則：
      1. 若命令被回成 "command not found"（而該工具真實存在）→ 不符邏輯。
      2. **負面檢查**：抓 LLM 露餡的雜訊/幻覺（行首亂碼、不存在的掛載點、
         全零的行程時間），這些即使關鍵字都在也算不符邏輯。
      3. 對「本該失敗」的題（Q8）：符合邏輯 = 有真機式錯誤字串。
      4. Q10 跨命令時間一致性：專屬時間差檢查。
      5. 其餘題：檢查 probe.must_contain 的結構特徵是否都出現。
    """
    text = output

    # 規則 1：真實工具被回 not-found = 露餡
    if _NOT_FOUND_RE.search(text.strip()):
        return False, "被回成 command not found（真實工具不該如此）"

    # 規則 2：通用負面檢查（LLM 生成雜訊 / 幻覺）
    bad, why = _detect_llm_artifacts(probe, text)
    if bad:
        return False, why

    # 規則 4：Q10 跨命令時間一致性（probe 標了 special check）
    if probe.id == 10:
        nums = re.findall(r"\b(\d{9,})\b", text)
        if len(nums) >= 2:
            delta = int(nums[1]) - int(nums[0])
            if 1 <= delta <= 3:
                return True, f"兩個時間戳差 {delta}s，跨命令時間一致"
            return False, f"時間戳差 {delta}s，非真機的 ~2s（狀態不一致）"
        return False, "未見兩個時間戳，無法維持跨命令時間狀態"

    # 規則 3：本該失敗的題（FALC）
    if probe.ideal_class == FALC:
        if _NO_SUCH_FILE_RE.search(text):
            return True, "給出真機式的 'No such file or directory' 錯誤"
        return False, "未給出真機式錯誤（可能假裝成功或亂編內容）"

    # 規則 5：結構特徵比對
    missing = [k for k in probe.must_contain if k.lower() not in text.lower()]
    if missing:
        return False, f"缺少真機結構特徵：{missing}"

    # 規則 6：正向完整性——真機必有的硬結構，缺了即判不完整（露餡）。
    # 針對 LLM 輸出從嚴：沒有明顯幻覺 ≠ 完整。
    incomplete = [k for k in probe.must_have_all if k.lower() not in text.lower()]
    if incomplete:
        return False, f"輸出不完整，缺真機必有結構：{incomplete}"

    if probe.must_contain or probe.must_have_all:
        return True, "含全部必要結構且無缺漏"
    # 沒有結構要求的題（如 Q3 純看能否產出結果）：非空即算結構過。
    return (bool(text.strip()),
            "有非空輸出" if text.strip() else "空輸出")


# 行首雜訊：真機每行以空白或已知欄位起頭，LLM 偶爾冒出孤立字母（如 ip addr
# 輸出裡的 "c       valid_lft"）。抓「行首是單一非空白字母 + 大量空白」的樣式。
_LINE_NOISE_RE = re.compile(r"^[a-zA-Z]\s{3,}\S", re.MULTILINE)

# mount 幻覺掛載點：真機不會有這些。LLM 常編造 /dev/.mapper、nvdm、把 bdev
# 掛到裝置路徑等。白名單式抓「明顯不該出現在真實 mount 輸出的字串」。
_MOUNT_HALLUCINATIONS = ("/dev/.mapper", "/dev/.lvm", "nvdm", "bdev on /sys/bus")


def _detect_llm_artifacts(probe: Probe, text: str) -> tuple[bool, str]:
    """通用負面檢查：抓 LLM 生成的雜訊與幻覺，回 (是否露餡, 原因)。"""
    # 行首孤立字母雜訊（Q5 ip addr 的 "c valid_lft" 類）
    m = _LINE_NOISE_RE.search(text)
    if m:
        return True, f"行首雜訊（LLM 生成殘渣）：{m.group(0)!r}"

    # mount 幻覺掛載點（Q9）
    if "mount" in probe.command or "on /" in text and " type " in text:
        for h in _MOUNT_HALLUCINATIONS:
            if h in text:
                return True, f"幻覺掛載點（真機不存在）：{h!r}"

    # ps 全零時間：真機的 init/systemd 是長期行程，TIME 不會全 0:00。
    # ps 每行格式 ...START TIME COMMAND，TIME 是 COMMAND 前那一欄。只看資料行
    # （跳過表頭），若每行的 TIME 欄都是 0:00 → 露餡。
    if "ps" in probe.command:
        time_cols = []
        for line in text.splitlines():
            if line.strip().startswith("USER") or not line.strip():
                continue  # 表頭 / 空行
            toks = line.split()
            # 找 COMMAND 前的 TIME 欄：TIME 形如 M:SS 或 H:MM:SS，位置在倒數，
            # 抓該行最後一個符合時間樣式的 token。
            time_like = [t for t in toks if re.fullmatch(r"\d+:\d\d(?::\d\d)?", t)]
            if time_like:
                time_cols.append(time_like[-1])  # 最後一個 = TIME 欄
        if len(time_cols) >= 2 and all(t == "0:00" for t in time_cols):
            return True, "所有行程 TIME 全為 0:00（真機的 init 應有累積 CPU 時間）"

    return False, ""


def classify(probe: Probe, output: str, exit_code: int | None,
             system: str) -> Judgement:
    """把一次輸出分類到四象限，並判定是否 == probe 的理想類別。"""
    compliant, reason = _is_logic_compliant(probe, output, exit_code)

    # 「成功」語意：對本該失敗的題（FALC），真機的正解是失敗，故此處的
    # 「成功」指的是「達成該題的正確結果」= 該失敗時失敗、該成功時成功。
    if probe.ideal_class == FALC:
        # 正確結果 = 失敗且有正確錯誤。是否「達成」以 compliant 表示。
        succeeded_correctly = compliant
        predicted = FALC if compliant else FALNLC
    else:
        raw_success = _looks_successful(output, exit_code)
        if raw_success and compliant:
            predicted = SALC
        elif raw_success and not compliant:
            predicted = SALNLC
        elif not raw_success and compliant:
            predicted = FALC
        else:
            predicted = FALNLC
        succeeded_correctly = (predicted == probe.ideal_class)

    # 用 accept_classes 判定「過/不過」：多數題 = {ideal_class}（行為不變），
    # 少數有多種合法真機結果的題（如 Q19 crontab = {SALC, FALC}）兩者皆算通過。
    passed = (predicted in probe.accept_classes)
    return Judgement(
        probe_id=probe.id, system=system,
        predicted_class=predicted, passed=passed, reason=reason,
    )
