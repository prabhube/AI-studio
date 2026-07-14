"""
Video Repository — Data access layer for the videos table.

All methods will be implemented during the video generation phase.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.repositories.base import BaseRepository


class VideoRepository(BaseRepository[Video]):
    """Data access for the videos table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Video, session)

    async def get_by_project_id(
        self, project_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Video]:
        """Return all videos belonging to a project."""
        ...

    async def get_by_celery_task_id(self, task_id: str) -> Video | None:
        """Return the video associated with a Celery task ID."""
        ...

    async def update_status(
        self, video_id: uuid.UUID, status: str, error_message: str | None = None
    ) -> Video | None:
        """Update video status and optional error message."""
        ...
