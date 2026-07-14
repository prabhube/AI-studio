"""
Audio Service — Business logic for TTS synthesis and STT transcription.

All methods will be implemented in Phase 5.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audio import AudioClip
from app.repositories.audio_repository import AudioRepository
from app.schemas.audio import TTSRequest


class AudioService:
    """Orchestrates TTS generation and STT transcription requests."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = AudioRepository(session)

    async def request_tts(
        self, user_id: uuid.UUID, payload: TTSRequest
    ) -> AudioClip:
        """Create an AudioClip record and dispatch a TTS Celery task."""
        ...

    async def get_by_id(self, clip_id: uuid.UUID, user_id: uuid.UUID) -> AudioClip:
        """Return an audio clip, validating user ownership."""
        ...

    async def list_for_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[AudioClip], int]:
        """Return paginated audio clips for a project."""
        ...

    async def delete(self, clip_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Soft-delete a clip and remove the file from disk."""
        ...

    async def list_voices(self) -> list[str]:
        """Return all available TTS voice IDs from the configured provider."""
        ...
