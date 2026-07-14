"""
Image Provider Factory.

WHY this file exists:
    Single point of construction for image generation providers.
    Reads IMAGE_PROVIDER from settings and returns the correct backend.

Usage:
    provider = await get_image_provider()
    result = await provider.generate(ImageGenerationRequest(...))
"""

from app.core.config import get_settings
from app.core.exceptions import ProviderNotConfiguredError
from app.core.logging import get_logger
from app.providers.base.image_provider import ImageProvider

logger = get_logger(__name__)

_provider_instance: ImageProvider | None = None


async def get_image_provider() -> ImageProvider:
    """
    Return the singleton image provider configured in settings.

    Raises:
        ProviderNotConfiguredError: If IMAGE_PROVIDER is "none" or unknown.
    """
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    settings = get_settings()
    provider_name = settings.image.provider

    if provider_name == "stable_diffusion":
        from app.providers.image.stable_diffusion_provider import StableDiffusionProvider
        _provider_instance = StableDiffusionProvider(settings.image)

    elif provider_name == "none":
        raise ProviderNotConfiguredError("image")

    else:
        raise ProviderNotConfiguredError(f"image:{provider_name}")

    logger.info("image_provider_initialized", provider=provider_name)
    return _provider_instance


def reset_image_provider() -> None:
    """Reset singleton for testing."""
    global _provider_instance
    _provider_instance = None
