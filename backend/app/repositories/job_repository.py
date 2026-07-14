"""
GenerationJob Repository — Data access layer for the generation_jobs table.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generation_job import GenerationJob
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[GenerationJob]):
    """Data access for the generation_jobs table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(GenerationJob, session)

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[GenerationJob]:
        """Return jobs for a user, optionally filtered by status."""
        ...

    async def get_by_celery_task_id(self, task_id: str) -> GenerationJob | None:
        """Return the job associated with a Celery task ID."""
        ...

    async def update_progress(
        self, job_id: uuid.UUID, progress_percent: int
    ) -> None:
        """Update the progress percentage of a running job."""
        ...

    async def mark_completed(
        self, job_id: uuid.UUID, result_url: str, duration_seconds: float
    ) -> GenerationJob | None:
        """Mark a job as completed with its result URL."""
        ...

    async def mark_failed(
        self, job_id: uuid.UUID, error_message: str
    ) -> GenerationJob | None:
        """Mark a job as failed with an error message."""
        ...
