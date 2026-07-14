"""
Image Service — Business logic for image generation.

WHY this file exists:
    Bridges the API layer and the AI image provider.
    Responsibilities:
      1. Validate the user owns the target project
      2. Create an Image record in the DB (status=pending)
      3. Dispatch a Celery task for background generation
      4. Return the pending Image record to the API layer

    The actual Stable Diffusion inference happens in tasks/image_tasks.py,
    not here. This keeps the API response fast (< 100ms).

All methods will be implemented in Phase 4.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.repositories.image_repository import ImageRepository
from app.schemas.image import ImageGenerationRequest


class ImageService:
    """Orchestrates image generation requests."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ImageRepository(session)

    async def request_generation(
        self, user_id: uuid.UUID, payload: ImageGenerationRequest
    ) -> Image:
        """
        Create an Image record and dispatch a background generation task.

        Returns the Image with status='pending' immediately.
        The actual generation happens asynchronously in Celery.
        """
        ...

    async def get_by_id(self, image_id: uuid.UUID, user_id: uuid.UUID) -> Image:
        """Return an image, validating user ownership via the project."""
        ...

    async def list_for_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[Image], int]:
        """Return paginated images for a project."""
        ...

    async def delete(self, image_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Soft-delete an image and remove the file from disk."""
        ...
