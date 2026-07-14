"""
Stable Diffusion Image Provider — Placeholder.

WHY this file exists:
    Provides Stable Diffusion v1.5/XL implementation of ImageProvider.
    Will use diffusers (HuggingFace) or InvokeAI CLI under the hood.

Implementation notes (for Phase 4):
    - Load pipeline via diffusers.StableDiffusionPipeline
    - Run in asyncio.ThreadPoolExecutor (diffusers is synchronous)
    - Save output to settings.image.output_dir / UUID.png
    - Support negative prompts, seed for reproducibility
    - VRAM management: load model once, keep in memory
"""

from pathlib import Path

from app.core.logging import get_logger
from app.providers.base.image_provider import (
    ImageGenerationRequest,
    ImageGenerationResult,
)

logger = get_logger(__name__)


class StableDiffusionProvider:
    """
    ImageProvider implementation backed by Stable Diffusion.

    Satisfies the ImageProvider Protocol structurally.
    """

    def __init__(self, settings) -> None:
        self._settings = settings
        self._pipeline = None  # Loaded in Phase 4
        logger.info("sd_provider_initialized", model_path=settings.model_path)

    async def generate(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResult:
        """Generate image from prompt. Implementation: Phase 4."""
        raise NotImplementedError("StableDiffusionProvider.generate() — Phase 4")

    async def upscale(self, image_path: Path, scale_factor: int = 2) -> Path:
        """Upscale image. Implementation: Phase 4."""
        raise NotImplementedError("StableDiffusionProvider.upscale() — Phase 4")

    async def is_available(self) -> bool:
        return False  # Phase 4: check self._pipeline is not None

    def model_info(self) -> dict[str, str]:
        return {
            "name": "stable_diffusion",
            "provider": "StableDiffusionProvider",
            "version": "1.5",
            "backend": "diffusers",
            "model_path": self._settings.model_path,
        }
