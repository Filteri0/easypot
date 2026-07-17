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
from honeyshell.commands.base import DeferToLLM
from honeyshell.commands.context import ShellContext
from honeyshell.core.events import CommandEvent, ErrorEvent
from honeyshell.commands.streams import (
    NullReader,
    Readable,
    StringReader,
    StringWriter,
    Writable,
)
from honeyshell.fs import FSError
from honeyshell.shell.cmdsubst import contains_substitution, substitute_commands
from honeyshell.shell.expand import expand_token
from honeyshell.shell.parser import ParseError, Pipeline, SimpleCommand, parse
from honeyshell.shell.shell_builtins import (
    apply_assignments,
    handle_noop_builtin,
    is_assignment,
    is_control_noise,
)

__all__ = ["Interpreter"]


class _NullWriter:
    """A Writable that discards everything — the target for ``2>/dev/null``."""

    def write(self, data: str) -> None:  # noqa: D401
        pass


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
        #: Wire the re-entrant hook the sh/bash builtin uses to run sub-commands
        #: through this same interpreter (shared state + miss_handler).
        ctx.run_line = self.execute

    # -- public entry --

    async def execute(
        self,
        line: str,
        *,
        stdout: Writable | None = None,
        stderr: Writable | None = None,
    ) -> int:
        """Parse and run one command line. Returns the final exit status.

        ``stdout``/``stderr`` optionally redirect this run's output — used by
        the ``sh``/``bash`` builtin so a piped-in or ``-c`` script writes to
        sh's own stdout rather than the session's. When omitted, output goes to
        the interpreter's configured streams (the normal case).
        """
        prev_out, prev_err = self.stdout, self.stderr
        if stdout is not None:
            self.stdout = stdout
        if stderr is not None:
            self.stderr = stderr
        try:
            return await self._execute_inner(line)
        except Exception as exc:  # noqa: BLE001
            # Defensive top-level catch. Everything below *should* handle its
            # own errors (parse/FS/command/backend all do), but a future
            # expansion/arithmetic/command bug could raise past them. Without
            # this, the exception unwinds through the session loop and the whole
            # shell dies mid-session — a strong "not a real bash" fingerprint.
            # Instead: emit a generic error (never a traceback), record it as
            # high-value intel (an attacker who reliably triggers this found an
            # uncovered edge), and let the prompt loop continue.
            self._emit(ErrorEvent(
                raw=line, phase="execute", exc_type=type(exc).__name__,
            ))
            self.stderr.write("-bash: internal error\n")
            self.last_status = 1
            return 1
        finally:
            self.stdout, self.stderr = prev_out, prev_err

    async def _execute_inner(self, line: str) -> int:
        # Command substitution runs before parsing (bash evaluates $(...) prior
        # to word-splitting; our POSIX lexer would otherwise shred it).
        if contains_substitution(line):
            line = await substitute_commands(line, self._capture_line)

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
            # Read-permission gate, mirroring the file-reading builtins: a
            # non-root user redirecting from a file they can't read gets
            # "Permission denied", not the file contents. access() is the same
            # single judge cat/head/... use.
            uid = self.ctx.uid
            gid = getattr(self.ctx, "login_uid", None)
            gid = gid if gid is not None else uid
            try:
                exists = self.ctx.fs.exists(target, self.ctx.cwd)
            except FSError:
                exists = False
            if exists and not self.ctx.fs.access(
                    target, "r", uid, gid, self.ctx.cwd):
                return None, f"{target}: Permission denied"
            try:
                text = self.ctx.fs.readtext(target, self.ctx.cwd)
            except FSError as e:
                return None, f"{target}: {e.message}"
            return StringReader(text), None
        if first:
            return NullReader(), None
        return StringReader(prev_text or ""), None

    def _make_stdout(self, node: SimpleCommand, base_out: Writable):
        # Only plain stdout file redirects (fd 1) open a file here; fd-2 and dup
        # forms are resolved in _dispatch via _resolve_stderr so both streams
        # can be steered together (2>&1, >&2, &>file).
        out_redir = [r for r in node.redirects
                     if r.op in (">", ">>") and r.fd == 1 and r.dup is None
                     and not r.both]
        both_redir = [r for r in node.redirects if r.both]
        if both_redir:
            out_redir = out_redir + both_redir
        if not out_redir:
            return base_out, None
        r = out_redir[-1]  # last redirect wins
        target = self._expand(r.target)
        buf = StringWriter()

        def flush() -> str | None:
            return self._flush_redirect(buf, target, r.op)

        return buf, flush

    def _resolve_stderr(self, node: SimpleCommand, stdout: Writable):
        """Decide where this command's stderr goes, per fd redirects.

        Returns (stderr_writer, flush_or_None). Semantics:
        * ``2>file`` / ``2>>file`` -> stderr to a VFS file.
        * ``2>&1``                 -> stderr merges into stdout.
        * ``>&2`` / ``1>&2``       -> stdout already handled; stderr stays.
        * ``&>file``               -> both streams already point at the file
                                      (stdout buffer); stderr rides along.
        * ``2>/dev/null``          -> discarded.
        Absent any of these, stderr flows to the session as usual.
        """
        # &>file: stderr shares the stdout buffer (which flush writes out).
        if any(r.both for r in node.redirects):
            return stdout, None
        # >&2 / 1>&2: stdout was redirected to stderr in _dispatch; nothing to
        # do for stderr itself here.
        err_redir = [r for r in node.redirects if r.fd == 2]
        if not err_redir:
            return self.stderr, None
        r = err_redir[-1]
        if r.dup == 1:                      # 2>&1
            return stdout, None
        target = self._expand(r.target)
        if target in ("/dev/null", "/dev/zero"):
            return _NullWriter(), None
        buf = StringWriter()

        def flush() -> str | None:
            return self._flush_redirect(buf, target, r.op)

        return buf, flush

    def _flush_redirect(self, buf, target: str, op: str) -> str | None:
        """Write a redirect buffer to the VFS, emulating Permission denied.

        A new file needs write on its parent dir; overwriting needs write on
        the file itself. Mirrors a real shell rejecting `echo x > /root/f` for
        a non-root user. root (uid 0) bypasses via access()."""
        data = buf.getvalue()
        uid = self.ctx.uid
        gid = getattr(self.ctx, "login_uid", None) or uid
        try:
            exists = self.ctx.fs.is_file(target, self.ctx.cwd)
        except FSError:
            exists = False
        if exists:
            ok = self.ctx.fs.access(target, "w", uid, gid, self.ctx.cwd)
        else:
            norm = self.ctx.fs.normalize(target, self.ctx.cwd)
            parent = norm.rsplit("/", 1)[0] or "/"
            ok = self.ctx.fs.access(parent, "w", uid, gid, self.ctx.cwd)
        if not ok:
            return f"{target}: Permission denied"
        try:
            if op == ">>" and self.ctx.fs.is_file(target, self.ctx.cwd):
                data = self.ctx.fs.readtext(target, self.ctx.cwd) + data
            self.ctx.fs.write_file(target, data, self.ctx.cwd)
        except FSError as e:
            return f"{target}: {e.message}"
        return None

    # -- dispatch --

    async def _dispatch(
        self, node: SimpleCommand, stdin: Readable, stdout: Writable
    ) -> int:
        # Resolve where stderr goes for this command (2>file, 2>&1, 2>/dev/null,
        # &>file). ``cmd_stderr`` replaces self.stderr for everything below.
        cmd_stderr, err_flush = self._resolve_stderr(node, stdout)
        # >&2 / 1>&2: stdout is redirected onto stderr's destination.
        if any(r.fd == 1 and r.dup == 2 for r in node.redirects):
            stdout = self.stderr

        try:
            return await self._dispatch_inner(node, stdin, stdout, cmd_stderr)
        finally:
            if err_flush is not None:
                ferr = err_flush()
                if ferr is not None:
                    self.stderr.write(f"-bash: {ferr}\n")

    async def _dispatch_inner(
        self, node: SimpleCommand, stdin: Readable, stdout: Writable,
        cmd_stderr: Writable,
    ) -> int:
        raw_argv = node.argv

        # Pure assignment line (VAR=val ...): store into environ before any
        # expansion of a command name. Values are still expanded ($A in B=$A).
        if is_assignment(raw_argv):
            return apply_assignments(raw_argv, self.ctx, self._expand)

        # Leading assignments followed by a command (``FOO=bar cmd args``): the
        # common "temporary environment" form (e.g.
        # ``DEBIAN_FRONTEND=noninteractive apt ...``). Apply the assignments to
        # environ, then dispatch the remaining words as the command. (We don't
        # scope them to just this command — for a throwaway per-connection
        # session that's an acceptable simplification.)
        raw_argv = self._strip_leading_assignments(raw_argv)

        argv: list[str] = []
        for tok in raw_argv:
            expanded = self._expand(tok)
            # drop unquoted words that expanded to nothing (approximate bash);
            # keep originally-empty (quoted "") tokens.
            if expanded == "" and tok != "":
                continue
            argv.append(expanded)

        if not argv:
            return 0  # redirect-only command (file already handled by flush)

        # Shell control-flow keywords (if/for/…): swallow rather than dispatch
        # as commands. The block body runs on its own lines; this only avoids
        # "if: command not found" noise for scripts piped into sh (stage A).
        if is_control_noise(argv):
            return 0

        # No-op shell builtins (set -e, export, unset, :, umask, …). export and
        # unset really mutate environ; the rest succeed quietly.
        noop = handle_noop_builtin(argv, self.ctx, self._expand)
        if noop is not None:
            return noop

        token = argv[0]
        cls = registry.resolve(token)

        # 已註冊命令先執行，但可能**降級**（raise DeferToLLM）——當它只能忠實
        # 模擬其真實行為的一個子集時（例如 awk 處理 ``{print $N}`` 但不處理
        # ``BEGIN``/樣式）。降級會把命令重新分類為真正的 miss，讓 audit 流保持
        # 誠實（hit=False）——見 commands/base.py::DeferToLLM。因此我們在**得知**
        # hit 命令是否降級**之後**才發出 CommandEvent，而非之前，好讓 miss rate
        # 反映真實情況。
        if cls is not None:
            cmd = cls(self.ctx, argv, stdin, stdout, cmd_stderr)
            try:
                code = await cmd.run()
            except DeferToLLM:
                # 內建棄權。把它記成 miss，並走與未註冊命令相同的 LLM 接縫。若
                # 沒接後端，退回命令的保守輸出，而非會被指紋辨識的錯誤。
                self._emit(CommandEvent(
                    raw=" ".join(argv), resolved_name=None, hit=False,
                ))
                return await self._miss(
                    argv, token, stdin, stdout, cmd_stderr, deferred=cmd
                )
            except Exception:  # noqa: BLE001 - 絕不讓出錯的命令弄垮整個 session
                self._emit(CommandEvent(
                    raw=" ".join(argv), resolved_name=token, hit=True,
                ))
                cmd_stderr.write(f"bash: {token}: internal error\n")
                return 1
            # 真正的 hit。
            self._emit(CommandEvent(
                raw=" ".join(argv), resolved_name=token, hit=True,
            ))
            return code if isinstance(code, int) else 0

        # 未註冊的 token -> 真正的 miss。
        self._emit(CommandEvent(
            raw=" ".join(argv), resolved_name=None, hit=False,
        ))
        return await self._miss(argv, token, stdin, stdout, cmd_stderr)

    async def _miss(self, argv, token, stdin, stdout, cmd_stderr, deferred=None):
        """處理 miss：交給 LLM 後端，否則優雅降級。

        ``deferred`` 是 raise 了 DeferToLLM 的內建實例（若有）；沒接 LLM 時由它的
        :meth:`fallback` 提供保守輸出。對真正未知的命令，維持 bash 的
        ``command not found``。
        """
        if self.miss_handler is not None:
            # LLM 接縫：把命令交給注入的後端工廠。
            cmd = self.miss_handler(self.ctx, argv, stdin, stdout, cmd_stderr)
            try:
                code = await cmd.run()
            except Exception:  # noqa: BLE001 — 後端錯誤不得導致崩潰
                if deferred is not None:
                    return await self._safe_fallback(deferred, token, cmd_stderr)
                cmd_stderr.write(f"bash: {token}: command not found\n")
                return 127
            return code if isinstance(code, int) else 0
        if deferred is not None:
            # 已註冊但降級、且無 LLM：執行檔存在，所以回 "command not found" 是說謊。
            # 改用它的保守輸出。
            return await self._safe_fallback(deferred, token, cmd_stderr)
        cmd_stderr.write(f"bash: {token}: command not found\n")
        return 127

    async def _safe_fallback(self, deferred, token, cmd_stderr) -> int:
        try:
            code = await deferred.fallback()
        except Exception:  # noqa: BLE001 — fallback 絕不得弄垮 session
            cmd_stderr.write(f"bash: {token}: internal error\n")
            return 1
        return code if isinstance(code, int) else 0

    # -- helpers --

    def _expand(self, tok: str) -> str:
        return expand_token(tok, self.ctx, self.last_status)

    def _emit(self, event) -> None:
        """Publish an audit event if a bus is wired. Stamps the session id and
        never propagates errors — auditing must not perturb the honeypot."""
        bus = getattr(self.ctx, "event_bus", None)
        if bus is None:
            return
        try:
            if getattr(event, "session_id", None) is None:
                event.session_id = getattr(self.ctx, "session_id", None)
            bus.emit(event)
        except Exception:  # noqa: BLE001 — audit path is strictly best-effort
            pass

    async def _capture_line(self, line: str) -> str:
        """Run one command line, capturing and returning its stdout.

        Used as the runner for command substitution. Executes through this same
        interpreter (shared VFS/cwd/env + miss_handler) with stdout diverted to
        a buffer; stderr still flows to the session so errors remain visible.
        A depth guard reuses the shell-nesting counter so a substitution that
        recurses endlessly can't spin forever.
        """
        if self.ctx.shell_depth >= 8:
            return ""
        buf = StringWriter()
        outer_cwd = self.ctx.cwd
        self.ctx.shell_depth += 1
        try:
            await self.execute(line, stdout=buf)
        finally:
            self.ctx.shell_depth -= 1
            # A substitution's cd (e.g. $(cd /x && pwd)) is contained; it must
            # not move the outer session's working directory.
            self.ctx.cwd = outer_cwd
        return buf.getvalue()

    def _strip_leading_assignments(self, argv: list[str]) -> list[str]:
        """Apply and remove leading ``NAME=value`` words, return the rest.

        Handles the ``FOO=bar cmd`` temporary-environment form. Stops at the
        first non-assignment word (the command). Values are expanded.
        """
        i = 0
        for tok in argv:
            name, sep, raw = tok.partition("=")
            if sep == "=" and name and (name[0].isalpha() or name[0] == "_") \
                    and all(c.isalnum() or c == "_" for c in name):
                self.ctx.environ[name] = self._expand(raw)
                i += 1
            else:
                break
        return argv[i:]
