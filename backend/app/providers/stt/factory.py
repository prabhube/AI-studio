"""STT Provider Factory. Reads STT_PROVIDER from settings."""

from app.core.config import get_settings
from app.core.exceptions import ProviderNotConfiguredError
from app.core.logging import get_logger
from app.providers.base.stt_provider import STTProvider

logger = get_logger(__name__)

_provider_instance: STTProvider | None = None


async def get_stt_provider() -> STTProvider:
    """Return the singleton STT provider."""
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    settings = get_settings()
    provider_name = settings.stt.provider

    if provider_name == "whisper":
        from app.providers.stt.whisper_provider import WhisperProvider
        _provider_instance = WhisperProvider(settings.stt)

    elif provider_name == "none":
        raise ProviderNotConfiguredError("stt")

    else:
        raise ProviderNotConfiguredError(f"stt:{provider_name}")

    logger.info("stt_provider_initialized", provider=provider_name)
    return _provider_instance


def reset_stt_provider() -> None:
    global _provider_instance
    _provider_instance = None
