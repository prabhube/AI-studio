"""
LLM Provider Factory.

WHY this file exists:
    The factory reads the LLM_PROVIDER environment variable and returns
    the correct concrete provider. Callers never construct providers manually.

    This is the only place in the entire codebase that knows which
    LLM provider is in use. Everything else is abstracted behind LLMProvider.

Pattern used: Factory Method
    get_llm_provider() reads config and returns the correct implementation.
    The return type is always LLMProvider — the concrete type is hidden.

Usage:
    provider = await get_llm_provider()
    result = await provider.generate("Write a video script about...")

Adding a new provider:
    1. Create NewProvider in providers/llm/new_provider.py
    2. Add a new elif branch in get_llm_provider()
    3. Add the new option to LLMSettings in core/config.py
    Zero other changes required.
"""

from functools import lru_cache

from app.core.config import get_settings
from app.core.exceptions import ProviderNotConfiguredError
from app.core.logging import get_logger
from app.providers.base.llm_provider import LLMProvider

logger = get_logger(__name__)

_provider_instance: LLMProvider | None = None


async def get_llm_provider() -> LLMProvider:
    """
    Return the singleton LLM provider configured in settings.

    Raises:
        ProviderNotConfiguredError: If LLM_PROVIDER is "none" or unknown.
    """
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    settings = get_settings()
    provider_name = settings.llm.provider

    if provider_name == "gemma":
        from app.providers.llm.gemma_provider import GemmaProvider
        _provider_instance = GemmaProvider(settings.llm)

    elif provider_name == "llama":
        from app.providers.llm.llama_provider import LlamaProvider
        _provider_instance = LlamaProvider(settings.llm)

    elif provider_name == "none":
        raise ProviderNotConfiguredError("llm")

    else:
        raise ProviderNotConfiguredError(f"llm:{provider_name}")

    logger.info("llm_provider_initialized", provider=provider_name)
    return _provider_instance


def reset_llm_provider() -> None:
    """
    Reset the singleton for testing purposes.

    WHY: Tests need to inject different providers without
         restarting the process.
    """
    global _provider_instance
    _provider_instance = None
