"""
Shared llama.cpp LLM provider base.

WHY this file exists:
    Gemma and Llama both run as GGUF models through llama.cpp
    (llama-cpp-python). The loading, threading, and inference plumbing is
    identical for both — only the model metadata and chat template differ.

    Centralising that plumbing here means:
      - GemmaProvider / LlamaProvider are a few lines each (just the model's
        identity + chat format), which is what makes them interchangeable.
      - A future GGUF model (Mistral, Phi, Qwen, ...) is a 3-line subclass.
      - The tricky bits (event-loop safety, lazy loading, error mapping) are
        written and tested once.

Concurrency model:
    llama.cpp is synchronous C++ and a single model handle is NOT safe for
    concurrent calls. Every inference call is dispatched to a dedicated
    single-worker ThreadPoolExecutor, which:
      - keeps the asyncio event loop unblocked, and
      - serialises access to the one model handle.

Loading:
    The model is loaded lazily on first use (guarded by an asyncio.Lock) so
    importing the provider — and starting the app — never blocks on reading a
    multi-gigabyte weight file. `is_available()` reports readiness cheaply
    without triggering a load.
"""

from __future__ import annotations

import asyncio
import functools
import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover - imports only for type checking
    from app.core.config import LLMSettings
    from llama_cpp import Llama

logger = get_logger(__name__)

#: Roles accepted in a chat message, matching the OpenAI-style convention
#: that llama.cpp's chat templates expect.
_VALID_ROLES = frozenset({"system", "user", "assistant"})


