"""
Gemma LLM Provider — Placeholder.

WHY this file exists:
    Provides the Gemma-2B/7B implementation of LLMProvider
    using llama.cpp (via llama-cpp-python) for GGUF model files.

    This is a PLACEHOLDER. The interface (method signatures and
    docstrings) is final. The implementation body will be filled
    in during Phase 3 of development.

Implementation notes (for Phase 3):
    - Load model via llama_cpp.Llama(model_path=...)
    - Run in an asyncio.ThreadPoolExecutor to avoid blocking the
      event loop (llama.cpp is synchronous C++ under the hood)
    - Model is loaded once at __init__ time — expensive operation
    - Use settings.llm.temperature and max_tokens as defaults
"""

from app.core.logging import get_logger
from app.providers.base.llm_provider import LLMProvider

logger = get_logger(__name__)


class GemmaProvider:
    """
    LLMProvider implementation backed by Google Gemma via llama.cpp.

    Satisfies the LLMProvider Protocol structurally — no inheritance needed.
    """

    def __init__(self, settings) -> None:
        """
        Initialize the provider with LLMSettings.

        Args:
            settings: LLMSettings instance from core.config.

        Note:
            Model loading is deferred to avoid blocking app startup.
            is_available() returns False until the model is loaded.
        """
        self._settings = settings
        self._model = None  # Loaded lazily or at startup in Phase 3
        logger.info("gemma_provider_initialized", model_path=settings.model_path)

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """Generate text completion. Implementation: Phase 3."""
        raise NotImplementedError("GemmaProvider.generate() — Phase 3")

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Multi-turn chat completion. Implementation: Phase 3."""
        raise NotImplementedError("GemmaProvider.chat() — Phase 3")

    async def is_available(self) -> bool:
        """Return True when the model file exists and is loaded."""
        return False  # Phase 3: check self._model is not None

    def model_info(self) -> dict[str, str]:
        """Return metadata about the loaded Gemma model."""
        return {
            "name": "gemma",
            "provider": "GemmaProvider",
            "version": "2b-it",  # Updated in Phase 3
            "backend": "llama.cpp",
            "model_path": self._settings.model_path,
        }
