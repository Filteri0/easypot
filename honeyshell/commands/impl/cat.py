"""cat — concatenate files to stdout, or copy stdin when given no operands.

Split out of the former ``basic.py`` starter set. The no-operand stdin path is
what lets ``cat`` sit in a pipeline.

Option handling mirrors GNU coreutils so recon probes don't expose the
honeypot: a bare ``-`` means stdin; ``--`` ends option parsing; an unknown
short flag reports ``invalid option -- 'X'`` and an unknown long flag reports
``unrecognized option '--foo'`` (both exit 2) — rather than the old behaviour
of treating ``-Z`` as a filename (``-Z: No such file or directory``), a clear
tell. A small, common subset is actually implemented: ``-n`` (number all
lines), ``-b`` (number non-blank lines), ``-E`` (mark line ends with ``$``).
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fileorstdin import check_read
from honeyshell.fs import FSError

__all__ = ["Cat"]

# Long options GNU cat accepts, mapped to the short flag we already handle.
_LONG = {
    "--number": "n",
    "--number-nonblank": "b",
    "--show-ends": "E",
}


@register("cat", "/bin/cat")
class Cat(Command):
    async def run(self) -> int:
        number = False       # -n
        number_nonblank = False  # -b
        show_ends = False    # -E
        operands: list[str] = []
        no_more = False

        for a in self.args:
            if no_more or a == "-" or not a.startswith("-"):
                operands.append(a)
            elif a == "--":
                no_more = True
            elif a.startswith("--"):
                short = _LONG.get(a)
                if short is None:
                    self.errline(f"cat: unrecognized option '{a}'")
                    self.errline("Try 'cat --help' for more information.")
                    return 2
                if short == "n":
                    number = True
                elif short == "b":
                    number_nonblank = True
                elif short == "E":
                    show_ends = True
            else:
                for ch in a[1:]:
                    if ch == "n":
                        number = True
                    elif ch == "b":
                        number_nonblank = True
                    elif ch == "E":
                        show_ends = True
                    else:
                        self.errline(f"cat: invalid option -- '{ch}'")
                        self.errline("Try 'cat --help' for more information.")
                        return 2

        # Collect the raw text (stdin for no operands or a bare '-').
        if not operands:
            text = await self.read_all()
            self.write(self._render(text, number, number_nonblank, show_ends))
            return 0

        rc = 0
        for path in operands:
            if path == "-":
                text = await self.read_all()
            else:
                denied = check_read(self.ctx, path)
                if denied is not None:
                    rc = self.fail(f"{path}: {denied}")
                    continue
                try:
                    text = self.ctx.fs.readtext(path, self.ctx.cwd)
                except FSError as e:
                    rc = self.fail(f"{path}: {e.message}")
                    continue
            self.write(self._render(text, number, number_nonblank, show_ends))
        return rc

    @staticmethod
    def _render(text: str, number: bool, number_nonblank: bool,
                show_ends: bool) -> str:
        """Apply -n/-b/-E. Fast path: no flags -> return text unchanged.

        Numbering follows GNU cat: ``-b`` numbers only non-blank lines and
        overrides ``-n``; the counter is 6-wide, right-justified, tab-separated.
        ``-E`` appends ``$`` before each newline.
        """
        if not (number or number_nonblank or show_ends):
            return text
        # Preserve a trailing-newline vs not; split on '\n' keeping structure.
        lines = text.split("\n")
        trailing = lines and lines[-1] == ""
        if trailing:
            lines = lines[:-1]
        out: list[str] = []
        counter = 0
        for ln in lines:
            body = ln + "$" if show_ends else ln
            if number_nonblank:
                if ln != "":
                    counter += 1
                    out.append(f"{counter:>6}\t{body}")
                else:
                    out.append(body)
            elif number:
                counter += 1
                out.append(f"{counter:>6}\t{body}")
            else:
                out.append(body)
        result = "\n".join(out)
        if trailing:
            result += "\n"
        return result
