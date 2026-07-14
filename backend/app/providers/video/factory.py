"""Video Provider Factory. Reads VIDEO_PROVIDER from settings."""

from app.core.config import get_settings
from app.core.exceptions import ProviderNotConfiguredError
from app.core.logging import get_logger
from app.providers.base.video_provider import VideoProvider

logger = get_logger(__name__)

_provider_instance: VideoProvider | None = None


async def get_video_provider() -> VideoProvider:
    """Return the singleton video provider."""
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    settings = get_settings()
    provider_name = settings.video.provider

    if provider_name == "ffmpeg":
        from app.providers.video.ffmpeg_provider import FFmpegProvider
        _provider_instance = FFmpegProvider(settings.video)

    elif provider_name == "none":
        raise ProviderNotConfiguredError("video")

    else:
        raise ProviderNotConfiguredError(f"video:{provider_name}")

    logger.info("video_provider_initialized", provider=provider_name)
    return _provider_instance


def reset_video_provider() -> None:
    global _provider_instance
    _provider_instance = None
