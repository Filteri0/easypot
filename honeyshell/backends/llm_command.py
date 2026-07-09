"""LLMCommand — wraps an LLM response as an ordinary Command.

The whole point is that the interpreter's dispatch loop doesn't change: on a
registry miss it constructs an ``LLMCommand`` exactly like any built-in and
``await``\\s ``run()``. Inside, the command asks the resolver for
``(A_i, C_i, F_i)`` and:

* writes ``A_i`` to stdout (the terminal output the attacker sees),
* stashes ``C_i``/``F_i`` on the context for the ``memory/`` milestone to fold
  into SR/H and Memory Pruning (kept as a plain list here, no pruning yet),
* falls back to bash's ``command not found`` (exit 127) if the LLM is down, so
  behaviour degrades safely.

Exit status: we return 0 for a produced response. The real exit code a command
would set isn't part of the paper's (A,C,F) triple; deriving it from the output
is left as a later refinement.
"""

from __future__ import annotations

from honeyshell.backends.fs_applier import apply_fs_ops
from honeyshell.backends.resolver import ChainResolver
from honeyshell.commands.base import Command

__all__ = ["LLMCommand", "make_llm_command_factory"]


class LLMCommand(Command):
    """A Command whose output comes from the LLM resolver.

    Constructed with the same signature as any Command plus an injected
    ``resolver`` (and optional ``session_id``); see
    :func:`make_llm_command_factory` for how the interpreter wires it in
    without knowing about backends.
    """

    resolver: ChainResolver
    session_id: str | None = None

    async def run(self) -> int:
        memory = getattr(self.ctx, "memory", None)
        # Supply prior SR/H from session memory so multi-turn attacks stay
        # consistent (empty on the first turn or when memory is disabled).
        sr = memory.sr_notes() if memory is not None else None
        history = memory.as_history() if memory is not None else None

        resolution = await self.resolver.resolve(
            self.argv,
            self.ctx.cwd,
            username=self.ctx.username,
            session_id=self.session_id,
            sr=sr,
            history=history,
        )
        if resolution is None:
            # LLM unavailable -> behave like bash for an unknown command.
            self.errline(f"bash: {self.prog}: command not found")
            return 127

        if resolution.output:
            # The model returns output without a trailing newline; add one so
            # it sits on its own line like a real command's output.
            text = resolution.output
            self.write(text if text.endswith("\n") else text + "\n")

        # --- C_i -> VirtualFS -------------------------------------------------
        # Apply the structured state change to the real (emulated) tree so what
        # the attacker sees next (`ls`, `cat`) matches what the model narrated.
        # This is the core of "C_i 回寫 VFS": the VFS stays the single source of
        # truth; the model's memory is reconciled to it below. Never raises.
        report = apply_fs_ops(
            self.ctx.fs, self.ctx.cwd, resolution.fs_ops,
            uid=self.ctx.uid, gid=self.ctx.uid,
        )

        # Reconcile memory with what ACTUALLY happened, not what the model
        # claimed. When ops applied, the SR note and impact come from the
        # applier (reliable); otherwise fall back to the model's prose C_i and
        # its self-scored F_i (the non-structural path, e.g. "started nginx").
        if report.changed:
            state_note = report.notes()
            impact = report.impact
        else:
            state_note = resolution.state_change
            impact = resolution.impact

        # Fold this turn into session memory (SR/H/FL), then apply decay +
        # pruning so the running prompt stays within budget. A cached response
        # is still recorded — it's part of the conversation the attacker sees.
        if memory is not None:
            memory.record(
                " ".join(self.argv),
                resolution.output,
                state_note,
                impact,
            )
            pruner = getattr(self.ctx, "pruner", None)
            if pruner is not None:
                pruner.step(memory)
        return 0


def make_llm_command_factory(resolver: ChainResolver, session_id: str | None = None):
    """Return a factory the interpreter can call like a registry class.

    The interpreter constructs commands as ``cls(ctx, argv, stdin, stdout,
    stderr)``. We return a callable with that signature that produces a
    fully-wired :class:`LLMCommand`, so the dispatch site needs only to swap the
    ``command not found`` branch for ``factory(...)`` — no backend imports leak
    into the interpreter.
    """

    def _factory(ctx, argv, stdin=None, stdout=None, stderr=None):
        cmd = LLMCommand(ctx, argv, stdin, stdout, stderr)
        cmd.resolver = resolver
        cmd.session_id = session_id
        return cmd

    return _factory
