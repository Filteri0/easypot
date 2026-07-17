"""The async command base class.

Design lineage
--------------
Borrowed from Cowrie's ``HoneyPotCommand``: every emulated command is a class
with a small, uniform contract (write output, read input, report an exit
status). We keep that shape but make it ``async`` so it composes with
asyncio/asyncssh, and we replace Cowrie's manual ``cmdstack`` with the natural
coroutine call stack — an interactive command simply ``await``\\s
:meth:`read_line` and blocks the shell until its ``run`` returns.

Contract
--------
The interpreter resolves a command token to a ``Command`` subclass, then::

    cmd = SubCls(ctx, argv, stdin, stdout, stderr)
    exit_code = await cmd.run()

* ``argv`` is the command as invoked; ``argv[0]`` is the token the attacker
  typed (``ls`` or ``/bin/ls``), and :pyattr:`args` is everything after it.
* ``run`` returns an ``int`` exit code. Subclasses override ``run`` only.
* Output goes through :meth:`write`/:meth:`line` (stdout) and
  :meth:`error`/:meth:`errline` (stderr); the interpreter/pipeline decides
  where those streams actually go.
"""

from __future__ import annotations

from honeyshell.commands.context import ShellContext
from honeyshell.commands.streams import (
    NullReader,
    Readable,
    StringWriter,
    Writable,
)

__all__ = ["Command", "DeferToLLM"]


class DeferToLLM(Exception):
    """已註冊命令 raise 此例外，將該次呼叫交給 LLM 接縫處理。

    設計血緣（HANDOFF v5，「做法 B」）：registry/miss_handler 的分工原本代表
    *hit* 命令（有註冊類別者）永遠不會走到 LLM。但有些內建只能忠實處理其真實
    行為的**一個子集**——``awk`` 確定性地涵蓋常見的 ``{print $N}`` 欄位提取
    idiom，但複雜 program（``/pattern/``、``BEGIN``、算術）罕見，交給模型生成
    比假造更好。

    與其發出誤導性的 ``hit=True`` 卻偷偷呼叫 LLM（那會污染整份報告賴以成立的
    miss rate 數字，見 HANDOFF §21/§32），這類命令改 raise ``DeferToLLM``。
    interpreter 捕捉它、把命令重新分類為真正的 miss（audit 流裡 ``hit=False``），
    並走一般的 ``miss_handler``。若沒接 LLM 後端，interpreter 會透過
    :meth:`Command.fallback` 退回命令自己的保守輸出，讓蜜罐永不崩潰、也不會用
    假造錯誤暴露自己。

    這同時保住三件事的誠實：hit/miss 統計（降級命令算 miss）、安全模型（LLM
    路徑是唯一接縫）、以及韌性（無 LLM 部署仍能合理回應）。此機制可複用——未來
    複雜的 ``sed``/``grep`` 也能降級。
    """


class Command:
    #: Canonical name; set automatically by @register if left blank.
    name: str = ""

    def __init__(
        self,
        ctx: ShellContext,
        argv: list[str],
        stdin: Readable | None = None,
        stdout: Writable | None = None,
        stderr: Writable | None = None,
    ) -> None:
        self.ctx = ctx
        self.argv = list(argv)
        self.stdin: Readable = stdin or NullReader()
        self.stdout: Writable = stdout or StringWriter()
        self.stderr: Writable = stderr or StringWriter()
        self.exit_code = 0

    # -- convenience accessors --

    @property
    def prog(self) -> str:
        """The token as invoked (argv[0]), for use in error messages."""
        return self.argv[0] if self.argv else self.name

    @property
    def args(self) -> list[str]:
        """Everything after argv[0]."""
        return self.argv[1:]

    # -- output helpers --

    def write(self, data: str) -> None:
        self.stdout.write(data)

    def line(self, data: str = "") -> None:
        self.stdout.write(data + "\n")

    def error(self, data: str) -> None:
        self.stderr.write(data)

    def errline(self, data: str = "") -> None:
        self.stderr.write(data + "\n")

    def fail(self, message: str, code: int = 1) -> int:
        """Write ``prog: message`` to stderr and return an exit code."""
        self.errline(f"{self.prog}: {message}")
        return code

    # -- input helpers --

    async def read_line(self) -> str | None:
        return await self.stdin.readline()

    async def read_all(self) -> str:
        return await self.stdin.read()

    # -- to override --

    async def run(self) -> int:
        raise NotImplementedError

    async def fallback(self) -> int:
        """當命令 raise 了 :class:`DeferToLLM` 但沒有可用的 LLM 後端時所用的
        保守輸出。

        當 interpreter 無法連到模型時，會呼叫此方法取代 miss_handler。預設是靜默
        成功（exit 0、無輸出）——對降級命令而言，保持安靜比發出 ``command not
        found``（該執行檔明明存在）或可能被指紋辨識的假造錯誤更安全。子類可覆寫以
        回傳更合理的內容（例如 awk 像 ``$0`` 那樣整行回顯）。
        """
        return 0
