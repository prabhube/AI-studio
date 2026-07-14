"""
Image Provider Protocol.

WHY this file exists:
    Defines the contract for all image generation backends.
    Stable Diffusion today; future models (DALL-E local, FLUX, etc.) tomorrow.
    The ImageService only ever sees this interface.

Protocol methods:
    generate()        → Text-to-image generation
    upscale()         → Increase resolution of an existing image
    is_available()    → Model readiness check
    model_info()      → Provider metadata
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ImageGenerationRequest:
    """
    Immutable value object for an image generation request.

    WHY a dataclass instead of plain dict?
        Type-safe. Validated at construction. Immutable (frozen=True)
        prevents accidental mutation across async boundaries.
    """

    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    num_inference_steps: int = 20
    guidance_scale: float = 7.5
    seed: int | None = None


@dataclass(frozen=True)
class ImageGenerationResult:
    """Result returned by any image provider."""

    file_path: Path
    width: int
    height: int
    seed: int
    prompt: str
    generation_time_seconds: float


@runtime_checkable
class ImageProvider(Protocol):
    """Structural protocol for all image generation providers."""

    async def generate(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResult:
        """
        Generate an image from a text prompt.

        Args:
            request: Immutable generation parameters.

        Returns:
            ImageGenerationResult with the path to the saved image.
        """
        ...

    async def upscale(
        self, image_path: Path, scale_factor: int = 2
    ) -> Path:
        """
        Upscale an existing image by the given factor.

        Args:
            image_path:   Path to the source image.
            scale_factor: Target multiplier (e.g. 2 = 2x resolution).

        Returns:
            Path to the upscaled image.
        """
        ...

    async def is_available(self) -> bool:
        """Return True if the model is loaded and ready."""
        ...

    def model_info(self) -> dict[str, str]:
        """Return provider metadata."""
        ...
