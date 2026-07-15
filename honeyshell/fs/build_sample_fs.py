"""Builder for the sample ``data/fs.json`` filesystem.

Why this exists
---------------
The shipped ``fs.json`` was produced by an upstream conversion that collapsed
almost every node to an empty ``dir``, which both broke the fs/command tests
and made the honeypot trivially detectable. Rather than depend on an external,
possibly-lossy Cowrie ``fs.pickle``, we build a *type-correct* Debian-ish tree
programmatically here. It is:

* **Version-controlled & reproducible** — re-run to regenerate ``fs.json``.
* **Type-correct** — dirs are dirs, files carry contents/size, symlinks carry
  a target (so ``/sbin/ls`` resolves through ``/sbin -> /bin``).
* **Test-aligned** — satisfies fs/command tests (``/root`` 0700/4096,
  ``/bin/ls`` 0755/133792, ``/sbin`` -> ``/bin``, ``/home/svc/.bashrc`` only).
* **Plausible for a honeypot** — see the persona note below.

Persona — a production database server (``happydog``)
-----------------------------------------------------
The tree is dressed as a *busy PostgreSQL 13 + Redis* host, a high-value target
that entices attackers to dig in (paper's goal of deeper engagement). The
"lived-in" evidence an attacker's recon scripts read is deliberately seeded:

* shell / psql history for real users (root, mchen the DBA, phil, deploy),
* connection-credential breadcrumbs (.pgpass, config.yaml) — all REDACTED, so
  nothing is actually usable,
* DB data + backup artifacts (/var/lib/postgresql, /var/backups/db),
* real-format logs (auth.log, postgresql, etc.) that ``cat`` returns directly
  — these are the **fallback** the honeypot serves when the LLM is offline; the
  LLM, driven by the matching SystemProfile/Principles, generates in the same
  direction when online, so the two layers agree.

This pairs with ``core.config.SystemProfile`` (hostname ``happydog``, services
``postgresql``/``redis-server``, ports 5432/6379) and the DB persona rule in
``Principles.extra_rules`` — keep all three in sync when editing.

Usage
-----
    python -m honeyshell.fs.build_sample_fs                 # writes data/fs.json
    python -m honeyshell.fs.build_sample_fs out/fs.json     # custom path
    python -m honeyshell.fs.build_sample_fs --hostname box  # /etc/hostname body

The default hostname written into ``/etc/hostname`` is "happydog"; the *running*
server's prompt hostname is a separate concern set via ``ServerConfig`` — ``cat
/etc/hostname`` simply reflects this file's contents. Tests build with an
explicit ``hostname=`` so they don't depend on this default.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from honeyshell.fs.filesystem import DIR, FILE, LINK, FSNode, VirtualFS
from honeyshell.fs.loader import save_json

_DEFAULT_OUT = Path(__file__).resolve().parents[1] / "data" / "fs.json"
_MT = 1718150400.0  # fixed mtime for reproducible output (per-node spread: §3)


def _dir(name: str, *, perm: int = 0o755, uid: int = 0, gid: int = 0,
         mtime: float = _MT) -> FSNode:
    return FSNode(name, DIR, uid=uid, gid=gid, perm=perm, mtime=mtime)


def _file(
    name: str,
    contents: str | bytes = b"",
    *,
    perm: int = 0o644,
    uid: int = 0,
    gid: int = 0,
    size: int | None = None,
    mtime: float = _MT,
) -> FSNode:
    """A file node. If ``size`` is given it is stored independently of
    ``contents`` (a metadata-only file: realistic size, empty read)."""
    data = contents.encode() if isinstance(contents, str) else contents
    node = FSNode(name, FILE, uid=uid, gid=gid, perm=perm, mtime=mtime)
    node.contents = data if data else None
    node.size = size if size is not None else (len(data) if data else 0)
    return node


def _link(name: str, target: str, *, mtime: float = _MT) -> FSNode:
    return FSNode(name, LINK, perm=0o777, mtime=mtime, target=target)


def _add(parent: FSNode, *children: FSNode) -> FSNode:
    for c in children:
        parent.children[c.name] = c
    return parent


# =========================================================================== #
# /etc content
# =========================================================================== #

_PASSWD = (
    "root:x:0:0:root:/root:/bin/bash\n"
    "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
    "bin:x:2:2:bin:/bin:/usr/sbin/nologin\n"
    "sys:x:3:3:sys:/dev:/usr/sbin/nologin\n"
    "sync:x:4:65534:sync:/bin:/bin/sync\n"
    "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
    "sshd:x:105:65534::/run/sshd:/usr/sbin/nologin\n"
    "postgres:x:1003:1003:PostgreSQL administrator,,,:/var/lib/postgresql:/bin/bash\n"
    "redis:x:1004:1004::/var/lib/redis:/usr/sbin/nologin\n"
    "phil:x:1000:1000:Phil Turner,,,:/home/phil:/bin/bash\n"
    "mchen:x:1002:1002:Mei Chen (DBA),,,:/home/mchen:/bin/bash\n"
    "deploy:x:1005:1005:CI deploy,,,:/home/deploy:/bin/bash\n"
    "svc:x:1001:1001::/home/svc:/bin/bash\n"
)

# shadow: all hashes REDACTED/example — unusable for cracking (ethics/legal),
# but present so ``cat /etc/shadow`` looks real to recon. 0640 root:shadow.
_SHADOW = (
    "root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000"
    "000000000000000000000000000000:19700:0:99999:7:::\n"
    "daemon:*:19000:0:99999:7:::\n"
    "bin:*:19000:0:99999:7:::\n"
    "sys:*:19000:0:99999:7:::\n"
    "sshd:!:19000:0:99999:7:::\n"
    "www-data:*:19000:0:99999:7:::\n"
    "postgres:!:19000:0:99999:7:::\n"
    "redis:!:19000:0:99999:7:::\n"
    "phil:$6$defQWE$EXAMPLE111111111111111111111111111111111111111111111111"
    "11111111111111111111111111111:19420:0:99999:7:::\n"
    "mchen:$6$ghiRTY$EXAMPLE22222222222222222222222222222222222222222222222"
    "2222222222222222222222222222:19450:0:99999:7:::\n"
    "deploy:$6$jklUIO$EXAMPLE3333333333333333333333333333333333333333333333"
    "33333333333333333333333333:19460:0:99999:7:::\n"
    "svc:!:19420:0:99999:7:::\n"
)

_GROUP = (
    "root:x:0:\n"
    "daemon:x:1:\n"
    "bin:x:2:\n"
    "sys:x:3:\n"
    "adm:x:4:phil,mchen\n"
    "tty:x:5:\n"
    "sudo:x:27:phil,mchen\n"
    "www-data:x:33:\n"
    "ssh:x:112:\n"
    "postgres:x:1003:\n"
    "redis:x:1004:\n"
    "phil:x:1000:\n"
    "mchen:x:1002:\n"
    "deploy:x:1005:\n"
    "svc:x:1001:\n"
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

_HOSTS = (
    "127.0.0.1\tlocalhost\n"
    "127.0.1.1\thappydog\n"
    "\n"
    "::1\tlocalhost ip6-localhost ip6-loopback\n"
    "ff02::1\tip6-allnodes\n"
    "ff02::2\tip6-allrouters\n"
)

_RESOLV = (
    "# This file is managed by man:systemd-resolved(8). Do not edit.\n"
    "nameserver 8.8.8.8\n"
    "nameserver 1.1.1.1\n"
    "search localdomain\n"
)

_FSTAB = (
    "# /etc/fstab: static file system information.\n"
    "UUID=e1a2b3c4-1111-2222-3333-abcdef000000 /     ext4 errors=remount-ro 0 1\n"
    "UUID=f9e8d7c6-4444-5555-6666-000000fedcba /boot ext4 defaults          0 2\n"
    "/swapfile none swap sw 0 0\n"
)

_MACHINE_ID = "3f2504e04f8941d39a0c0305e82c3301\n"

_CRONTAB = (
    "# /etc/crontab: system-wide crontab\n"
    "SHELL=/bin/sh\n"
    "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n"
    "\n"
    "17 *  * * *  root  cd / && run-parts --report /etc/cron.hourly\n"
    "25 6  * * *  root  test -x /usr/sbin/anacron || run-parts /etc/cron.daily\n"
    "30 2  * * *  postgres  /usr/local/bin/pg_backup.sh >> /var/log/pg_backup.log 2>&1\n"
)

_SSHD_CONFIG = (
    "Port 22\n"
    "PermitRootLogin yes\n"
    "PasswordAuthentication yes\n"
    "PubkeyAuthentication yes\n"
    "ChallengeResponseAuthentication no\n"
    "UsePAM yes\n"
    "X11Forwarding yes\n"
    "PrintMotd no\n"
    "AcceptEnv LANG LC_*\n"
    "Subsystem sftp /usr/lib/openssh/sftp-server\n"
)

# PostgreSQL main config — the kind of file a DBA edits and an attacker reads.
_PG_CONFIG = (
    "# -----------------------------\n"
    "# PostgreSQL configuration file\n"
    "# -----------------------------\n"
    "data_directory = '/var/lib/postgresql/13/main'\n"
    "hba_file = '/etc/postgresql/13/main/pg_hba.conf'\n"
    "listen_addresses = '*'\n"
    "port = 5432\n"
    "max_connections = 200\n"
    "shared_buffers = 2GB\n"
    "effective_cache_size = 6GB\n"
    "work_mem = 16MB\n"
    "maintenance_work_mem = 512MB\n"
    "wal_level = replica\n"
    "log_directory = '/var/log/postgresql'\n"
    "log_min_duration_statement = 1000\n"
    "log_line_prefix = '%m [%p] %q%u@%d '\n"
)

_PG_HBA = (
    "# TYPE  DATABASE  USER  ADDRESS         METHOD\n"
    "local   all       postgres              peer\n"
    "local   all       all                   md5\n"
    "host    all       all   127.0.0.1/32    md5\n"
    "host    all       all   10.0.0.0/8      md5\n"
    "host    appdb     appuser 0.0.0.0/0     md5\n"
)

# =========================================================================== #
# User home content (the "lived-in" evidence recon reads)
# =========================================================================== #

_ROOT_HIST = (
    "ls -la\ndf -h\nfree -m\napt update\n"
    "systemctl status postgresql\nsystemctl status redis-server\n"
    "su - postgres\ntail -f /var/log/postgresql/postgresql-13-main.log\n"
    "netstat -tlnp\nss -tlnp\n"
    "vim /etc/postgresql/13/main/postgresql.conf\n"
    "systemctl restart postgresql\ncat /var/log/auth.log | grep Failed\n"
    "crontab -l\ndu -sh /var/lib/postgresql/*\nps aux | grep postgres\nexit\n"
)

_MCHEN_HIST = (
    "cd ~\npsql -U postgres -h localhost\n"
    "pg_dump -U postgres appdb > backup.sql\nls -lh backup.sql\n"
    "gzip backup.sql\nscp backup.sql.gz backup-srv:/backups/\n"
    "psql -U postgres -d appdb -c 'SELECT count(*) FROM users;'\n"
    "redis-cli -a REDACTED info\nredis-cli KEYS '*'\n"
    "vim ~/queries/slow.sql\npg_dumpall -U postgres > full.sql\n"
    "cat ~/.pgpass\nlogout\n"
)

# psql history: high-value intel (db/table names, sensitive columns).
_MCHEN_PSQL = (
    "\\l\n\\c appdb\n\\dt\nSELECT count(*) FROM users;\n"
    "SELECT id, email, created_at FROM users ORDER BY id DESC LIMIT 20;\n"
    "SELECT * FROM orders WHERE status = 'paid' LIMIT 50;\n"
    "\\d users\n\\d payments\n"
    "SELECT card_last4, amount FROM payments LIMIT 10;\n"
    "UPDATE users SET is_admin = true WHERE email = 'mchen@corp.local';\n\\q\n"
)

_MCHEN_PGPASS = (
    "localhost:5432:appdb:postgres:S3cr3tPgPass_REDACTED\n"
    "localhost:6379:*:redis:R3disPass_REDACTED\n"
)

_ROOT_PGPASS = "localhost:5432:*:postgres:PgAdminPass_REDACTED\n"

_PHIL_HIST = (
    "cd webapp\ngit pull\npython3 -m venv venv\nsource venv/bin/activate\n"
    "pip install -r requirements.txt\npython3 app.py\nvim config.yaml\n"
    "git commit -am 'fix db config'\ngit push\nlogout\n"
)

_PHIL_CONFIG = (
    "db:\n  host: localhost\n  port: 5432\n  name: appdb\n"
    "  user: appuser\n  password: appDbPass_REDACTED\n"
    "redis:\n  host: localhost\n  port: 6379\n"
)

_DEPLOY_HIST = "cd /opt/app\ngit pull\n./deploy.sh\nsystemctl restart appserver\nlogout\n"


def _build_home(hostname: str) -> FSNode:
    home = _dir("home")

    # svc: kept minimal (only a hidden .bashrc) to preserve existing tests.
    svc = _dir("svc", uid=1001, gid=1001)
    _add(svc, _file(".bashrc", "# svc bashrc\n", uid=1001, gid=1001))

    # phil: app developer.
    phil = _dir("phil", uid=1000, gid=1000)
    _add(
        phil,
        _file(".bashrc", "# phil bashrc\n", uid=1000, gid=1000),
        _file(".profile", "# phil profile\n", uid=1000, gid=1000),
        _file(".bash_history", _PHIL_HIST, perm=0o600, uid=1000, gid=1000),
    )
    webapp = _dir("webapp", uid=1000, gid=1000)
    _add(
        webapp,
        _file("app.py", "from flask import Flask\napp = Flask(__name__)\n",
              uid=1000, gid=1000),
        _file("config.yaml", _PHIL_CONFIG, perm=0o600, uid=1000, gid=1000),
        _file("requirements.txt",
              "flask==2.0.1\npsycopg2==2.9.1\nredis==3.5.3\n",
              uid=1000, gid=1000),
    )
    phil.children["webapp"] = webapp

    # mchen: DBA — the densest intel.
    mchen = _dir("mchen", uid=1002, gid=1002)
    _add(
        mchen,
        _file(".bashrc", "# mchen bashrc\n", uid=1002, gid=1002),
        _file(".profile", "# mchen profile\n", uid=1002, gid=1002),
        _file(".bash_history", _MCHEN_HIST, perm=0o600, uid=1002, gid=1002),
        _file(".psql_history", _MCHEN_PSQL, perm=0o600, uid=1002, gid=1002),
        _file(".pgpass", _MCHEN_PGPASS, perm=0o600, uid=1002, gid=1002),
    )
    mssh = _dir(".ssh", perm=0o700, uid=1002, gid=1002)
    _add(
        mssh,
        _file("id_rsa", perm=0o600, uid=1002, gid=1002, size=2602),
        _file("id_rsa.pub", "ssh-rsa AAAAB3NzaC1yc2EAAAA...mchen@happydog\n",
              uid=1002, gid=1002),
        _file("known_hosts", "backup-srv ssh-rsa AAAAB3NzaC1yc2E...\n",
              uid=1002, gid=1002),
        _file("authorized_keys",
              "ssh-rsa AAAAB3NzaC1yc2E...mchen@laptop\n",
              perm=0o600, uid=1002, gid=1002),
    )
    mchen.children[".ssh"] = mssh
    queries = _dir("queries", uid=1002, gid=1002)
    _add(queries, _file(
        "slow.sql",
        "-- queries to optimize\n"
        "SELECT * FROM orders o JOIN users u ON o.user_id = u.id;\n",
        uid=1002, gid=1002))
    mchen.children["queries"] = queries

    # deploy: CI account.
    deploy = _dir("deploy", uid=1005, gid=1005)
    _add(
        deploy,
        _file(".bashrc", "# deploy bashrc\n", uid=1005, gid=1005),
        _file(".bash_history", _DEPLOY_HIST, perm=0o600, uid=1005, gid=1005),
        _file("deploy.sh",
              "#!/bin/bash\ncd /opt/app && git pull && "
              "systemctl restart appserver\n",
              perm=0o755, uid=1005, gid=1005),
    )

    _add(home, phil, mchen, deploy, svc)
    return home


def _build_var() -> FSNode:
    var = _dir("var")

    # --- /var/lib: DB data footprint ---
    lib = _dir("lib")
    pg = _dir("postgresql", uid=1003, gid=1003)
    pg13 = _dir("13", uid=1003, gid=1003)
    main = _dir("main", perm=0o700, uid=1003, gid=1003)
    _add(
        main,
        _file("PG_VERSION", "13\n", uid=1003, gid=1003),
        _file("postmaster.pid",
              "2481\n/var/lib/postgresql/13/main\n1718000000\n5432\n",
              uid=1003, gid=1003, size=68),
    )
    base = _dir("base", uid=1003, gid=1003)
    _add(base, _dir("16384", uid=1003, gid=1003),
         _dir("16385", uid=1003, gid=1003))  # appdb / other oids
    main.children["base"] = base
    pg13.children["main"] = main
    pg.children["13"] = pg13
    lib.children["postgresql"] = pg

    redis = _dir("redis", uid=1004, gid=1004)
    _add(redis, _file("dump.rdb", uid=1004, gid=1004, perm=0o660, size=104857))
    lib.children["redis"] = redis
    var.children["lib"] = lib

    # --- /var/backups/db: the ransom/exfil bait ---
    backups = _dir("backups")
    db = _dir("db")
    _add(
        db,
        _file("appdb-2024-06-10.sql.gz", size=8451200),
        _file("appdb-2024-06-11.sql.gz", size=8502144),
        _file("full-2024-06-11.sql.gz", size=15204352),
    )
    backups.children["db"] = db
    var.children["backups"] = backups

    # --- /var/log: real-format samples = LLM-offline fallback ---
    log = _dir("log")
    _add(
        log,
        _file("auth.log", _AUTH_LOG, perm=0o640, gid=4),
        _file("syslog", _SYSLOG, perm=0o640, gid=4),
        _file("dpkg.log", _DPKG_LOG),
        _file("wtmp", perm=0o664, gid=43, size=9216),      # binary, metadata
        _file("lastlog", perm=0o664, gid=43, size=292292),
    )
    pglog = _dir("postgresql")
    _add(pglog, _file("postgresql-13-main.log", _PG_LOG, perm=0o640, gid=1003))
    log.children["postgresql"] = pglog
    var.children["log"] = log

    # --- /var/www: minimal, present because www-data exists in passwd ---
    www = _dir("www")
    _add(www, _dir("html"))
    var.children["www"] = www
    return var


# --- log sample bodies (kept short but real-format) ---

_AUTH_LOG = (
    "Jun 11 06:12:03 happydog sshd[2210]: Accepted password for mchen "
    "from 10.0.0.14 port 51344 ssh2\n"
    "Jun 11 06:12:03 happydog sshd[2210]: pam_unix(sshd:session): session "
    "opened for user mchen(uid=1002) by (uid=0)\n"
    "Jun 11 07:44:19 happydog sudo:    mchen : TTY=pts/0 ; PWD=/home/mchen ; "
    "USER=root ; COMMAND=/usr/bin/systemctl restart postgresql\n"
    "Jun 11 08:02:55 happydog sshd[3120]: Failed password for root from "
    "45.155.205.9 port 40122 ssh2\n"
    "Jun 11 08:02:57 happydog sshd[3120]: Failed password for root from "
    "45.155.205.9 port 40122 ssh2\n"
    "Jun 11 08:03:01 happydog sshd[3120]: Disconnected from authenticating "
    "user root 45.155.205.9 port 40122 [preauth]\n"
    "Jun 11 09:15:40 happydog sshd[3402]: Accepted publickey for deploy "
    "from 10.0.0.20 port 33512 ssh2\n"
)

_SYSLOG = (
    "Jun 11 06:00:01 happydog CRON[1987]: (root) CMD (cd / && run-parts "
    "--report /etc/cron.hourly)\n"
    "Jun 11 06:25:12 happydog systemd[1]: Starting Daily apt upgrade...\n"
    "Jun 11 08:30:02 happydog postgres[2490]: [12-1] LOG:  checkpoint "
    "starting: time\n"
    "Jun 11 08:30:14 happydog postgres[2490]: [13-1] LOG:  checkpoint "
    "complete: wrote 812 buffers\n"
    "Jun 11 09:00:00 happydog systemd[1]: Started Session 42 of user mchen.\n"
)

_DPKG_LOG = (
    "2024-06-10 06:25:14 status installed postgresql-13:amd64 13.14-0+deb11u1\n"
    "2024-06-10 06:25:15 status installed redis-server:amd64 5:6.0.16-1+deb11u2\n"
    "2024-06-11 06:25:30 status installed libssl1.1:amd64 1.1.1n-0+deb11u5\n"
)

_PG_LOG = (
    "2024-06-11 08:30:02.114 UTC [2490] LOG:  database system is ready to "
    "accept connections\n"
    "2024-06-11 08:41:19.882 UTC [3055] postgres@appdb LOG:  duration: "
    "1284.551 ms  statement: SELECT * FROM orders WHERE status = 'paid';\n"
    "2024-06-11 09:02:44.301 UTC [3120] appuser@appdb LOG:  connection "
    "authorized: user=appuser database=appdb\n"
    "2024-06-11 09:14:07.552 UTC [3120] appuser@appdb LOG:  duration: "
    "2044.019 ms  statement: SELECT card_last4, amount FROM payments;\n"
)

_CPUINFO = (
    "processor\t: 0\nvendor_id\t: GenuineIntel\n"
    "model name\t: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz\n"
    "cpu MHz\t\t: 2400.000\ncache size\t: 35840 KB\n"
    "processor\t: 1\nvendor_id\t: GenuineIntel\n"
    "model name\t: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz\n"
    "cpu MHz\t\t: 2400.000\ncache size\t: 35840 KB\n"
)

_MEMINFO = (
    "MemTotal:        8167848 kB\nMemFree:         5432100 kB\n"
    "MemAvailable:    6931200 kB\nBuffers:          123456 kB\n"
    "Cached:          1345678 kB\nSwapTotal:       2097148 kB\n"
    "SwapFree:        2097148 kB\n"
)

# The mount table `mount` (no args) and `cat /proc/mounts` expose. Kept in one
# place so both agree, and aligned with the df filesystem set (/, tmpfs x3).
_MOUNTS = (
    "sysfs /sys sysfs rw,nosuid,nodev,noexec,relatime 0 0\n"
    "proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0\n"
    "udev /dev devtmpfs rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,"
    "mode=755 0 0\n"
    "devpts /dev/pts devpts rw,nosuid,noexec,relatime,gid=5,mode=620,"
    "ptmxmode=000 0 0\n"
    "tmpfs /run tmpfs rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755 "
    "0 0\n"
    "/dev/sda1 / ext4 rw,relatime,errors=remount-ro 0 0\n"
    "tmpfs /dev/shm tmpfs rw,nosuid,nodev 0 0\n"
    "tmpfs /run/lock tmpfs rw,nosuid,nodev,noexec,relatime,size=5120k 0 0\n"
)


# =========================================================================== #
# Tool presence (§2) — /usr/bin, /usr/sbin, /bin populated with metadata-only
# binaries so `ls /usr/bin`, `ls -la /usr/bin | wc -l` and `which <tool>` all
# agree with the LLM's "assume any tool is installed" behaviour. Files are
# content-less (empty read) but carry a realistic size, matching the /bin
# convention already used for ls/bash/cat.
# =========================================================================== #

# name -> realistic on-disk size (bytes). Curated for a Debian 11 DB host;
# includes the DB toolchain (psql/pg_dump/redis-cli) an attacker expects here.
_USR_BIN_TOOLS: dict[str, int] = {
    # interpreters / build
    "python3": 5479600, "python3.9": 5479600, "perl": 2093056,
    "gcc": 1092352, "make": 260072, "awk": 662320, "gawk": 662320,
    # editors
    "vim": 3040000, "vi": 3040000, "nano": 250000, "less": 191472,
    # net / transfer
    "curl": 254832, "wget": 484416, "ssh": 805208, "scp": 145016,
    "sftp": 205016, "nc": 47320, "ncat": 47320, "socat": 375632,
    "rsync": 700000, "telnet": 68000, "ftp": 130000,
    # archive / compress
    "tar": 458008, "gzip": 98048, "gunzip": 2251, "bzip2": 39536,
    "xz": 92264, "zip": 210000, "unzip": 200000,
    # inspect / debug
    "strace": 1200000, "ltrace": 180000, "gdb": 9800000, "lsof": 179000,
    "tcpdump": 1155000, "htop": 240000, "file": 30000, "strings": 40000,
    # crypto / hash
    "openssl": 962624, "md5sum": 47000, "sha256sum": 47000, "base64": 39000,
    # scm / db clients
    "git": 3251320, "psql": 700000, "pg_dump": 620000, "pg_dumpall": 90000,
    "redis-cli": 5300000, "sqlite3": 1400000,
    # package management (Debian) — present so `which apt-get`/`dpkg` resolve,
    # keeping tool presence consistent with the LLM's apt-get output. (yum/dnf
    # are deliberately absent: this is a Debian host, and the yum builtin
    # reports command-not-found.)
    "apt": 174000, "apt-get": 174000, "apt-cache": 174000,
    "dpkg": 350000, "dpkg-query": 90000,
    # misc userland
    "sudo": 232416, "screen": 450000, "tmux": 680000, "wall": 35000,
    "crontab": 43000, "find": 320000, "xargs": 60000, "dig": 130000,
    "nslookup": 140000, "host": 130000, "python": 5479600,
}

# /usr/sbin: service/daemon-side tools.
_USR_SBIN_TOOLS: dict[str, int] = {
    "sshd": 852024, "cron": 60000, "rsyslogd": 700000,
    "postgres": 8200000, "redis-server": 5300000, "service": 8000,
    "useradd": 150000, "usermod": 150000, "groupadd": 40000,
    "visudo": 240000, "iptables": 96000, "ss": 130000,
}


def _build_bindir(name: str, tools: dict[str, int]) -> FSNode:
    """A bin directory of metadata-only executables (0755, empty read)."""
    d = _dir(name)
    for tool, size in tools.items():
        d.children[tool] = _file(tool, perm=0o755, size=size)
    return d


# =========================================================================== #
# Timestamp spread (§3) — defeat the "every node shares one mtime" fingerprint.
#
# Real hosts show a *layered* time profile in ``ls -l``: base-system files date
# to install time, packages to their install date, and user/activity files
# (histories, logs, backups) to recent days. We reproduce that deterministically
# (seeded by path, not wall-clock) so fs.json stays reproducible and testable,
# while no two unrelated files share an identical timestamp.
#
# Anchors (UTC):
#   install  ~ 2024-02-10   base system / bin / etc skeleton
#   packages ~ 2024-06-10   postgresql/redis install, dpkg activity
#   recent   ~ 2024-06-11..14  user histories, logs, backups, runtime state
# =========================================================================== #

_T_INSTALL = 1707523200.0   # 2024-02-10
_T_PACKAGE = 1717977600.0   # 2024-06-10
_T_RECENT = 1718064000.0    # 2024-06-11

# Prefix -> (base_anchor, jitter_span_seconds). First match wins (longest
# prefixes first). Jitter is derived from a hash of the full path, so it's
# stable across rebuilds but differs per file.
_MTIME_RULES: tuple[tuple[str, float, float], ...] = (
    ("/var/log", _T_RECENT, 3 * 86400),          # logs: last few days
    ("/var/backups", _T_RECENT, 2 * 86400),       # nightly backups
    ("/var/lib/postgresql", _T_RECENT, 4 * 86400),  # live DB files churn
    ("/var/lib/redis", _T_RECENT, 4 * 86400),
    ("/root/.bash_history", _T_RECENT, 2 * 86400),
    ("/home", _T_RECENT, 4 * 86400),              # user activity
    ("/root", _T_PACKAGE, 5 * 86400),             # root dotfiles: setup-ish
    ("/etc/postgresql", _T_PACKAGE, 2 * 86400),   # pg config: install time
    ("/etc/ssh", _T_INSTALL, 2 * 86400),
    ("/usr/bin", _T_PACKAGE, 10 * 86400),         # packages installed over time
    ("/usr/sbin", _T_PACKAGE, 10 * 86400),
    ("/etc", _T_INSTALL, 6 * 86400),              # base config skeleton
    ("/bin", _T_INSTALL, 3 * 86400),
    ("/proc", _T_RECENT, 1 * 86400),              # pseudo-fs: "now"
)
_MTIME_DEFAULT = (_T_INSTALL, 5 * 86400)


def _mtime_for(path: str) -> float:
    """Deterministic mtime for a path: pick an anchor by prefix, add stable
    per-path jitter (hash-derived) so siblings differ but rebuilds match."""
    import hashlib

    anchor, span = _MTIME_DEFAULT
    for prefix, a, s in _MTIME_RULES:
        if path == prefix or path.startswith(prefix + "/") or path == prefix:
            anchor, span = a, s
            break
    h = int(hashlib.sha256(path.encode()).hexdigest()[:8], 16)
    return anchor + (h % int(span))


def _spread_mtimes(node: FSNode, path: str = "") -> None:
    """Walk the tree and assign a semantic, per-path mtime to every node."""
    if path:  # skip the synthetic root ("/")
        node.mtime = _mtime_for(path)
    for name, child in node.children.items():
        child_path = f"{path}/{name}" if path != "/" else f"/{name}"
        if not path:
            child_path = f"/{name}"
        _spread_mtimes(child, child_path)


def build(hostname: str = "happydog") -> VirtualFS:
    """Construct the sample filesystem tree (DB-server persona)."""
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
    # /sbin -> /bin (usr-merge style), so /sbin/ls == /bin/ls.
    sbin = _link("sbin", "/bin")

    # --- /etc : full-ish, DB-flavoured ---
    etcd = _dir("etc")
    _add(
        etcd,
        _file("hostname", f"{hostname}\n"),
        _file("os-release", _OS_RELEASE),
        _file("passwd", _PASSWD, perm=0o644),
        _file("shadow", _SHADOW, perm=0o640, gid=42),
        _file("group", _GROUP),
        _file("hosts", _HOSTS),
        _file("resolv.conf", _RESOLV),
        _file("fstab", _FSTAB),
        _file("machine-id", _MACHINE_ID),
        _file("crontab", _CRONTAB),
    )
    ssh_etc = _dir("ssh")
    _add(
        ssh_etc,
        _file("sshd_config", _SSHD_CONFIG),
        _file("ssh_host_rsa_key", perm=0o600, size=2602),
        _file("ssh_host_rsa_key.pub",
              "ssh-rsa AAAAB3NzaC1yc2E...root@happydog\n"),
    )
    etcd.children["ssh"] = ssh_etc
    pg_etc = _dir("postgresql")
    pg_etc_13 = _dir("13")
    pg_etc_main = _dir("main")
    _add(
        pg_etc_main,
        _file("postgresql.conf", _PG_CONFIG),
        _file("pg_hba.conf", _PG_HBA),
    )
    pg_etc_13.children["main"] = pg_etc_main
    pg_etc.children["13"] = pg_etc_13
    etcd.children["postgresql"] = pg_etc

    # --- /root : 0700, with dotfiles + DB-admin breadcrumbs ---
    rootd = _dir("root", perm=0o700)
    _add(
        rootd,
        _file(".bashrc", "# ~/.bashrc\nexport PS1='\\u@\\h:\\w\\$ '\n"),
        _file(".profile", "# ~/.profile\n"),
        _file(".bash_history", _ROOT_HIST, perm=0o600),
        _file(".pgpass", _ROOT_PGPASS, perm=0o600),
    )

    # --- /proc : the readouts attackers commonly inspect ---
    procd = _dir("proc")
    _add(
        procd,
        _file("cpuinfo", _CPUINFO),
        _file("meminfo", _MEMINFO),
        _file("version", "Linux version 5.10.0-19-amd64 (debian-kernel)\n"),
        # /proc/uptime is dynamic on a real box (up-secs idle-secs). We ship a
        # static value consistent in magnitude with the emulated ~7-day uptime
        # (the `uptime`/`top` commands compute the live figure from boot_time);
        # a `cat /proc/uptime` returning "No such file or directory" is a much
        # bigger tell than a slightly stale count, so a plausible constant wins.
        _file("uptime", "615254.71 4903211.02\n"),
        # Matches the load average `uptime`/`top` print (0.08 0.03 0.01).
        _file("loadavg", "0.08 0.03 0.01 1/214 8090\n"),
        # /proc/mounts — the authoritative mount table `mount` (no args) reads.
        _file("mounts", _MOUNTS),
    )

    homed = _build_home(hostname)
    vard = _build_var()

    # --- /usr : populated bin/sbin so tool-presence probes succeed (§2) ---
    usrd = _dir("usr")
    _add(
        usrd,
        _build_bindir("bin", _USR_BIN_TOOLS),
        _build_bindir("sbin", _USR_SBIN_TOOLS),
        _dir("lib"),
        _dir("share"),
        _add(_dir("local"), _dir("bin"), _dir("sbin")),
    )

    # --- other standard FHS top-level directories ---
    root_children = [
        bind, _dir("boot"), _dir("dev"), etcd, homed, _dir("lib"),
        _dir("lib64"), _dir("media"), _dir("mnt"),
        _add(_dir("opt"), _dir("app")),  # /opt/app referenced by deploy.sh
        procd, rootd, _dir("run"), sbin, _dir("srv"), _dir("sys"),
        _dir("tmp", perm=0o1777), usrd, vard,
    ]
    for c in root_children:
        root.children[c.name] = c

    # §3: replace the uniform _MT with a semantic, deterministic mtime spread.
    _spread_mtimes(root)

    return VirtualFS(root)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the sample fs.json tree.")
    ap.add_argument("out", nargs="?", default=str(_DEFAULT_OUT),
                    help="output path (default: honeyshell/data/fs.json)")
    ap.add_argument("--hostname", default="happydog",
                    help="contents of /etc/hostname (default: happydog)")
    args = ap.parse_args(argv)

    vfs = build(hostname=args.hostname)
    save_json(vfs, args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
