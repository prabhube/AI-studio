"""
Project Service — Business logic layer for project management.

WHY this file exists:
    Orchestrates project lifecycle: creation, listing, updating, deletion.
    Acts as the single source of truth for project-related business rules.

    What belongs here (not in the repository):
      - Authorization checks (does this user own this project?)
      - Status transitions (can a "generating" project be deleted?)
      - Cascading operations (delete project → cancel running jobs)

All methods will be implemented in Phase 2.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """
    Orchestrates project-related business operations.

    Injected with an AsyncSession per request by FastAPI dependencies.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ProjectRepository(session)

    async def create(self, user_id: uuid.UUID, payload: ProjectCreate) -> Project:
        """Create a new project owned by the given user."""
        ...

    async def get_by_id(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
        """Return a project, raising errors if not found or not owned by user."""
        ...

    async def list_for_user(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[Project], int]:
        """Return paginated projects for a user with total count."""
        ...

    async def update(
        self, project_id: uuid.UUID, user_id: uuid.UUID, payload: ProjectUpdate
    ) -> Project:
        """Update project metadata. Validates ownership."""
        ...

    async def delete(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Soft-delete a project and cancel any active generation jobs."""
        ...
