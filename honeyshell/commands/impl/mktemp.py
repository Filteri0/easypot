"""mktemp — create a temporary file or directory and print its path.

Attackers use ``cd $(mktemp -d)`` to get a scratch dir. We create a real node in
the VFS under /tmp with a random suffix and print its path, so the following
``cd``/writes land somewhere that actually exists (state consistency).

Supports ``-d`` (directory), ``-t``/templates are accepted loosely. The template
``XXXXXX`` (or a default) is filled with random chars.
"""

from __future__ import annotations

import random
import string

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError

__all__ = ["Mktemp"]


def _rand(n: int = 10) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


@register("mktemp", "/bin/mktemp", "/usr/bin/mktemp")
class Mktemp(Command):
    async def run(self) -> int:
        make_dir = False
        template = None
        for a in self.args:
            if a == "-d" or a == "--directory":
                make_dir = True
            elif a in ("-t", "-q", "-u", "--tmpdir"):
                continue
            elif not a.startswith("-"):
                template = a

        # Derive a path: honour a trailing XXXXXX in a template, else /tmp/tmp.XXXX
        if template and "XXX" in template:
            base = template.replace("X" * template.count("X"),
                                    _rand(max(6, template.count("X"))))
            path = base if base.startswith("/") else f"/tmp/{base}"
        else:
            prefix = "tmp." if not make_dir else "tmp."
            path = f"/tmp/{prefix}{_rand()}"

        try:
            if make_dir:
                self.ctx.fs.makedirs(path, self.ctx.cwd)
            else:
                self.ctx.fs.write_file(path, b"", self.ctx.cwd,
                                       uid=self.ctx.uid, gid=self.ctx.uid)
        except FSError as e:
            self.errline(f"mktemp: {e.message}")
            return 1
        self.line(path)
        return 0