class LlamaCppProvider:
    """
    Base implementation of the ``LLMProvider`` protocol for GGUF models.

    Concrete providers customise only three class attributes:
        model_name    — short identifier reported by ``model_info()``
        model_version — human-readable checkpoint version
        chat_format   — llama-cpp-python chat template name, or ``None`` to
                        use the template embedded in the GGUF file.

    The class satisfies ``LLMProvider`` structurally; no explicit inheritance
    from the Protocol is required.
    """

    #: Overridden by concrete subclasses.
    model_name: str = "llama.cpp"
    model_version: str = "unknown"
    #: llama-cpp-python ``chat_format``; ``None`` → use the GGUF's own template.
    chat_format: str | None = None

    def __init__(self, settings: LLMSettings) -> None:
        """
        Initialise the provider.

        Args:
            settings: The ``LLMSettings`` sub-config from ``core.config``.

        Note:
            Model loading is deferred until the first inference call so the
            application can start without blocking on a large weight file.
        """
        self._settings = settings
        self._model: Llama | None = None
        # max_workers=1 → serialises inference on a single model handle while
        # keeping the event loop free.
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix=f"{self.model_name}-llm",
        )
        self._load_lock = asyncio.Lock()
        logger.info(
            "llm_provider_initialized",
            provider=type(self).__name__,
            model=self.model_name,
            model_path=settings.model_path,
            chat_format=self.chat_format,
        )

    # ------------------------------------------------------------------
    # Protocol methods
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """
        Generate a single-turn text completion.

        Args:
            prompt:         The input prompt text.
            max_tokens:     Maximum number of tokens to generate.
            temperature:    Sampling temperature (0.0 = deterministic).
            stop_sequences: Strings that halt generation when produced.

        Returns:
            The generated completion text (leading/trailing whitespace stripped).

        Raises:
            LLMProviderError: If the model cannot be loaded or inference fails.
        """
        if not prompt or not prompt.strip():
            raise LLMProviderError(
                message="Prompt must be a non-empty string.",
                detail={"provider": self.model_name},
            )

        model = await self._ensure_loaded()
        call = functools.partial(
            self._run_completion,
            model,
            prompt,
            max_tokens,
            temperature,
            stop_sequences,
        )
        return await self._run_in_executor(call, operation="generate")

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Multi-turn chat completion.

        The model's chat template (Gemma vs Llama differ) is applied internally
        by llama.cpp, so callers always pass a plain list of role/content dicts.

        Args:
            messages:    ``[{"role": "user"|"assistant"|"system", "content": str}]``
            max_tokens:  Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            The assistant's reply as plain text.

        Raises:
            LLMProviderError: If ``messages`` is invalid, the model cannot be
                loaded, or inference fails.
        """
        self._validate_messages(messages)

        model = await self._ensure_loaded()
        call = functools.partial(
            self._run_chat,
            model,
            messages,
            max_tokens,
            temperature,
        )
        return await self._run_in_executor(call, operation="chat")

    async def is_available(self) -> bool:
        """
        Return True if the provider can serve inference.

        Cheap, non-blocking check: reports ready if the model is already
        loaded, or if the weight file exists and llama-cpp-python is installed.
        Does not trigger a (potentially multi-second) model load.
        """
        if self._model is not None:
            return True
        if not os.path.exists(self._settings.model_path):
            return False
        return importlib.util.find_spec("llama_cpp") is not None

    def model_info(self) -> dict[str, str]:
        """Return metadata about the configured model."""
        return {
            "name": self.model_name,
            "provider": type(self).__name__,
            "version": self.model_version,
            "backend": "llama.cpp",
            "model_path": self._settings.model_path,
            "loaded": str(self._model is not None),
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """
        Release the model handle and shut down the inference thread pool.

        Called by the factory's ``reset_llm_provider()`` so providers can be
        swapped (e.g. in tests) without leaking threads.
        """
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._model = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_loaded(self) -> Llama:
        """Load the model on first use; return the cached handle thereafter."""
        if self._model is not None:
            return self._model

        async with self._load_lock:
            # Double-checked locking: another coroutine may have loaded it
            # while we awaited the lock.
            if self._model is not None:
                return self._model

            loop = asyncio.get_running_loop()
            self._model = await loop.run_in_executor(self._executor, self._load_model)
            logger.info(
                "llm_model_loaded",
                provider=type(self).__name__,
                model=self.model_name,
            )
            return self._model

    def _load_model(self) -> Llama:
        """
        Load the GGUF model. Runs inside the executor thread.

        Raises:
            LLMProviderError: If the weight file is missing, llama-cpp-python
                is not installed, or the model fails to load.
        """
        model_path = self._settings.model_path
        if not os.path.exists(model_path):
            raise LLMProviderError(
                message=(
                    f"{self.model_name} model file not found at '{model_path}'. "
                    "Set LLM_MODEL_PATH to a valid .gguf file."
                ),
                detail={"provider": self.model_name, "model_path": model_path},
            )

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise LLMProviderError(
                message=(
                    "llama-cpp-python is not installed. "
                    "Install it with: pip install llama-cpp-python"
                ),
                detail={"provider": self.model_name},
            ) from exc

        try:
            return Llama(
                model_path=model_path,
                n_ctx=self._settings.context_length,
                n_threads=self._settings.n_threads,
                chat_format=self.chat_format,
                verbose=False,
            )
        except Exception as exc:
            logger.error(
                "llm_model_load_failed",
                provider=type(self).__name__,
                model_path=model_path,
                error=str(exc),
                exc_info=True,
            )
            raise LLMProviderError(
                message=f"Failed to load {self.model_name} model: {exc}",
                detail={"provider": self.model_name, "model_path": model_path},
            ) from exc

    async def _run_in_executor(
        self, call: functools.partial[str], *, operation: str
    ) -> str:
        """Run a blocking inference callable in the executor, mapping errors."""
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(self._executor, call)
        except LLMProviderError:
            raise
        except Exception as exc:
            logger.error(
                "llm_inference_failed",
                provider=type(self).__name__,
                operation=operation,
                error=str(exc),
                exc_info=True,
            )
            raise LLMProviderError(
                message=f"{self.model_name} {operation} failed: {exc}",
                detail={"provider": self.model_name, "operation": operation},
            ) from exc

    @staticmethod
    def _run_completion(
        model: Llama,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop_sequences: list[str] | None,
    ) -> str:
        """Blocking text completion. Runs inside the executor thread."""
        result = model.create_completion(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop_sequences or None,
            stream=False,
        )
        return str(result["choices"][0]["text"]).strip()

    @staticmethod
    def _run_chat(
        model: Llama,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Blocking chat completion. Runs inside the executor thread."""
        result = model.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
        content = result["choices"][0]["message"].get("content") or ""
        return str(content).strip()

    def _validate_messages(self, messages: list[dict[str, str]]) -> None:
        """Validate chat messages before dispatching to the model."""
        if not messages:
            raise LLMProviderError(
                message="chat() requires at least one message.",
                detail={"provider": self.model_name},
            )
        for index, message in enumerate(messages):
            role = message.get("role")
            content = message.get("content")
            if role not in _VALID_ROLES:
                raise LLMProviderError(
                    message=(
                        f"Invalid message role '{role}' at index {index}. "
                        f"Expected one of: {', '.join(sorted(_VALID_ROLES))}."
                    ),
                    detail={"provider": self.model_name, "index": index},
                )
            if not isinstance(content, str) or not content.strip():
                raise LLMProviderError(
                    message=f"Message at index {index} has empty content.",
                    detail={"provider": self.model_name, "index": index},
                )
