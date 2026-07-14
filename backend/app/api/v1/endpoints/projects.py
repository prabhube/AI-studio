"""
Projects API Endpoints — Placeholders.

WHY these endpoints exist:
    Projects are the top-level organizational unit. Every video,
    image, and audio clip belongs to a project.

Routes:
    POST   /projects/         → Create project
    GET    /projects/         → List user's projects (paginated)
    GET    /projects/{id}     → Get project by ID
    PATCH  /projects/{id}     → Update project metadata
    DELETE /projects/{id}     → Soft-delete project

All implementations: Phase 2.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "/",
    response_model=SuccessResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[ProjectResponse]:
    """Create a project. Implementation: Phase 2."""
    raise NotImplementedError("create_project — Phase 2")


@router.get(
    "/",
    response_model=PaginatedResponse[ProjectResponse],
    summary="List the current user's projects",
)
async def list_projects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[ProjectResponse]:
    """List projects. Implementation: Phase 2."""
    raise NotImplementedError("list_projects — Phase 2")


@router.get(
    "/{project_id}",
    response_model=SuccessResponse[ProjectResponse],
    summary="Get a project by ID",
)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[ProjectResponse]:
    """Get project. Implementation: Phase 2."""
    raise NotImplementedError("get_project — Phase 2")


@router.patch(
    "/{project_id}",
    response_model=SuccessResponse[ProjectResponse],
    summary="Update a project",
)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[ProjectResponse]:
    """Update project. Implementation: Phase 2."""
    raise NotImplementedError("update_project — Phase 2")


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete project. Implementation: Phase 2."""
    raise NotImplementedError("delete_project — Phase 2")
