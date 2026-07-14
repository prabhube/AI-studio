"""
Project Repository — Data access layer for the projects table.

WHY: Encapsulates all SQL queries for Project records.
     Services never write raw SQL — they call repository methods.
     This makes queries testable and replaceable independently.

All methods will be implemented in Phase 2 (domain implementation).
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """
    Data access for the projects table.

    Inherits standard CRUD from BaseRepository.
    Adds project-specific query methods below.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Project, session)

    async def get_by_user_id(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Project]:
        """Return all non-deleted projects belonging to a user."""
        ...

    async def count_by_user_id(self, user_id: uuid.UUID) -> int:
        """Return total project count for a user."""
        ...

    async def get_by_status(
        self, status: str, offset: int = 0, limit: int = 100
    ) -> list[Project]:
        """Return projects filtered by status (draft, generating, etc.)."""
        ...
