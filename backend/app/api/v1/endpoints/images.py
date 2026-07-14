"""
Images API Endpoints — Placeholders.

Routes:
    POST   /images/generate   → Generate an image via Stable Diffusion
    GET    /images/           → List images in a project
    GET    /images/{id}       → Get image details
    DELETE /images/{id}       → Delete image

All implementations: Phase 4.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.image import ImageGenerationRequest, ImageResponse

router = APIRouter(prefix="/images", tags=["Images"])


@router.post(
    "/generate",
    response_model=SuccessResponse[ImageResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate an image using Stable Diffusion",
)
async def generate_image(
    payload: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[ImageResponse]:
    """Generate image. Returns 202 Accepted. Implementation: Phase 4."""
    raise NotImplementedError("generate_image — Phase 4")


@router.get(
    "/",
    response_model=PaginatedResponse[ImageResponse],
    summary="List images in a project",
)
async def list_images(
    project_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[ImageResponse]:
    """List images. Implementation: Phase 4."""
    raise NotImplementedError("list_images — Phase 4")


@router.get(
    "/{image_id}",
    response_model=SuccessResponse[ImageResponse],
    summary="Get an image by ID",
)
async def get_image(
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[ImageResponse]:
    """Get image. Implementation: Phase 4."""
    raise NotImplementedError("get_image — Phase 4")


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an image",
)
async def delete_image(
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete image. Implementation: Phase 4."""
    raise NotImplementedError("delete_image — Phase 4")
