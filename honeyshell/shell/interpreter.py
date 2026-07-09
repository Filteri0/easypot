"""The shell interpreter.

Takes a raw command-line string, parses it, expands tokens, and executes the
resulting jobs against a :class:`~honeyshell.commands.context.ShellContext` —
dispatching commands via the registry and wiring pipelines/redirections to the
:class:`~honeyshell.fs.VirtualFS`.

This is the first module where a full round trip happens::

    interp = Interpreter(ctx, stdout, stderr)
    await interp.execute("cd /etc && cat hostname | cat")

Execution model
---------------
* **Job control** (``;`` ``&&`` ``||``): standard short-circuit semantics.
  ``&`` (background) currently runs inline; true async job control / PIDs are
  deferred.
* **Pipelines** are *buffered*: each stage runs to completion, its stdout is
  captured and fed as the next stage's stdin. This is simple and correct for
  the non-streaming commands a honeypot emulates; concurrent streaming (needed
  only for things like ``tail -f | grep``) is a later refinement and the point
  at which a dedicated ``pipeline.py`` would be extracted.
* **Redirection**: ``>`` / ``>>`` send stdout to a VirtualFS file (truncate /
  append); ``<`` feeds stdin from a file. fd-qualified redirects (``2>``,
  ``2>&1``) are still rejected by the parser and thus never reach here.
* **Unknown command** -> ``bash: <cmd>: command not found`` (exit 127). This is
  exactly the seam where a future LLM backend takes over instead of failing.
"""

from __future__ import annotations

from honeyshell.commands import registry
from honeyshell.commands.context import ShellContext
from honeyshell.commands.streams import (
    NullReader,
    Readable,
    StringReader,
    StringWriter,
    Writable,
)
from honeyshell.fs import FSError
from honeyshell.shell.expand import expand_token
from honeyshell.shell.parser import ParseError, Pipeline, SimpleCommand, parse

__all__ = ["Interpreter"]


class Interpreter:
    def __init__(
        self,
        ctx: ShellContext,
        stdout: Writable,
        stderr: Writable | None = None,
        *,
        miss_handler=None,
    ) -> None:
        self.ctx = ctx
        self.stdout = stdout
        self.stderr = stderr or stdout
        self.last_status = 0
        #: Optional factory called when the registry can't resolve a command:
        #: ``miss_handler(ctx, argv, stdin, stdout, stderr) -> Command``. This
        #: is the LLM seam — the transport injects a factory built by
        #: ``backends.make_llm_command_factory``. When None (default, and in
        #: unit tests) the interpreter keeps the plain bash "command not found"
        #: behaviour, so nothing else changes.
        self.miss_handler = miss_handler
        registry.discover()  # idempotent; ensures builtins are registered

    # -- public entry --

    async def execute(self, line: str) -> int:
        """Parse and run one command line. Returns the final exit status."""
        try:
            cmdline = parse(line)
        except ParseError as e:
            self.stderr.write(f"-bash: {e}\n")
            self.last_status = 2
            return 2

        if not cmdline:
            return self.last_status

        status = self.last_status
        run_next = True
        for job in cmdline.jobs:
            if run_next:
                status = await self._run_pipeline(job.pipeline)
                self.last_status = status
            conn = job.connector
            if conn == "&&":
                run_next = status == 0
            elif conn == "||":
                run_next = status != 0
            else:  # ';', '&', None
                run_next = True
        return status

    # -- pipelines --

    async def _run_pipeline(self, pipeline: Pipeline) -> int:
        stages = pipeline.commands
        prev_text: str | None = None
        status = 0
        for idx, node in enumerate(stages):
            is_last = idx == len(stages) - 1
            first = idx == 0

            stdin, in_err = self._make_stdin(node, prev_text, first)
            base_out: Writable = self.stdout if is_last else StringWriter()
            stdout, flush = self._make_stdout(node, base_out)

            if in_err is not None:
                self.stderr.write(f"-bash: {in_err}\n")
                status = 1
                prev_text = None if is_last else ""
                continue

            status = await self._dispatch(node, stdin, stdout)

            if flush is not None:
                ferr = flush()
                if ferr is not None:
                    self.stderr.write(f"-bash: {ferr}\n")
                    status = 1

            if is_last:
                prev_text = None
            elif flush is not None:
                prev_text = ""  # output diverted to a file; nothing flows on
            else:
                assert isinstance(base_out, StringWriter)
                prev_text = base_out.getvalue()
        return status

    # -- stdin / stdout wiring --

    def _make_stdin(
        self, node: SimpleCommand, prev_text: str | None, first: bool
    ) -> tuple[Readable | None, str | None]:
        in_redir = [r for r in node.redirects if r.op == "<"]
        if in_redir:
            target = self._expand(in_redir[-1].target)
            try:
                text = self.ctx.fs.readtext(target, self.ctx.cwd)
            except FSError as e:
                return None, f"{target}: {e.message}"
            return StringReader(text), None
        if first:
            return NullReader(), None
        return StringReader(prev_text or ""), None

    def _make_stdout(self, node: SimpleCommand, base_out: Writable):
        out_redir = [r for r in node.redirects if r.op in (">", ">>")]
        if not out_redir:
            return base_out, None
        r = out_redir[-1]  # last redirect wins
        target = self._expand(r.target)
        buf = StringWriter()

        def flush() -> str | None:
            data = buf.getvalue()
            try:
                if r.op == ">>" and self.ctx.fs.is_file(target, self.ctx.cwd):
                    data = self.ctx.fs.readtext(target, self.ctx.cwd) + data
                self.ctx.fs.write_file(target, data, self.ctx.cwd)
            except FSError as e:
                return f"{target}: {e.message}"
            return None

        return buf, flush

    # -- dispatch --

    async def _dispatch(
        self, node: SimpleCommand, stdin: Readable, stdout: Writable
    ) -> int:
        argv: list[str] = []
        for tok in node.argv:
            expanded = self._expand(tok)
            # drop unquoted words that expanded to nothing (approximate bash);
            # keep originally-empty (quoted "") tokens.
            if expanded == "" and tok != "":
                continue
            argv.append(expanded)

        if not argv:
            return 0  # redirect-only command (file already handled by flush)

        token = argv[0]
        cls = registry.resolve(token)
        if cls is None:
            if self.miss_handler is not None:
                # LLM seam: hand the command to the injected backend factory.
                cmd = self.miss_handler(
                    self.ctx, argv, stdin, stdout, self.stderr
                )
                try:
                    code = await cmd.run()
                except Exception:  # noqa: BLE001 — a backend error must not crash
                    self.stderr.write(f"bash: {token}: command not found\n")
                    return 127
                return code if isinstance(code, int) else 0
            self.stderr.write(f"bash: {token}: command not found\n")
            return 127

        cmd = cls(self.ctx, argv, stdin, stdout, self.stderr)
        try:
            code = await cmd.run()
        except Exception:  # noqa: BLE001 - never let a buggy command crash the session
            self.stderr.write(f"bash: {token}: internal error\n")
            return 1
        return code if isinstance(code, int) else 0

    # -- helpers --

    def _expand(self, tok: str) -> str:
        return expand_token(tok, self.ctx, self.last_status)
