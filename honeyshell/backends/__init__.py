"""honeyshell.backends — LLM-backed resolution for registry-missed commands.

Implements the HoneyGPT model path (paper §3): a provider-agnostic LLM client
(local Ollama by default), the Question Enhancement prompt (three-sub-question
CoT + Table 1 impact scoring), a hybrid cache router (§3.4), and an
``LLMCommand`` that lets the interpreter treat a model response like any other
built-in command.

Dependency policy: ``httpx`` is imported lazily inside ``client`` only; if it's
absent or the model is down the resolver returns None and the interpreter
degrades to bash's ``command not found``. Multi-turn memory (SR/H) and Memory
Pruning are handled by the separate ``memory`` milestone.
"""

from __future__ import annotations

from honeyshell.backends.cache import CacheEntry, ResponseCache
from honeyshell.backends.client import (
    LLMClient,
    LLMResult,
    LLMUnavailable,
    OllamaClient,
    extract_json,
)
from honeyshell.backends.content_fetcher import (
    ContentFetcher,
    build_content_messages,
)
from honeyshell.backends.fs_applier import (
    ApplyReport,
    apply_fs_ops,
    normalise_fs_ops,
)
from honeyshell.backends.llm_command import (
    LLMCommand,
    make_llm_command_factory,
)
from honeyshell.backends.prompt_builder import (
    TABLE1_RUBRIC,
    PromptBuilder,
    looks_like_command_not_found,
    parse_result,
)
from honeyshell.backends.resolver import ChainResolver, Resolution

__all__ = [
    "LLMClient",
    "LLMResult",
    "LLMUnavailable",
    "OllamaClient",
    "extract_json",
    "PromptBuilder",
    "TABLE1_RUBRIC",
    "parse_result",
    "looks_like_command_not_found",
    "ResponseCache",
    "CacheEntry",
    "ChainResolver",
    "Resolution",
    "ContentFetcher",
    "build_content_messages",
    "LLMCommand",
    "make_llm_command_factory",
    "apply_fs_ops",
    "normalise_fs_ops",
    "ApplyReport",
]
