"""chmod — change file mode bits.

Really mutates the VFS via the new ``fs.chmod`` API so a following ``ls -l``
reflects the change (state consistency — the same principle as the other
VFS-mutating builtins). Supports octal modes (``755``, ``0644``) and a common
subset of symbolic modes (``+x``, ``u+w``, ``go-r``). ``-R`` recurses.

Deferred: full symbolic grammar (``a=rx``, comma lists), setuid/sticky nuance.
"""

from __future__ import annotations

from honeyshell.commands.base import Command
from honeyshell.commands.registry import register
from honeyshell.commands.impl._fsflags import _split_flags
from honeyshell.fs import FSError, NoSuchFile

__all__ = ["Chmod"]


@register("chmod", "/bin/chmod")
class Chmod(Command):
    async def run(self) -> int:
        flags, operands = _split_flags(self.args)
        recursive = bool({"R", "recursive"} & flags)
        if len(operands) < 2:
            return self.fail("missing operand")
        mode_spec, paths = operands[0], operands[1:]
        rc = 0
        for path in paths:
            try:
                self._apply(mode_spec, path, recursive)
            except NoSuchFile:
                rc = self.fail(
                    f"cannot access '{path}': No such file or directory"
                )
            except ValueError:
                return self.fail(f"invalid mode: '{mode_spec}'")
            except FSError as e:
                rc = self.fail(f"changing perms of '{path}': {e.message}")
        return rc

    def _apply(self, mode_spec: str, path: str, recursive: bool) -> None:
        cur = self.ctx.fs.stat(path, self.ctx.cwd).perm
        new = _resolve_mode(mode_spec, cur)
        self.ctx.fs.chmod(path, new, self.ctx.cwd)
        if recursive and self.ctx.fs.stat(path, self.ctx.cwd).is_dir:
            for name in self.ctx.fs.listdir(path, self.ctx.cwd):
                self._apply(mode_spec, f"{path}/{name}", recursive)


def _resolve_mode(spec: str, current: int) -> int:
    """Octal literal, or a small symbolic subset applied to ``current``."""
    # Octal form: 755, 0644, etc.
    if spec and all(c in "01234567" for c in spec):
        return int(spec, 8)
    # Symbolic: [ugoa*][+-=][rwx]
    who = ""
    i = 0
    while i < len(spec) and spec[i] in "ugoa":
        who += spec[i]
        i += 1
    if i >= len(spec) or spec[i] not in "+-=":
        raise ValueError(spec)
    op = spec[i]
    perms = spec[i + 1:]
    bits = 0
    for p in perms:
        if p == "r":
            bits |= 0b100
        elif p == "w":
            bits |= 0b010
        elif p == "x":
            bits |= 0b001
        else:
            raise ValueError(spec)
    targets = who or "a"
    mask = 0
    if "u" in targets or "a" in targets:
        mask |= bits << 6
    if "g" in targets or "a" in targets:
        mask |= bits << 3
    if "o" in targets or "a" in targets:
        mask |= bits
    if op == "+":
        return current | mask
    if op == "-":
        return current & ~mask
    return mask  # '='  (only the targeted triads; simplified)
