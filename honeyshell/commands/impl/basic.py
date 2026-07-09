"""A small starter set of built-in commands.

Chosen to exercise the whole contract end-to-end without the interpreter:
pure output (echo/pwd/whoami), shell-state mutation (cd), filesystem reads
(cat/ls), stdin consumption for pipelines (cat with no args), and exit codes
(true/false). Richer flag handling (ls -l, echo -e, ...) is deferred; the
gaps are marked so later refinements are obvious.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.fs import FSError, NotADirectory


@register("echo", "/bin/echo")
class Echo(Command):
    async def run(self) -> int:
        args = self.args
        newline = True
        # consume leading -n flags (echo's only flag we support for now)
        while args and args[0] == "-n":
            newline = False
            args = args[1:]
        text = " ".join(args)
        self.write(text + "\n" if newline else text)
        return 0


@register("pwd", "/bin/pwd")
class Pwd(Command):
    async def run(self) -> int:
        self.line(self.ctx.cwd)
        return 0


@register("whoami", "/usr/bin/whoami")
class Whoami(Command):
    async def run(self) -> int:
        self.line(self.ctx.username)
        return 0


@register("true", "/bin/true")
class True_(Command):
    async def run(self) -> int:
        return 0


@register("false", "/bin/false")
class False_(Command):
    async def run(self) -> int:
        return 1


@register("cd")
class Cd(Command):
    async def run(self) -> int:
        target = self.args[0] if self.args else self.ctx.home
        try:
            st = self.ctx.fs.stat(target, self.ctx.cwd)
        except FSError as e:
            return self.fail(f"{target}: {e.message}")
        if not st.is_dir:
            return self.fail(f"{target}: Not a directory")
        self.ctx.cwd = self.ctx.fs.normalize(target, self.ctx.cwd)
        return 0


@register("cat", "/bin/cat")
class Cat(Command):
    async def run(self) -> int:
        # No operands: copy stdin to stdout (pipeline behaviour).
        if not self.args:
            self.write(await self.read_all())
            return 0
        rc = 0
        for path in self.args:
            try:
                self.write(self.ctx.fs.readtext(path, self.ctx.cwd))
            except FSError as e:
                rc = self.fail(f"{path}: {e.message}")
        return rc


@register("exit", "logout")
class Exit(Command):
    async def run(self) -> int:
        self.ctx.should_exit = True
        if self.args:
            try:
                return int(self.args[0]) & 0xFF
            except ValueError:
                self.errline(f"{self.prog}: {self.args[0]}: numeric argument required")
                return 2
        return 0


@register("ls", "/bin/ls")
class Ls(Command):
    """List directory contents.

    Supported: ``-a`` (show dotfiles). Long format (``-l``) is deferred.

    Output layout mirrors GNU coreutils: on a tty we pack names into
    *column-major* columns sized to the terminal width (down each column,
    then across); off a tty (pipes, redirection, exec mode) we emit one
    entry per line so downstream tools parse it reliably. The tty decision
    comes from :attr:`ShellContext.is_tty`.
    """

    async def run(self) -> int:
        show_all = False
        operands: list[str] = []
        for a in self.args:
            if a.startswith("-") and a != "-":
                # Validate every flag character; real ls rejects unknown ones
                # with "invalid option -- 'X'" and exit status 2. We currently
                # implement only -a; others are reported as invalid so the
                # honeypot doesn't silently accept bogus flags (an easy tell).
                for ch in a[1:]:
                    if ch == "a":
                        show_all = True
                    else:
                        self.errline(f"{self.prog}: invalid option -- '{ch}'")
                        self.errline(f"Try '{self.prog} --help' for more information.")
                        return 2
            else:
                operands.append(a)
        if not operands:
            operands = ["."]

        rc = 0
        multi = len(operands) > 1
        blocks: list[str] = []
        for path in operands:
            try:
                st = self.ctx.fs.stat(path, self.ctx.cwd)
            except FSError as e:
                # bash prints "cannot access 'X'" for a bad operand; keep the
                # simpler "X: <reason>" form we already use elsewhere for
                # consistency with the rest of the honeypot's messages.
                rc = self.fail(f"cannot access '{path}': {e.message}")
                continue
            if not st.is_dir:
                blocks.append(path)
                continue
            names = self.ctx.fs.listdir(path, self.ctx.cwd)
            if show_all:
                # Real `ls -a` always lists the . and .. entries first; the
                # VFS listdir omits them, so add them back (an empty home
                # otherwise prints nothing, an obvious honeypot tell).
                names = [".", ".."] + names
            else:
                names = [n for n in names if not n.startswith(".")]
            body = self._layout(names)
            blocks.append((f"{path}:\n" if multi else "") + body)
        out = "\n\n".join(b for b in blocks if b != "")
        if out:
            self.line(out)
        return rc

    def _layout(self, names: list[str]) -> str:
        """Format entry names: column-major grid on a tty, else one per line."""
        if not names:
            return ""
        if not self.ctx.is_tty:
            return "\n".join(names)
        return _columnate(names, self.ctx.term_width)


def _columnate(names: list[str], width: int, gap: int = 2) -> str:
    """Pack ``names`` into GNU-``ls``-style column-major columns.

    Names run *down* each column before wrapping to the next (column-major
    fill), columns are padded to the widest name they contain plus ``gap``
    spaces. We pick the largest column count whose padded rows still fit in
    ``width``; a single over-wide name degrades to one entry per line.
    """
    longest = max(len(n) for n in names)
    # Upper bound on columns that could possibly fit.
    max_cols = max(1, min(len(names), (width + gap) // (longest + gap)))

    for ncols in range(max_cols, 0, -1):
        nrows = -(-len(names) // ncols)  # ceil division
        # Column-major: column c holds names[c*nrows : (c+1)*nrows].
        col_widths = []
        for c in range(ncols):
            col = names[c * nrows:(c + 1) * nrows]
            col_widths.append(max((len(n) for n in col), default=0))
        total = sum(w + gap for w in col_widths) - gap
        if total <= width or ncols == 1:
            rows = []
            for r in range(nrows):
                cells = []
                for c in range(ncols):
                    idx = c * nrows + r
                    if idx >= len(names):
                        continue
                    name = names[idx]
                    # No trailing pad on the last cell of a row.
                    is_last = (c == ncols - 1) or (c * nrows + nrows + r >= len(names))
                    cells.append(name if is_last else name.ljust(col_widths[c] + gap))
                rows.append("".join(cells).rstrip())
            return "\n".join(rows)
    return "\n".join(names)
