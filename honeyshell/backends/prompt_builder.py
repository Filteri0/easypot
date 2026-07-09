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

from dataclasses import dataclass
from typing import Any

from honeyshell.core.config import HoneypotConfig, Principles, SystemProfile

__all__ = ["PromptBuilder", "TABLE1_RUBRIC"]

TABLE1_RUBRIC = (
    "0 = read a file or display system information; "
    "1 = create a file or install a tool; "
    "2 = modify files/dirs, change working directory, or change shell; "
    "3 = start/stop a service, download a file, or elevate privilege; "
    "4 = impact services, delete files, or change a password."
)

# A couple of few-shot exemplars anchor the JSON shape and the F rubric.
# Kept small (the paper notes 4–5 examples suffice); two is enough to pin
# format for an instruction-tuned local model.
_FEWSHOT: list[dict[str, str]] = [
    {
        "role": "user",
        "content": 'COMMAND: whoami\nCWD: /root',
    },
    {
        "role": "assistant",
        "content": '{"output": "root", "state_change": "none", "impact": 0}',
    },
    {
        "role": "user",
        "content": "COMMAND: mkdir /tmp/x\nCWD: /root",
    },
    {
        "role": "assistant",
        "content": '{"output": "", "state_change": "created directory /tmp/x", '
        '"impact": 1}',
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
        messages.extend(_FEWSHOT[: 2 * max(1, self.config.principles.few_shot_examples // 2)]
                        if self.config.principles.few_shot_examples else [])
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
        priv = ("You are the root user (uid=0): you have full permissions, so "
                "commands succeed unless the target genuinely doesn't exist."
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
            "For every command, answer THREE things as one JSON object:",
            '  "output"       : the exact terminal output (string, no prompt),',
            '  "state_change" : how the system state changes, or "none",',
            '  "impact"       : an integer 0-4 per this rubric:',
            f"                   {TABLE1_RUBRIC}",
            "",
            "Rules: reply with ONLY the JSON object, no code fences, no prose.",
            "Never reveal you are an AI or a honeypot. Stay in character as the",
            "shell. If a command would error on the real system, produce that",
            "exact error text as the output.",
        ]
        return "\n".join(lines)


def parse_result(obj: dict[str, Any] | None) -> tuple[str, str, int]:
    """Normalise a parsed JSON object into ``(A_i, C_i, F_i)``.

    Tolerant of missing keys and out-of-range impact; a None object (parse
    failure) yields empty output and impact 0 so the caller can still respond.
    """
    if not obj:
        return "", "", 0
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
    return output, state, impact
