"""Builder for the sample ``data/fs.json`` filesystem.

Why this exists
---------------
The shipped ``fs.json`` was produced by an upstream conversion that collapsed
almost every node to an empty ``dir`` (files, symlinks and all), which both
broke the fs/command tests and made the honeypot trivially detectable (``cat
/etc/passwd`` returning a directory error, empty homes, no symlinks). Rather
than depend on an external, possibly-lossy Cowrie ``fs.pickle``, we build a
small, *type-correct* Debian-ish tree programmatically here. It is:

* **Version-controlled & reproducible** — re-run to regenerate ``fs.json``.
* **Type-correct** — dirs are dirs, files carry contents/size, symlinks carry
  a target (so ``/sbin/ls`` resolves through ``/sbin -> /bin``).
* **Test-aligned** — satisfies the exact expectations in ``tests/test_fs.py``
  and ``tests/test_commands.py`` (``/etc`` = {hostname, os-release, passwd},
  ``/etc/hostname`` = "svr04\\n", ``/root`` 0700/4096, ``/bin/ls`` 0755/133792,
  ``/sbin`` -> ``/bin``, ``/home/svc/.bashrc`` only).
* **Plausible for a honeypot** — standard FHS top-level dirs plus the files an
  attacker commonly inspects (passwd, os-release, /proc/{cpuinfo,meminfo}).

Usage
-----
    python -m honeyshell.fs.build_sample_fs                 # writes data/fs.json
    python -m honeyshell.fs.build_sample_fs out/fs.json     # custom path
    python -m honeyshell.fs.build_sample_fs --hostname box  # /etc/hostname body

The default hostname written into ``/etc/hostname`` is "svr04" to match the
tests; the *running* server's prompt hostname is a separate concern set via
``ServerConfig`` — ``cat /etc/hostname`` simply reflects this file's contents.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from honeyshell.fs.filesystem import DIR, FILE, LINK, FSNode, VirtualFS
from honeyshell.fs.loader import save_json

_DEFAULT_OUT = Path(__file__).resolve().parents[1] / "data" / "fs.json"
_MT = 1718150400.0  # fixed mtime for reproducible output


def _dir(name: str, *, perm: int = 0o755, uid: int = 0, gid: int = 0) -> FSNode:
    return FSNode(name, DIR, uid=uid, gid=gid, perm=perm, mtime=_MT)


def _file(
    name: str,
    contents: str | bytes = b"",
    *,
    perm: int = 0o644,
    uid: int = 0,
    gid: int = 0,
    size: int | None = None,
) -> FSNode:
    """A file node. If ``size`` is given it is stored independently of
    ``contents`` (a metadata-only file: realistic size, empty read)."""
    data = contents.encode() if isinstance(contents, str) else contents
    node = FSNode(name, FILE, uid=uid, gid=gid, perm=perm, mtime=_MT)
    node.contents = data if data else None
    node.size = size if size is not None else (len(data) if data else 0)
    return node


def _link(name: str, target: str) -> FSNode:
    return FSNode(name, LINK, perm=0o777, mtime=_MT, target=target)


def _add(parent: FSNode, *children: FSNode) -> FSNode:
    for c in children:
        parent.children[c.name] = c
    return parent


_PASSWD = (
    "root:x:0:0:root:/root:/bin/bash\n"
    "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
    "bin:x:2:2:bin:/bin:/usr/sbin/nologin\n"
    "sys:x:3:3:sys:/dev:/usr/sbin/nologin\n"
    "sync:x:4:65534:sync:/bin:/bin/sync\n"
    "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
    "sshd:x:105:65534::/run/sshd:/usr/sbin/nologin\n"
    "phil:x:1000:1000:phil,,,:/home/phil:/bin/bash\n"
    "svc:x:1001:1001::/home/svc:/bin/bash\n"
)

_OS_RELEASE = (
    'PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"\n'
    'NAME="Debian GNU/Linux"\n'
    'VERSION_ID="11"\n'
    'VERSION="11 (bullseye)"\n'
    "VERSION_CODENAME=bullseye\n"
    "ID=debian\n"
    'HOME_URL="https://www.debian.org/"\n'
)

_CPUINFO = (
    "processor\t: 0\n"
    "vendor_id\t: GenuineIntel\n"
    "model name\t: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz\n"
    "cpu MHz\t\t: 2400.000\n"
    "cache size\t: 35840 KB\n"
    "processor\t: 1\n"
    "vendor_id\t: GenuineIntel\n"
    "model name\t: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz\n"
    "cpu MHz\t\t: 2400.000\n"
    "cache size\t: 35840 KB\n"
)

_MEMINFO = (
    "MemTotal:        8167848 kB\n"
    "MemFree:         5432100 kB\n"
    "MemAvailable:    6931200 kB\n"
    "Buffers:          123456 kB\n"
    "Cached:          1345678 kB\n"
    "SwapTotal:       2097148 kB\n"
    "SwapFree:        2097148 kB\n"
)


def build(hostname: str = "svr04") -> VirtualFS:
    """Construct the sample filesystem tree."""
    root = _dir("/")

    # --- /bin : commands as metadata-only files (realistic size, empty read) ---
    bind = _dir("bin")
    _add(
        bind,
        _file("ls", perm=0o755, size=133792),
        _file("bash", perm=0o755, size=1234376),
        _file("cat", perm=0o755, size=35064),
        _file("sh", perm=0o755, size=125688),
        _file("echo", perm=0o755, size=35064),
        _file("pwd", perm=0o755, size=35064),
    )

    # /sbin is a symlink to /bin (usr-merge style), so /sbin/ls == /bin/ls.
    sbin = _link("sbin", "/bin")

    # --- /etc : exactly {hostname, os-release, passwd} at top level (per tests) ---
    etcd = _dir("etc")
    _add(
        etcd,
        _file("hostname", f"{hostname}\n"),
        _file("os-release", _OS_RELEASE),
        _file("passwd", _PASSWD, perm=0o644),
    )

    # --- /root : 0700, present in base tree with a couple of dotfiles ---
    rootd = _dir("root", perm=0o700)
    _add(
        rootd,
        _file(".bashrc", "# ~/.bashrc\nexport PS1='\\u@\\h:\\w\\$ '\n", perm=0o644),
        _file(".profile", "# ~/.profile\n", perm=0o644),
    )

    # --- /home : phil (populated) and svc (only a hidden .bashrc, per tests) ---
    homed = _dir("home")
    phil = _dir("phil", uid=1000, gid=1000)
    _add(
        phil,
        _file(".bashrc", "# phil bashrc\n", uid=1000, gid=1000),
        _file(".profile", "# phil profile\n", uid=1000, gid=1000),
    )
    svc = _dir("svc", uid=1001, gid=1001)
    _add(svc, _file(".bashrc", "# svc bashrc\n", uid=1001, gid=1001))
    _add(homed, phil, svc)

    # --- /proc : the readouts attackers commonly inspect ---
    procd = _dir("proc")
    _add(
        procd,
        _file("cpuinfo", _CPUINFO),
        _file("meminfo", _MEMINFO),
        _file("version", "Linux version 5.10.0-19-amd64 (debian-kernel)\n"),
    )

    # --- other standard FHS top-level directories (mostly empty stubs) ---
    root_children = [
        bind,
        _dir("boot"),
        _dir("dev"),
        etcd,
        homed,
        _dir("lib"),
        _dir("lib64"),
        _dir("media"),
        _dir("mnt"),
        _dir("opt"),
        procd,
        rootd,
        _dir("run"),
        sbin,
        _dir("srv"),
        _dir("sys"),
        _dir("tmp", perm=0o1777),
        _dir("usr"),
        _dir("var"),
    ]
    for c in root_children:
        root.children[c.name] = c

    return VirtualFS(root)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the sample fs.json tree.")
    ap.add_argument("out", nargs="?", default=str(_DEFAULT_OUT),
                    help="output path (default: honeyshell/data/fs.json)")
    ap.add_argument("--hostname", default="svr04",
                    help="contents of /etc/hostname (default: svr04)")
    args = ap.parse_args(argv)

    vfs = build(hostname=args.hostname)
    save_json(vfs, args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
