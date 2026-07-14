"""
Video Service — Business logic for end-to-end video generation.

WHY this file exists:
    The most complex service. Orchestrates the full pipeline:
      1. Validate user owns the project
      2. Create a Video record (status=pending)
      3. Dispatch a high-level Celery pipeline task
      4. The pipeline task internally calls:
           - LLMService → generate script + image prompts
           - ImageService × N → generate each frame
           - AudioService → synthesize narration
           - VideoProvider.assemble() → combine all assets
      5. Update the Video record with the completed file path

All methods will be implemented in Phase 8 (end-to-end pipeline).
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.repositories.video_repository import VideoRepository
from app.schemas.video import VideoGenerationRequest


class VideoService:
    """Orchestrates end-to-end AI video generation."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = VideoRepository(session)

    async def request_generation(
        self, user_id: uuid.UUID, payload: VideoGenerationRequest
    ) -> Video:
        """
        Initiate the full video generation pipeline asynchronously.

        Returns a Video with status='pending' immediately.
        The Celery pipeline handles the rest in the background.
        """
        ...

    async def get_by_id(self, video_id: uuid.UUID, user_id: uuid.UUID) -> Video:
        """Return a video, validating user ownership."""
        ...

    async def get_status(self, video_id: uuid.UUID, user_id: uuid.UUID) -> Video:
        """Return just the status of a video (lightweight polling endpoint)."""
        ...

    async def list_for_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[Video], int]:
        """Return paginated videos for a project."""
        ...

    async def delete(self, video_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Soft-delete a video and remove media files from disk."""
        ...
