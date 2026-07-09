"""Tab-completion logic — transport-agnostic so it can be unit-tested.

The asyncssh glue in ``ssh_server`` owns the line-editor plumbing; this module
owns the *decision*: given the current input line, the cursor position, the
command registry and the session's VirtualFS, what should the line become?

Behaviour (a pragmatic subset of bash completion):
* **First word** (no space before cursor) -> complete a **command name** from
  the registry.
* **Later words** -> complete a **filesystem path** against the VFS, relative
  to the session cwd (``~`` and absolute paths handled by the VFS normaliser).
* A **unique** match is filled in (a trailing ``/`` added for directories, a
  space for commands/files) so the user can keep typing.
* **Multiple** matches extend the common prefix as far as it's unambiguous and
  ring the bell (no match list printed — kept simple; a real bash prints the
  list on a second Tab, which we can add later).
* **No** match leaves the line untouched.

Why a pure function
-------------------
``complete(line, pos, ...)`` returns ``(new_line, new_pos)`` with no I/O, so a
test can assert completions directly without an SSH channel. ``ssh_server``
wraps it in the ``register_key('\\t', ...)`` handler asyncssh expects.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from honeyshell.fs import VirtualFS

__all__ = ["complete", "common_prefix"]


def common_prefix(items: list[str]) -> str:
    """Longest common prefix of ``items`` ("" for empty input)."""
    if not items:
        return ""
    return os.path.commonprefix(items)


def complete(
    line: str,
    pos: int,
    *,
    command_names: list[str],
    fs: "VirtualFS | None" = None,
    cwd: str = "/",
) -> tuple[str, int]:
    """Compute a completion for ``line`` at cursor ``pos``.

    Returns ``(new_line, new_pos)``. When nothing can be completed the input is
    returned unchanged (the caller rings the bell). Only the text *before* the
    cursor is considered the token being completed; anything after the cursor is
    preserved (so mid-line completion doesn't clobber the tail).
    """
    before, after = line[:pos], line[pos:]
    # The token under the cursor = trailing run of non-space chars in `before`.
    # `leading` is everything before that token (preserved verbatim).
    stripped_len = len(before.rstrip(" "))
    token_start = before.rfind(" ", 0, stripped_len) + 1  # 0 if no space
    leading = before[:token_start]
    token = before[token_start:]
    # First word (the command) iff nothing but spaces precede the token.
    is_first_word = leading.strip() == ""

    if is_first_word:
        matches = sorted({n for n in command_names if n.startswith(token)})
        return _apply(matches, token, leading, after, is_path=False, fs=fs, cwd=cwd)

    # Path completion for later words.
    if fs is None:
        return line, pos
    matches = _path_matches(token, fs, cwd)
    return _apply(matches, token, leading, after, is_path=True, fs=fs, cwd=cwd)


def _path_matches(token: str, fs: "VirtualFS", cwd: str) -> list[str]:
    """Candidate paths in the token's directory that start with its basename.

    Splits the token into a directory part and a basename prefix, lists the
    directory in the VFS, and returns full token-shaped completions (preserving
    the user's directory prefix, e.g. ``etc/pa`` -> ``etc/passwd``).
    """
    if "/" in token:
        dir_part, _, base = token.rpartition("/")
        list_path = dir_part if dir_part else "/"
        prefix = dir_part + "/"
    else:
        list_path, base, prefix = ".", token, ""
    try:
        names = fs.listdir(list_path, cwd)
    except Exception:  # noqa: BLE001 - bad dir -> no completion, never raise
        return []
    return sorted(prefix + n for n in names if n.startswith(base))


def _apply(
    matches: list[str],
    token: str,
    leading: str,
    after: str,
    *,
    is_path: bool,
    fs: "VirtualFS | None",
    cwd: str,
) -> tuple[str, int]:
    """Turn candidate matches into a new (line, pos)."""
    if not matches:
        # Nothing matched: unchanged. Reconstruct exactly.
        line = leading + token + after
        return line, len(leading + token)

    if len(matches) == 1:
        completed = matches[0]
        suffix = _suffix_for(completed, is_path=is_path, fs=fs, cwd=cwd)
        new_before = leading + completed + suffix
        return new_before + after, len(new_before)

    # Multiple: extend to the common prefix (only if it grows the token).
    cp = common_prefix(matches)
    if len(cp) > len(token):
        new_before = leading + cp
        return new_before + after, len(new_before)
    # Ambiguous, no growth: leave unchanged (caller rings the bell).
    line = leading + token + after
    return line, len(leading + token)


def _suffix_for(
    completed: str, *, is_path: bool, fs: "VirtualFS | None", cwd: str
) -> str:
    """Trailing char after a unique completion: '/' for dirs, ' ' otherwise."""
    if is_path and fs is not None:
        try:
            if fs.is_dir(completed, cwd):
                return "/"
        except Exception:  # noqa: BLE001
            pass
        return " "
    # command name completion -> a space so the user types args next
    return " "
