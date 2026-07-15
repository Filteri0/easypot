"""Shared base + helper for text-processing builtins (head/tail/wc/grep).

Extracted from the former ``textutil.py``. ``_FileOrStdin`` yields
``(label, text)`` for each file operand or, given none, for stdin — the shape
that lets these commands compose in pipelines (``cat x | grep y | wc -l``).
``_int_flag`` parses ``-N`` style counts. Underscore-prefixed so ``discover()``
imports it harmlessly (it registers no command). Behaviour unchanged.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.fs import FSError

__all__ = ["_FileOrStdin", "_int_flag", "check_read"]


def check_read(ctx, path: str) -> str | None:
    """Return a ``Permission denied`` message if ``ctx``'s user can't read
    ``path``, else None.

    Centralises the read-permission gate so every file-reading builtin
    (cat/head/tail/grep/... and the ``<`` redirect) behaves identically. Uses
    the VFS's single ``access()`` judge (root bypasses; owner/group/other rwx).
    Only meaningful for existing readable files — callers still surface
    no-such-file / is-a-directory via the normal readtext error path, so we
    only veto when the path resolves to something the user provably can't read.
    Non-existent paths return None here (the read itself reports them), keeping
    the "denied" message reserved for genuine permission failures — matching
    real shells, which say "Permission denied" only for files that exist.
    """
    fs = ctx.fs
    try:
        if not fs.exists(path, ctx.cwd):
            return None
    except FSError:
        return None
    uid = ctx.uid
    gid = getattr(ctx, "login_uid", None)
    gid = gid if gid is not None else uid
    if fs.access(path, "r", uid, gid, ctx.cwd):
        return None
    return "Permission denied"


def _int_flag(args: list[str], flag: str, default: int) -> tuple[int, list[str]]:
    """Extract ``-N`` count (e.g. ``-n 20`` or ``-n20``) plus a bare ``-20``.

    Returns (count, remaining_operands). Non-numeric or absent -> default.
    """
    count = default
    operands: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == flag:  # "-n" "20"
            if i + 1 < len(args) and args[i + 1].lstrip("-").isdigit():
                count = int(args[i + 1])
                i += 2
                continue
            i += 1
            continue
        if a.startswith(flag) and a[len(flag):].lstrip("-").isdigit():  # "-n20"
            count = int(a[len(flag):])
            i += 1
            continue
        if a.startswith("-") and a != "-" and a[1:].isdigit():  # "-20"
            count = int(a[1:])
            i += 1
            continue
        operands.append(a)
        i += 1
    return count, operands


class _FileOrStdin(Command):
    """Helper base: yield (label, text) for each operand or for stdin."""

    async def _inputs(self, operands: list[str]):
        if not operands:
            yield None, await self.read_all()
            return
        for path in operands:
            if path != "-":
                denied = check_read(self.ctx, path)
                if denied is not None:
                    self.errline(f"{self.prog}: {path}: {denied}")
                    yield path, None
                    continue
            try:
                yield path, self.ctx.fs.readtext(path, self.ctx.cwd)
            except FSError as e:
                self.errline(f"{self.prog}: {path}: {e.message}")
                yield path, None
