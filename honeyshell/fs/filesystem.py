"""In-memory virtual filesystem for the honeypot shell.

Design lineage
--------------
Cowrie stores its fake filesystem as a nested ``list`` of fixed-index inodes
serialised with ``pickle``. We keep the *concept* (a metadata tree where most
files have no real content, plus embedded bytes for the few files attackers
``cat``) but drop pickle in favour of a human-editable JSON schema
(see ``fs/loader.py``) and an O(1) child lookup via ``dict``.

Runtime model
-------------
* A :class:`VirtualFS` owns a single ``FSNode`` tree (the root ``/``).
* All mutations (mkdir/write/rm) live only in this session's tree; nothing is
  persisted, matching Cowrie's throw-away-per-session semantics.
* Errors are raised as a small :class:`FSError` hierarchy so that command
  implementations can translate them into bash-like messages
  ("No such file or directory", "Is a directory", ...).

Simplifications (documented, revisit if fidelity demands)
--------------------------------------------------------
* Path normalisation is *lexical*: ``a/../b`` collapses before symlink
  resolution. True POSIX resolves symlinks first. This is predictable and
  sufficient for honeypot traffic.
* Permission bits are stored but *not enforced* here; enforcement (uid/gid vs
  mode) is a policy the interpreter/commands apply, so the FS stays mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "FSError",
    "NoSuchFile",
    "NotADirectory",
    "IsADirectory",
    "FileExists",
    "DirectoryNotEmpty",
    "FSNode",
    "FSStat",
    "VirtualFS",
    "DIR",
    "FILE",
    "LINK",
]

DIR = "dir"
FILE = "file"
LINK = "link"

_DEFAULT_PERM = {DIR: 0o755, FILE: 0o644, LINK: 0o777}
_MAX_SYMLINK_HOPS = 40


# --- error hierarchy -----------------------------------------------------


class FSError(Exception):
    """Base class for virtual-filesystem errors.

    ``path`` is the offending path; ``message`` is a bash-style reason so
    commands can render e.g. ``cat: /x: No such file or directory``.
    """

    message = "error"

    def __init__(self, path: str = "") -> None:
        self.path = path
        super().__init__(f"{path}: {self.message}" if path else self.message)


class NoSuchFile(FSError):
    message = "No such file or directory"


class NotADirectory(FSError):
    message = "Not a directory"


class IsADirectory(FSError):
    message = "Is a directory"


class FileExists(FSError):
    message = "File exists"


class DirectoryNotEmpty(FSError):
    message = "Directory not empty"


class SymlinkLoop(FSError):
    message = "Too many levels of symbolic links"


# --- nodes ---------------------------------------------------------------


@dataclass
class FSNode:
    """One filesystem entry.

    ``contents`` is the raw file bytes when embedded, else ``None`` (metadata
    only — the file lists but reads as empty, like most Cowrie files).
    ``size`` is stored independently of ``contents`` so ``ls -l`` can show a
    realistic size even for content-less files.
    """

    name: str
    ntype: str = FILE
    uid: int = 0
    gid: int = 0
    perm: int = 0o644
    mtime: float = 0.0
    size: int | None = None
    contents: bytes | None = None
    target: str | None = None  # symlink target
    children: dict[str, FSNode] = field(default_factory=dict)

    def effective_size(self) -> int:
        if self.ntype == DIR:
            return 4096
        if self.size is not None:
            return self.size
        return len(self.contents) if self.contents is not None else 0


@dataclass
class FSStat:
    """Lightweight stat result for command implementations."""

    name: str
    ntype: str
    uid: int
    gid: int
    perm: int
    size: int
    mtime: float
    target: str | None = None

    @property
    def is_dir(self) -> bool:
        return self.ntype == DIR

    @property
    def is_file(self) -> bool:
        return self.ntype == FILE

    @property
    def is_link(self) -> bool:
        return self.ntype == LINK


# --- filesystem ----------------------------------------------------------


class VirtualFS:
    """A mutable, in-memory Unix-like filesystem."""

    def __init__(self, root: FSNode | None = None) -> None:
        if root is None:
            root = FSNode(name="/", ntype=DIR, perm=0o755)
        if root.ntype != DIR:
            raise FSError("root must be a directory")
        self.root = root

    # -- path handling --

    def normalize(self, path: str, cwd: str = "/") -> str:
        """Lexically normalise ``path`` (relative to ``cwd``) to an absolute
        path string. Does not resolve symlinks or check existence."""
        comps = self._split(path, cwd)
        return "/" + "/".join(comps)

    def _split(self, path: str, cwd: str) -> list[str]:
        if not path:
            path = "."
        if path.startswith("/"):
            comps: list[str] = []
        else:
            comps = [c for c in cwd.strip("/").split("/") if c]
        for part in path.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if comps:
                    comps.pop()
            else:
                comps.append(part)
        return comps

    # -- traversal --

    def _walk(
        self, comps: list[str], follow_final: bool = True, _hops: int = 0
    ) -> FSNode:
        node = self.root
        for idx, name in enumerate(comps):
            if node.ntype != DIR:
                raise NotADirectory("/" + "/".join(comps[:idx]))
            child = node.children.get(name)
            if child is None:
                raise NoSuchFile("/" + "/".join(comps[: idx + 1]))
            is_final = idx == len(comps) - 1
            if child.ntype == LINK and (not is_final or follow_final):
                child = self._deref(child, comps[:idx], _hops)
            node = child
        return node

    def _deref(self, link: FSNode, parent_comps: list[str], hops: int) -> FSNode:
        if hops >= _MAX_SYMLINK_HOPS:
            raise SymlinkLoop("/" + "/".join(parent_comps + [link.name]))
        target = link.target or ""
        if target.startswith("/"):
            resolved = target
        else:
            resolved = "/" + "/".join(parent_comps) + "/" + target
        return self._walk(self._split(resolved, "/"), True, hops + 1)

    def _lookup(self, path: str, cwd: str, follow: bool = True) -> FSNode:
        return self._walk(self._split(path, cwd), follow_final=follow)

    # -- queries --

    def exists(self, path: str, cwd: str = "/") -> bool:
        try:
            self._lookup(path, cwd)
        except FSError:
            return False
        return True

    def is_dir(self, path: str, cwd: str = "/") -> bool:
        try:
            return self._lookup(path, cwd).ntype == DIR
        except FSError:
            return False

    def is_file(self, path: str, cwd: str = "/") -> bool:
        try:
            return self._lookup(path, cwd).ntype == FILE
        except FSError:
            return False

    def is_link(self, path: str, cwd: str = "/") -> bool:
        try:
            return self._lookup(path, cwd, follow=False).ntype == LINK
        except FSError:
            return False

    def stat(self, path: str, cwd: str = "/", follow: bool = True) -> FSStat:
        node = self._lookup(path, cwd, follow=follow)
        return FSStat(
            name=node.name,
            ntype=node.ntype,
            uid=node.uid,
            gid=node.gid,
            perm=node.perm,
            size=node.effective_size(),
            mtime=node.mtime,
            target=node.target,
        )

    def listdir(self, path: str = ".", cwd: str = "/") -> list[str]:
        node = self._lookup(path, cwd)
        if node.ntype != DIR:
            raise NotADirectory(self.normalize(path, cwd))
        return sorted(node.children)

    def scandir(self, path: str = ".", cwd: str = "/") -> list[FSStat]:
        node = self._lookup(path, cwd)
        if node.ntype != DIR:
            raise NotADirectory(self.normalize(path, cwd))
        out = []
        for name in sorted(node.children):
            c = node.children[name]
            out.append(
                FSStat(name, c.ntype, c.uid, c.gid, c.perm,
                       c.effective_size(), c.mtime, c.target)
            )
        return out

    def readbytes(self, path: str, cwd: str = "/") -> bytes:
        node = self._lookup(path, cwd)
        if node.ntype == DIR:
            raise IsADirectory(self.normalize(path, cwd))
        return node.contents if node.contents is not None else b""

    def readtext(self, path: str, cwd: str = "/", encoding: str = "utf-8") -> str:
        return self.readbytes(path, cwd).decode(encoding, errors="replace")

    def readlink(self, path: str, cwd: str = "/") -> str:
        node = self._lookup(path, cwd, follow=False)
        if node.ntype != LINK:
            raise FSError(self.normalize(path, cwd))  # not a symlink
        return node.target or ""

    # -- mutations --

    def _parent_and_name(self, path: str, cwd: str) -> tuple[FSNode, str]:
        comps = self._split(path, cwd)
        if not comps:
            raise FileExists("/")  # cannot create the root
        parent = self._walk(comps[:-1], follow_final=True)
        if parent.ntype != DIR:
            raise NotADirectory("/" + "/".join(comps[:-1]))
        return parent, comps[-1]

    def mkdir(
        self,
        path: str,
        cwd: str = "/",
        *,
        uid: int = 0,
        gid: int = 0,
        perm: int = 0o755,
    ) -> None:
        parent, name = self._parent_and_name(path, cwd)
        if name in parent.children:
            raise FileExists(self.normalize(path, cwd))
        parent.children[name] = FSNode(name, DIR, uid, gid, perm)

    def makedirs(self, path: str, cwd: str = "/", perm: int = 0o755) -> None:
        comps = self._split(path, cwd)
        node = self.root
        for name in comps:
            nxt = node.children.get(name)
            if nxt is None:
                nxt = FSNode(name, DIR, perm=perm)
                node.children[name] = nxt
            elif nxt.ntype != DIR:
                raise NotADirectory(name)
            node = nxt

    def write_file(
        self,
        path: str,
        data: bytes | str,
        cwd: str = "/",
        *,
        uid: int = 0,
        gid: int = 0,
        perm: int = 0o644,
        create: bool = True,
    ) -> None:
        if isinstance(data, str):
            data = data.encode("utf-8")
        parent, name = self._parent_and_name(path, cwd)
        existing = parent.children.get(name)
        if existing is not None:
            if existing.ntype == DIR:
                raise IsADirectory(self.normalize(path, cwd))
            existing.contents = data
            existing.size = len(data)
            return
        if not create:
            raise NoSuchFile(self.normalize(path, cwd))
        parent.children[name] = FSNode(
            name, FILE, uid, gid, perm, size=len(data), contents=data
        )

    def touch(self, path: str, cwd: str = "/", *, perm: int = 0o644) -> None:
        parent, name = self._parent_and_name(path, cwd)
        if name not in parent.children:
            parent.children[name] = FSNode(name, FILE, perm=perm, size=0)

    def symlink(self, target: str, linkpath: str, cwd: str = "/") -> None:
        parent, name = self._parent_and_name(linkpath, cwd)
        if name in parent.children:
            raise FileExists(self.normalize(linkpath, cwd))
        parent.children[name] = FSNode(name, LINK, perm=0o777, target=target)

    def remove(self, path: str, cwd: str = "/", *, recursive: bool = False) -> None:
        parent, name = self._parent_and_name(path, cwd)
        node = parent.children.get(name)
        if node is None:
            raise NoSuchFile(self.normalize(path, cwd))
        if node.ntype == DIR and node.children and not recursive:
            raise DirectoryNotEmpty(self.normalize(path, cwd))
        del parent.children[name]

    def move(self, src: str, dst: str, cwd: str = "/") -> None:
        sp, sname = self._parent_and_name(src, cwd)
        node = sp.children.get(sname)
        if node is None:
            raise NoSuchFile(self.normalize(src, cwd))
        dp, dname = self._parent_and_name(dst, cwd)
        # mv into an existing directory keeps the source name
        existing = dp.children.get(dname)
        if existing is not None and existing.ntype == DIR:
            dp = existing
            dname = sname
        del sp.children[sname]
        node.name = dname
        dp.children[dname] = node
