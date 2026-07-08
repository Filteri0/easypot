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


@register("ls", "/bin/ls")
class Ls(Command):
    async def run(self) -> int:
        # supported: -a (show dotfiles). One entry per line (safe when piped);
        # column layout for a tty and -l long format are deferred.
        show_all = False
        operands: list[str] = []
        for a in self.args:
            if a.startswith("-") and a != "-":
                show_all = show_all or ("a" in a[1:])
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
                rc = self.fail(f"{path}: {e.message}")
                continue
            if not st.is_dir:
                blocks.append(path)
                continue
            names = self.ctx.fs.listdir(path, self.ctx.cwd)
            if not show_all:
                names = [n for n in names if not n.startswith(".")]
            body = "\n".join(names)
            blocks.append((f"{path}:\n" if multi else "") + body)
        out = "\n\n".join(b for b in blocks if b != "")
        if out:
            self.line(out)
        return rc
