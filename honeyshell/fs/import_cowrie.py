"""One-shot converter: Cowrie ``fs.pickle`` -> honeyshell ``fs.json``.

Why a separate offline tool
---------------------------
The whole point of moving to JSON was to keep ``pickle`` out of the *runtime*
(unpickling untrusted data executes arbitrary code). This converter is the
only place pickle is touched, and it is meant to be run **once, offline, on a
pickle you trust** (your own Cowrie asset). The honeypot server never imports
this module.

    python -m honeyshell.fs.import_cowrie  path/to/fs.pickle  out/fs.json

Cowrie inode layout (index -> field)
------------------------------------
    0 name   1 type   2 uid   3 gid   4 size
    5 mode   6 ctime  7 contents/children   8 target(symlink)   9 realfile

``type`` constants in Cowrie (``shell/fs.py``): ``T_LINK, T_DIR, T_FILE, T_BLK,
T_CHR, T_SOCK, T_FIFO = range(0, 7)``. Rather than trust those numbers (they
have drifted across forks), we infer the node kind *structurally*, which is
robust: index-7 is a list -> directory; index-8 truthy -> symlink; else file.
The raw ``type`` int is used only as a tie-breaker / sanity check.
"""

from __future__ import annotations

import base64
import json
import pickle  # nosec B403 - trusted, offline conversion only
import sys
from typing import Any

# Cowrie index constants (for readability).
A_NAME, A_TYPE, A_UID, A_GID, A_SIZE = 0, 1, 2, 3, 4
A_MODE, A_CTIME, A_CONTENTS, A_TARGET = 5, 6, 7, 8

_DEFAULT_PERM = {"dir": 0o755, "file": 0o644, "link": 0o777}


def _get(inode: list, idx: int, default: Any = None) -> Any:
    return inode[idx] if len(inode) > idx else default


def _infer_type(inode: list) -> str:
    contents = _get(inode, A_CONTENTS)
    target = _get(inode, A_TARGET)
    if isinstance(contents, list):
        return "dir"
    if target:
        return "link"
    return "file"


def _convert(inode: list) -> dict[str, Any]:
    ntype = _infer_type(inode)
    name = _get(inode, A_NAME, "") or "/"
    mode = _get(inode, A_MODE, 0) or 0
    perm = mode & 0o777

    node: dict[str, Any] = {"type": ntype, "name": name}
    uid, gid = _get(inode, A_UID, 0) or 0, _get(inode, A_GID, 0) or 0
    if uid:
        node["uid"] = uid
    if gid:
        node["gid"] = gid
    if perm and perm != _DEFAULT_PERM[ntype]:
        node["perm"] = format(perm, "04o")
    ctime = _get(inode, A_CTIME, 0)
    if ctime:
        node["mtime"] = ctime

    if ntype == "dir":
        children = [_convert(c) for c in _get(inode, A_CONTENTS, []) or []]
        if children:
            node["children"] = children
    elif ntype == "link":
        node["target"] = _get(inode, A_TARGET, "") or ""
    else:  # file
        size = _get(inode, A_SIZE, 0) or 0
        node["size"] = int(size)
        contents = _get(inode, A_CONTENTS)
        if isinstance(contents, (bytes, bytearray)):
            try:
                node["contents"] = bytes(contents).decode("utf-8")
            except UnicodeDecodeError:
                node["contents_b64"] = base64.b64encode(bytes(contents)).decode()
        elif isinstance(contents, str) and contents:
            node["contents"] = contents
    return node


def convert_pickle(pickle_path: str) -> dict[str, Any]:
    """Load a Cowrie pickle and return our JSON-ready root dict."""
    with open(pickle_path, "rb") as fh:
        root = pickle.load(fh)  # nosec B301 - trusted, offline only
    if not isinstance(root, list):
        raise ValueError("unexpected pickle root; expected a Cowrie inode list")
    tree = _convert(root)
    if tree["type"] != "dir":
        raise ValueError("pickle root is not a directory inode")
    tree["name"] = "/"
    return tree


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "usage: python -m honeyshell.fs.import_cowrie <fs.pickle> <fs.json>",
            file=sys.stderr,
        )
        print(
            "WARNING: only run on a pickle you trust (unpickling is unsafe).",
            file=sys.stderr,
        )
        return 2
    tree = convert_pickle(argv[1])
    with open(argv[2], "w", encoding="utf-8") as fh:
        json.dump(tree, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
