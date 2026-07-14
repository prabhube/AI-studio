"""
TTS Provider Factory.

Reads TTS_PROVIDER from settings and returns the correct backend.
"""

from app.core.config import get_settings
from app.core.exceptions import ProviderNotConfiguredError
from app.core.logging import get_logger
from app.providers.base.tts_provider import TTSProvider

logger = get_logger(__name__)

_provider_instance: TTSProvider | None = None


async def get_tts_provider() -> TTSProvider:
    """Return the singleton TTS provider. Raises ProviderNotConfiguredError if none."""
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    settings = get_settings()
    provider_name = settings.tts.provider

    if provider_name == "piper":
        from app.providers.tts.piper_provider import PiperProvider
        _provider_instance = PiperProvider(settings.tts)

    elif provider_name == "none":
        raise ProviderNotConfiguredError("tts")

    else:
        raise ProviderNotConfiguredError(f"tts:{provider_name}")

    logger.info("tts_provider_initialized", provider=provider_name)
    return _provider_instance


def reset_tts_provider() -> None:
    """Reset singleton for testing."""
    global _provider_instance
    _provider_instance = None
