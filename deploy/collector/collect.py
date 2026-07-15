"""easypot log collector.

Tails every ``*.jsonl`` file a honeypot writes under ``AUDIT_DIR`` (excluding
its own merged output) and appends each new line — tagged with its source
honeypot — to ``MERGED_OUT`` and to stdout. Pure stdlib: no pandas/DB yet. The
analyzer (structured aggregation) is a separate, later component that reads the
merged file; keeping collection dumb-and-robust means a analyzer crash never
loses raw events.

Design notes
------------
* **Poll-based tail**, not inotify: simplest thing that survives file rotation,
  truncation, and files appearing after startup (a honeypot may start after the
  collector). Every ``POLL_INTERVAL`` we re-scan the dir and read any growth.
* **Per-file offset** tracked in memory; if a file shrinks (rotated/truncated)
  we reset its offset to 0 and re-read.
* **Source tag** is the filename stem (``honeypot-a.jsonl`` -> ``honeypot-a``),
  injected as ``_source`` so downstream can group by honeypot without needing
  the honeypots to know their own name.
* **Never crashes on a bad line**: malformed JSON is passed through wrapped in a
  ``{"_raw": ...}`` envelope rather than dropped, so nothing is silently lost.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

AUDIT_DIR = Path(os.environ.get("AUDIT_DIR", "/data/audit"))
MERGED_OUT = Path(os.environ.get("MERGED_OUT", "/data/audit/_merged.jsonl"))
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "1.0"))

# Files the collector itself owns — never tail these (would loop).
_SELF = {MERGED_OUT.name}


def _source_files() -> list[Path]:
    if not AUDIT_DIR.is_dir():
        return []
    return sorted(
        p for p in AUDIT_DIR.glob("*.jsonl")
        if p.name not in _SELF and not p.name.startswith("_")
    )


def _emit(out_fh, source: str, line: str) -> None:
    line = line.rstrip("\n")
    if not line:
        return
    try:
        obj = json.loads(line)
        if isinstance(obj, dict):
            obj["_source"] = source
        else:  # a JSON scalar/array on its own line — wrap it
            obj = {"_source": source, "_value": obj}
    except json.JSONDecodeError:
        obj = {"_source": source, "_raw": line}
    rendered = json.dumps(obj, ensure_ascii=False)
    out_fh.write(rendered + "\n")
    out_fh.flush()
    # Also to stdout so `docker compose logs collector` shows the live stream.
    print(rendered, flush=True)


def _open_merged():
    """Open the merged-output file for append, retrying on failure.

    A transient permission/IO problem (e.g. a shared volume not yet writable)
    must NOT crash the process — that turns into a Docker restart-loop that
    hides the real cause. Instead we log the error clearly and keep retrying,
    so the container stays up and starts working the moment the path becomes
    writable. Ensures the parent dir exists first (best effort)."""
    while True:
        try:
            MERGED_OUT.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        try:
            return open(MERGED_OUT, "a", encoding="utf-8")
        except OSError as exc:
            print(f"[collector] cannot open {MERGED_OUT}: {exc} "
                  f"(retrying in {POLL_INTERVAL}s)", file=sys.stderr, flush=True)
            time.sleep(max(POLL_INTERVAL, 1.0))


def main() -> int:
    try:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    offsets: dict[str, int] = {}
    print(f"[collector] watching {AUDIT_DIR} -> {MERGED_OUT}", file=sys.stderr,
          flush=True)

    out_fh = _open_merged()
    try:
        while True:
            for path in _source_files():
                source = path.stem
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                last = offsets.get(source, 0)
                if size < last:          # rotated/truncated -> re-read
                    last = 0
                if size == last:
                    continue
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") \
                            as fh:
                        fh.seek(last)
                        for line in fh:
                            _emit(out_fh, source, line)
                        offsets[source] = fh.tell()
                except OSError:
                    continue
            time.sleep(POLL_INTERVAL)
    finally:
        try:
            out_fh.close()
        except OSError:
            pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
