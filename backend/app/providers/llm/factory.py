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

import asyncio

from app.core.config import get_settings
from app.core.exceptions import ProviderNotConfiguredError
from app.core.logging import get_logger
from app.providers.base.llm_provider import LLMProvider

logger = get_logger(__name__)

# Module-level singleton — the provider (and its loaded model) is expensive,
# so we build it once per process.
_provider_instance: LLMProvider | None = None
# Serialises concurrent first-time initialisation so we never build two
# providers (and two model handles) in a race.
_init_lock = asyncio.Lock()


async def get_llm_provider() -> LLMProvider:
    """
    Return the singleton LLM provider configured in settings.

    The concrete implementation is selected purely from ``settings.llm.provider``
    (the ``LLM_PROVIDER`` env var). Business logic depends only on the
    ``LLMProvider`` protocol, so switching providers never touches services.

    Raises:
        ProviderNotConfiguredError: If LLM_PROVIDER is "none" or unknown.
    """
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    async with _init_lock:
        # Another coroutine may have initialised while we awaited the lock.
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

        logger.info("llm_provider_selected", provider=provider_name)
        return _provider_instance


def reset_llm_provider() -> None:
    """
    Reset the singleton, releasing any loaded model and inference threads.

    WHY: Tests need to inject different providers without restarting the
         process. Providers may hold a thread pool and a multi-GB model
         handle, so we close them before dropping the reference.
    """
    global _provider_instance

    close = getattr(_provider_instance, "close", None)
    if callable(close):
        close()

    _provider_instance = None
