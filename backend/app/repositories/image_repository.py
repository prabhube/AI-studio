"""
Image Repository — Data access layer for the images table.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.repositories.base import BaseRepository


class ImageRepository(BaseRepository[Image]):
    """Data access for the images table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Image, session)

    async def get_by_project_id(
        self, project_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Image]:
        """Return all images belonging to a project, ordered by sequence."""
        ...

    async def get_by_video_id(self, video_id: uuid.UUID) -> list[Image]:
        """Return all images associated with a specific video, ordered by sequence."""
        ...

    async def update_status(
        self, image_id: uuid.UUID, status: str, error_message: str | None = None
    ) -> Image | None:
        """Update image status and optional error message."""
        ...
