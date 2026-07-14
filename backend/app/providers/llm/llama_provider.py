"""
Llama LLM Provider — Placeholder.

WHY this file exists:
    Provides the Meta Llama implementation of LLMProvider
    using llama.cpp (via llama-cpp-python) for GGUF model files.

    Structurally identical to GemmaProvider — same interface,
    different model checkpoint. This demonstrates the plug-in
    architecture: swapping models requires zero service changes.

Implementation notes (for Phase 3):
    - Load via llama_cpp.Llama with Llama-specific chat template
    - Llama uses a different prompt format than Gemma (Llama 3 uses
      <|begin_of_text|> etc.) — format is handled internally here,
      the service layer passes plain strings/dicts
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


class LlamaProvider:
    """
    LLMProvider implementation backed by Meta Llama via llama.cpp.

    Satisfies the LLMProvider Protocol structurally.
    """

    def __init__(self, settings) -> None:
        self._settings = settings
        self._model = None
        logger.info("llama_provider_initialized", model_path=settings.model_path)

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """Generate text completion. Implementation: Phase 3."""
        raise NotImplementedError("LlamaProvider.generate() — Phase 3")

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Multi-turn chat completion. Implementation: Phase 3."""
        raise NotImplementedError("LlamaProvider.chat() — Phase 3")

    async def is_available(self) -> bool:
        """Return True when the model file exists and is loaded."""
        return False

    def model_info(self) -> dict[str, str]:
        return {
            "name": "llama",
            "provider": "LlamaProvider",
            "version": "3-8b",
            "backend": "llama.cpp",
            "model_path": self._settings.model_path,
        }
