"""dd — convert and copy a file.

Honeypot subset: reads ``if=`` from the VFS (or /dev/zero-style pseudo sources)
and writes ``of=`` back into the VFS, so a subsequent ``ls``/``cat`` sees the
result (state consistency). Reports the conventional records-in/out summary on
stderr. Attackers use dd to stage payloads and to probe /dev/*.

Deferred: real bs/count arithmetic on huge sizes, ``conv=`` options.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError

__all__ = ["Dd"]


def _parse_size(spec: str) -> int:
    units = {"c": 1, "b": 512, "k": 1024, "K": 1024, "M": 1024 ** 2,
             "G": 1024 ** 3}
    if spec and spec[-1] in units:
        try:
            return int(spec[:-1]) * units[spec[-1]]
        except ValueError:
            return 0
    try:
        return int(spec)
    except ValueError:
        return 0


@register("dd", "/bin/dd")
class Dd(Command):
    async def run(self) -> int:
        params = {}
        for a in self.args:
            if "=" in a:
                k, _, v = a.partition("=")
                params[k] = v

        infile = params.get("if")
        outfile = params.get("of")
        bs = _parse_size(params.get("bs", "512")) or 512
        count = int(params.get("count", "0") or 0)

        # Source bytes: from a VFS file, or synthesised for pseudo-devices.
        data = b""
        if infile in ("/dev/zero", "/dev/null"):
            data = b"\x00" * (bs * count) if count else b""
        elif infile in ("/dev/urandom", "/dev/random"):
            data = b"\x00" * (bs * count) if count else b""
        elif infile:
            try:
                data = self.ctx.fs.readbytes(infile, self.ctx.cwd)
            except FSError:
                self.errline(f"dd: failed to open '{infile}': "
                             f"No such file or directory")
                return 1

        if count and bs and infile not in ("/dev/zero", "/dev/null",
                                           "/dev/urandom", "/dev/random"):
            data = data[:bs * count]

        if outfile and outfile not in ("/dev/null",):
            try:
                self.ctx.fs.write_file(outfile, data, self.ctx.cwd,
                                       uid=self.ctx.uid, gid=self.ctx.uid)
            except FSError as e:
                self.errline(f"dd: failed to open '{outfile}': {e.message}")
                return 1
        elif outfile is None:
            # No of=: dd writes to stdout.
            self.write(data.decode("utf-8", "replace"))

        records = (len(data) + bs - 1) // bs if bs else 0
        self.errline(f"{records}+0 records in")
        self.errline(f"{records}+0 records out")
        self.errline(f"{len(data)} bytes ({len(data)} B) copied, "
                     f"0.001 s, {len(data)} MB/s")
        return 0
