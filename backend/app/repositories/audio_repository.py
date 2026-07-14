"""
AudioClip Repository — Data access layer for the audio_clips table.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audio import AudioClip
from app.repositories.base import BaseRepository


class AudioRepository(BaseRepository[AudioClip]):
    """Data access for the audio_clips table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AudioClip, session)

    async def get_by_project_id(
        self, project_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[AudioClip]:
        """Return all audio clips belonging to a project."""
        ...

    async def update_status(
        self, clip_id: uuid.UUID, status: str, error_message: str | None = None
    ) -> AudioClip | None:
        """Update audio clip status."""
        ...
