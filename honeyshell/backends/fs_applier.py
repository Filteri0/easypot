"""fs_applier — apply an LLM's structured C_i (state change) to the VirtualFS.

Why this exists (paper §3, HANDOFF "最大整合風險")
--------------------------------------------------
HoneyGPT models a command as ``(A_i, C_i, F_i) = LLM(...)`` where **C_i** is the
state change. If C_i lives only as a free-text note in the System State Register
(SR), the VirtualFS never actually changes: the LLM can *say* it created
``/tmp/x.sh`` while ``ls /tmp`` still shows nothing — a giveaway that unmasks the
honeypot. This module closes that gap.

Strategy (keeps the VFS as the single source of truth)
------------------------------------------------------
The prompt now asks the model to return **structured** ``fs_ops`` alongside the
prose ``state_change``. We apply those ops to the session's VirtualFS so the
tree and the model's memory agree. Anything the model *can't* express as an op
still rides along as the free-text SR note (fallback), matching HANDOFF's
"無法結構化的才留 SR 純文字".

Design decisions
----------------
* **Impact is *derived* here, not trusted from the model.** A local model scores
  Table 1 inconsistently; the actual op performed is a far more reliable signal.
  We return the max derived impact so the pruner ranks turns correctly. The
  caller uses this in preference to the model's own ``impact`` when any op
  applied. (Rubric mapping in ``_OP_IMPACT``.)
* **Failures are silent to the attacker.** If the model asks to ``rm`` a file
  that doesn't exist, or a path can't be resolved, we log a warning and skip
  that op — we do **not** surface an error, because a mismatch between the
  model's narrated output (A_i) and a Python traceback would itself be a tell.
  The honeypot must never crash on a bad op (mirrors the LLM-down resilience in
  ``resolver``/``llm_command``).
* **Paths resolve against the session cwd**, so a relative ``x.sh`` lands where
  the attacker is standing, exactly like the real shell.

Supported ops
-------------
    {"op": "mkdir",      "path": "/tmp/d"}                 -> makedirs (idempotent)
    {"op": "touch",      "path": "a.sh"}                   -> empty file
    {"op": "write_file", "path": "a.sh", "content": "..."} -> file w/ contents
    {"op": "rm",         "path": "/tmp/d"}                 -> recursive remove
    {"op": "mv",         "src": "a", "dst": "b"}           -> move/rename
    {"op": "cp",         "src": "a", "dst": "b"}           -> copy (file only)

Unknown ops / malformed entries are logged and skipped. ``cp`` on a directory is
not yet supported (files only); it's logged and skipped rather than half-applied.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from honeyshell.fs import FSError, VirtualFS

__all__ = ["AppliedOp", "ApplyReport", "apply_fs_ops", "normalise_fs_ops"]

_logger = logging.getLogger("honeyshell.backends.fs_applier")

# op name -> Table 1 impact (paper §3.2.2). Derived here rather than trusted
# from the model. rm is the destructive top of the scale; writes modify; create
# is low.
_OP_IMPACT: dict[str, int] = {
    "mkdir": 1,
    "touch": 1,
    "write_file": 2,
    "cp": 1,
    "mv": 2,
    "rm": 4,
}


@dataclass
class AppliedOp:
    """One op that was successfully applied (for the SR note / audit)."""

    op: str
    detail: str  # human-readable, e.g. "created file /tmp/x.sh"


@dataclass
class ApplyReport:
    """Outcome of applying a batch of fs_ops.

    ``applied`` lists the ops that took effect; ``impact`` is the max Table 1
    score across them (0 when nothing applied). ``notes`` renders the applied
    ops as SR text so the model's memory reflects what the VFS actually did —
    not what the model merely claimed.
    """

    applied: list[AppliedOp] = field(default_factory=list)
    impact: int = 0
    failed: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.applied)

    def notes(self) -> str:
        """Join applied-op details into one SR note ("" when nothing applied)."""
        return "; ".join(a.detail for a in self.applied)


def normalise_fs_ops(raw: Any) -> list[dict[str, Any]]:
    """Coerce a model-returned ``fs_ops`` value into a clean list of dicts.

    Tolerant of the shapes a local model actually emits: a missing/None value,
    a single dict instead of a list, or list entries that aren't dicts. Anything
    unusable is dropped (logged at debug), so downstream code always sees a
    well-formed list.
    """
    if raw is None:
        return []
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        _logger.debug("fs_ops not a list/dict: %r", type(raw))
        return []
    out: list[dict[str, Any]] = []
    for entry in raw:
        if isinstance(entry, dict) and isinstance(entry.get("op"), str):
            out.append(entry)
        else:
            _logger.debug("skipping malformed fs_op entry: %r", entry)
    return out


def apply_fs_ops(
    fs: VirtualFS, cwd: str, fs_ops: Any, *, uid: int = 0, gid: int = 0
) -> ApplyReport:
    """Apply structured ``fs_ops`` to ``fs`` relative to ``cwd``.

    Never raises: every op is guarded so a bad path can't crash the session.
    Returns an :class:`ApplyReport` the caller folds into SR/FL.
    """
    report = ApplyReport()
    for entry in normalise_fs_ops(fs_ops):
        op = entry["op"]
        try:
            detail = _dispatch(fs, cwd, op, entry, uid=uid, gid=gid)
        except FSError as exc:
            # Expected, benign: the model referenced a path that doesn't fit the
            # current tree. Skip silently (to the attacker); note for operators.
            _logger.warning("fs_op %s failed (%s); skipping", op, exc)
            report.failed += 1
            continue
        except Exception as exc:  # defensive: never crash the honeypot on an op
            _logger.warning("fs_op %s raised %r; skipping", op, exc)
            report.failed += 1
            continue
        if detail is None:
            _logger.debug("unsupported fs_op %r; skipping", op)
            report.failed += 1
            continue
        report.applied.append(AppliedOp(op, detail))
        report.impact = max(report.impact, _OP_IMPACT.get(op, 0))
    return report


def _dispatch(
    fs: VirtualFS, cwd: str, op: str, entry: dict[str, Any], *, uid: int, gid: int
) -> str | None:
    """Run one op; return a human note, or None if the op is unsupported.

    Path resolution is via VirtualFS which already handles cwd-relative paths.
    """
    if op == "mkdir":
        path = _need(entry, "path")
        # makedirs is idempotent (won't FileExists on an existing dir), which
        # matches a model that re-narrates a dir it "already made" a turn ago.
        fs.makedirs(path, cwd)
        return f"created directory {fs.normalize(path, cwd)}"

    if op == "touch":
        path = _need(entry, "path")
        fs.touch(path, cwd)
        return f"touched {fs.normalize(path, cwd)}"

    if op == "write_file":
        path = _need(entry, "path")
        content = entry.get("content", "")
        if not isinstance(content, str):
            content = str(content)
        fs.write_file(path, content, cwd, uid=uid, gid=gid)
        return f"wrote {fs.normalize(path, cwd)} ({len(content)} bytes)"

    if op == "rm":
        path = _need(entry, "path")
        # recursive so the model's "rm -rf /tmp/x" narration stays consistent;
        # DirectoryNotEmpty would otherwise desync tree vs. story.
        fs.remove(path, cwd, recursive=True)
        return f"removed {fs.normalize(path, cwd)}"

    if op == "mv":
        src = _need(entry, "src")
        dst = _need(entry, "dst")
        fs.move(src, dst, cwd)
        return f"moved {fs.normalize(src, cwd)} -> {fs.normalize(dst, cwd)}"

    if op == "cp":
        src = _need(entry, "src")
        dst = _need(entry, "dst")
        if fs.is_dir(src, cwd):
            # Recursive dir copy not modelled yet (files only); skip cleanly
            # rather than partially materialise a tree.
            _logger.debug("cp of a directory not supported: %s", src)
            return None
        data = fs.readbytes(src, cwd)  # raises NoSuchFile if src missing
        fs.write_file(dst, data, cwd, uid=uid, gid=gid)
        return f"copied {fs.normalize(src, cwd)} -> {fs.normalize(dst, cwd)}"

    return None  # unknown op


def _need(entry: dict[str, Any], key: str) -> str:
    """Fetch a required string field, raising FSError if absent/blank.

    Using FSError (not KeyError) routes a malformed op through the same silent
    skip path as a bad path, keeping the caller's error handling uniform.
    """
    val = entry.get(key)
    if not isinstance(val, str) or not val:
        raise FSError(f"missing '{key}'")
    return val
