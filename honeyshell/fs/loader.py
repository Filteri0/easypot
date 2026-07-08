"""Load and save the virtual filesystem as human-editable JSON.

JSON schema (a node)
--------------------
    {
      "type": "dir" | "file" | "link",   # required
      "name": "etc",                      # required except root may omit / use "/"
      "uid": 0, "gid": 0,                 # optional, default 0
      "perm": "0755",                     # optional octal string; default by type
      "mtime": 0,                         # optional epoch seconds; default 0
      "size": 1234,                       # optional (files); realistic ls -l size
      "contents": "root:x:0:0:...\n",     # optional readable text (files)
      "contents_b64": "AAEC...",          # optional base64 (binary files)
      "target": "/etc/foo",               # required for links
      "children": [ ...nodes... ]         # dirs only
    }

The root object is a single ``dir`` node (``name`` "/" is conventional).
``perm`` is stored as an octal *string* (e.g. "0755") for readability; it maps
to ``FSNode.perm`` as an int. ``type`` bits are *not* encoded in ``perm`` — the
node ``type`` field carries that, keeping the JSON clean.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from honeyshell.fs.filesystem import (
    DIR,
    FILE,
    LINK,
    _DEFAULT_PERM,
    FSNode,
    VirtualFS,
)

__all__ = [
    "FSFormatError",
    "load_json",
    "load_dict",
    "save_json",
    "to_dict",
]

_VALID_TYPES = {DIR, FILE, LINK}


class FSFormatError(Exception):
    """Raised when the JSON does not match the filesystem schema."""


# --- JSON -> runtime -----------------------------------------------------


def _perm_from(value: Any, ntype: str, where: str) -> int:
    if value is None:
        return _DEFAULT_PERM[ntype]
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 8)
        except ValueError as exc:
            raise FSFormatError(f"{where}: bad octal perm {value!r}") from exc
    raise FSFormatError(f"{where}: perm must be octal string or int")


def _node_from(obj: dict[str, Any], where: str) -> FSNode:
    if not isinstance(obj, dict):
        raise FSFormatError(f"{where}: node must be an object")
    ntype = obj.get("type")
    if ntype not in _VALID_TYPES:
        raise FSFormatError(f"{where}: invalid type {ntype!r}")
    name = obj.get("name", "/")
    if not isinstance(name, str):
        raise FSFormatError(f"{where}: name must be a string")

    node = FSNode(
        name=name,
        ntype=ntype,
        uid=int(obj.get("uid", 0)),
        gid=int(obj.get("gid", 0)),
        perm=_perm_from(obj.get("perm"), ntype, where),
        mtime=float(obj.get("mtime", 0)),
    )

    if ntype == FILE:
        if "contents" in obj and obj["contents"] is not None:
            node.contents = str(obj["contents"]).encode("utf-8")
        elif "contents_b64" in obj and obj["contents_b64"] is not None:
            try:
                node.contents = base64.b64decode(obj["contents_b64"])
            except (ValueError, TypeError) as exc:
                raise FSFormatError(f"{where}: bad base64 contents") from exc
        # explicit size wins; else derive from contents (or 0)
        if "size" in obj and obj["size"] is not None:
            node.size = int(obj["size"])
        elif node.contents is not None:
            node.size = len(node.contents)
        else:
            node.size = 0

    elif ntype == LINK:
        target = obj.get("target")
        if not isinstance(target, str) or not target:
            raise FSFormatError(f"{where}: link requires a non-empty target")
        node.target = target

    elif ntype == DIR:
        for i, child in enumerate(obj.get("children", []) or []):
            cnode = _node_from(child, f"{where}/{child.get('name', i)}")
            node.children[cnode.name] = cnode

    return node


def load_dict(obj: dict[str, Any]) -> VirtualFS:
    """Build a :class:`VirtualFS` from a parsed JSON object."""
    root = _node_from(obj, "<root>")
    if root.ntype != DIR:
        raise FSFormatError("root node must be a directory")
    return VirtualFS(root)


def load_json(path: str | Path) -> VirtualFS:
    """Load a :class:`VirtualFS` from a JSON file on disk."""
    with open(path, encoding="utf-8") as fh:
        return load_dict(json.load(fh))


# --- runtime -> JSON -----------------------------------------------------


def _node_to(node: FSNode) -> dict[str, Any]:
    out: dict[str, Any] = {"type": node.ntype, "name": node.name}
    if node.uid:
        out["uid"] = node.uid
    if node.gid:
        out["gid"] = node.gid
    if node.perm != _DEFAULT_PERM[node.ntype]:
        out["perm"] = format(node.perm, "04o")
    if node.mtime:
        out["mtime"] = node.mtime

    if node.ntype == FILE:
        if node.size is not None:
            out["size"] = node.size
        if node.contents is not None:
            try:
                out["contents"] = node.contents.decode("utf-8")
            except UnicodeDecodeError:
                out["contents_b64"] = base64.b64encode(node.contents).decode("ascii")
    elif node.ntype == LINK:
        out["target"] = node.target or ""
    elif node.ntype == DIR and node.children:
        out["children"] = [_node_to(c) for c in node.children.values()]
    return out


def to_dict(vfs: VirtualFS) -> dict[str, Any]:
    """Serialise a :class:`VirtualFS` back to a JSON-ready dict."""
    return _node_to(vfs.root)


def save_json(vfs: VirtualFS, path: str | Path, *, indent: int = 2) -> None:
    """Write a :class:`VirtualFS` to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(to_dict(vfs), fh, indent=indent, ensure_ascii=False)
        fh.write("\n")
