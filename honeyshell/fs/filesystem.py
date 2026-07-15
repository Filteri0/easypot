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

import time as _time
from dataclasses import dataclass, field
from typing import Callable

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

    def __init__(self, root: FSNode | None = None,
                 clock: "Callable[[], float] | None" = None) -> None:
        if root is None:
            root = FSNode(name="/", ntype=DIR, perm=0o755)
        if root.ntype != DIR:
            raise FSError("root must be a directory")
        self.root = root
        # Wall-clock used to stamp mtimes on runtime-created/modified nodes
        # (mkdir/write/touch/symlink). Without this, new files default to
        # mtime=0.0 -> "Jan  1  1970" in `ls -l`, an instant honeypot tell when
        # an attacker does `echo x > f; ls -l`. Injectable so the honeypot can
        # pass its emulated (time-shifted) clock and tests can pin it.
        self._clock = clock or _time.time
        #: The uid/gid stamped on runtime-created nodes when a caller doesn't
        #: pass one explicitly. Set per-session to the login uid so
        #: `echo x > f` / `mkdir d` / `touch t` are owned by the logged-in user,
        #: not root. Defaults to 0 for bare/test contexts.
        self.default_uid = 0
        self.default_gid = 0

    def set_owner(self, uid: int, gid: int | None = None) -> None:
        """Set the default owner for subsequent runtime-created nodes."""
        self.default_uid = uid
        self.default_gid = uid if gid is None else gid

    def _now(self) -> float:
        return self._clock()

    def shift_mtimes(self, anchor_now: float) -> None:
        """Shift every node's mtime so the newest becomes ``anchor_now``.

        The shipped tree is built around a fixed 2024 timeline (reproducible
        fs.json). At load time we slide the whole tree forward so its most
        recent file sits at 'now', keeping the *relative* layering (install <
        packages < recent activity) intact while making absolute dates agree
        with ``date``/``uptime``. Without this, `ls -l` shows 2024 but `date`
        shows the real year — a giveaway. No-op if the tree is empty.
        """
        newest = self._max_mtime(self.root)
        if newest <= 0:
            return
        delta = anchor_now - newest
        self._apply_shift(self.root, delta)

    def _max_mtime(self, node: "FSNode") -> float:
        m = node.mtime
        for child in node.children.values():
            cm = self._max_mtime(child)
            if cm > m:
                m = cm
        return m

    def _apply_shift(self, node: "FSNode", delta: float) -> None:
        if node.mtime > 0:
            node.mtime += delta
        for child in node.children.values():
            self._apply_shift(child, delta)

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

    def access(self, path: str, mode: str, uid: int, gid: int = -1,
               cwd: str = "/", *, follow: bool = True) -> bool:
        """Return whether ``uid`` may access ``path`` for ``mode`` (any of
        'r','w','x'), using standard Unix owner/group/other permission bits.

        This is *advisory*: the VFS mutation methods stay permissive (so
        internal provisioning and tests aren't blocked); command implementations
        call this to emulate ``Permission denied`` where a real shell would.
        root (uid 0) bypasses all checks, matching real kernels. Missing path
        -> False (caller reports no-such-file separately if needed).
        """
        if uid == 0:
            return True
        try:
            node = self._lookup(path, cwd, follow=follow)
        except FSError:
            return False
        perm = node.perm
        if node.uid == uid:
            shift = 6           # owner triad
        elif gid >= 0 and node.gid == gid:
            shift = 3           # group triad
        else:
            shift = 0           # other triad
        bits = (perm >> shift) & 7
        need = {"r": 4, "w": 2, "x": 1}
        return all(bits & need[m] for m in mode)

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
        uid: int | None = None,
        gid: int | None = None,
        perm: int = 0o755,
    ) -> None:
        parent, name = self._parent_and_name(path, cwd)
        if name in parent.children:
            raise FileExists(self.normalize(path, cwd))
        u = self.default_uid if uid is None else uid
        g = self.default_gid if gid is None else gid
        parent.children[name] = FSNode(name, DIR, u, g, perm,
                                       mtime=self._now())

    def makedirs(self, path: str, cwd: str = "/", perm: int = 0o755) -> None:
        comps = self._split(path, cwd)
        node = self.root
        for name in comps:
            nxt = node.children.get(name)
            if nxt is None:
                nxt = FSNode(name, DIR, perm=perm, mtime=self._now())
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
        uid: int | None = None,
        gid: int | None = None,
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
            existing.mtime = self._now()  # writing a file bumps its mtime
            return
        if not create:
            raise NoSuchFile(self.normalize(path, cwd))
        u = self.default_uid if uid is None else uid
        g = self.default_gid if gid is None else gid
        parent.children[name] = FSNode(
            name, FILE, u, g, perm, size=len(data), contents=data,
            mtime=self._now(),
        )

    def touch(self, path: str, cwd: str = "/", *, perm: int = 0o644) -> None:
        parent, name = self._parent_and_name(path, cwd)
        existing = parent.children.get(name)
        if existing is None:
            parent.children[name] = FSNode(name, FILE, self.default_uid,
                                           self.default_gid, perm, size=0,
                                           mtime=self._now())
        else:
            existing.mtime = self._now()  # touch bumps mtime of existing file

    def symlink(self, target: str, linkpath: str, cwd: str = "/") -> None:
        parent, name = self._parent_and_name(linkpath, cwd)
        if name in parent.children:
            raise FileExists(self.normalize(linkpath, cwd))
        parent.children[name] = FSNode(name, LINK, perm=0o777, target=target,
                                       mtime=self._now())

    def chmod(self, path: str, perm: int, cwd: str = "/") -> None:
        """Set the permission bits on ``path``. Raises if it doesn't exist.

        Mechanism only — the FS stores the mode; whether a caller is *allowed*
        to chmod is policy the command layer applies (see chmod builtin).
        """
        node = self._lookup(path, cwd, follow=True)
        node.perm = perm & 0o7777

    def chown(
        self, path: str, cwd: str = "/", *,
        uid: int | None = None, gid: int | None = None,
    ) -> None:
        """Set owner uid and/or group gid on ``path``. Raises if absent."""
        node = self._lookup(path, cwd, follow=True)
        if uid is not None:
            node.uid = uid
        if gid is not None:
            node.gid = gid

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
