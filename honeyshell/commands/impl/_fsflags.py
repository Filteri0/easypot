"""Shared flag-splitting helper for filesystem-mutating builtins.

Extracted from the former ``filesystem.py`` where ``_split_flags`` was shared by
mkdir/rmdir/rm/touch/mv/cp. Lives in an underscore-prefixed module so the
registry's ``discover()`` pass imports it harmlessly (it registers nothing) and
the six command files import ``_split_flags`` from here instead of duplicating
it. Behaviour is unchanged.
"""

from __future__ import annotations

__all__ = ["_split_flags", "parent_writable", "path_readable"]


def _perm_ids(ctx):
    """(uid, gid) a command should check permissions as. login_uid doubles as
    the primary gid in this model (users get a private group), matching the
    convention already used by the read/write gates elsewhere."""
    uid = ctx.uid
    gid = getattr(ctx, "login_uid", None)
    return uid, (gid if gid is not None else uid)


def parent_writable(ctx, path: str) -> bool:
    """Whether ``ctx``'s user may create/remove the directory entry ``path``.

    In Unix, adding or removing a name in a directory is governed by write (and
    search) permission on the *parent directory*, NOT on the target file — this
    is why root-owned files in a world-writable /tmp can be deleted by anyone.
    rm/mv (removing the source name) and cp/mv (creating the dest name) all
    reduce to this check. root bypasses (access() handles uid 0). A missing
    parent returns True here so the command's own "No such file" path reports
    it rather than a misleading "Permission denied".
    """
    fs = ctx.fs
    norm = fs.normalize(path, ctx.cwd)
    parent = norm.rsplit("/", 1)[0] or "/"
    try:
        if not fs.exists(parent, ctx.cwd):
            return True
    except Exception:  # noqa: BLE001
        return True
    uid, gid = _perm_ids(ctx)
    return fs.access(parent, "w", uid, gid, ctx.cwd)


def path_readable(ctx, path: str) -> bool:
    """Whether ``ctx``'s user may read ``path`` (for cp's source). Missing path
    -> True so the caller surfaces the real stat/no-such-file error."""
    fs = ctx.fs
    try:
        if not fs.exists(path, ctx.cwd):
            return True
    except Exception:  # noqa: BLE001
        return True
    uid, gid = _perm_ids(ctx)
    return fs.access(path, "r", uid, gid, ctx.cwd)


def _split_flags(args: list[str]) -> tuple[set[str], list[str]]:
    """Partition argv tail into a set of flag chars and positional operands.

    ``-rf`` becomes {'r','f'}; ``--`` stops flag parsing; a bare ``-`` is an
    operand. Long options (``--recursive``) are recorded by their full text.
    """
    flags: set[str] = set()
    operands: list[str] = []
    no_more = False
    for a in args:
        if no_more or not a.startswith("-") or a == "-":
            operands.append(a)
        elif a == "--":
            no_more = True
        elif a.startswith("--"):
            flags.add(a[2:])
        else:
            flags.update(a[1:])
    return flags, operands
