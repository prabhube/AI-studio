"""
Videos API Endpoints — Placeholders.

Routes:
    POST   /videos/generate       → Initiate video generation pipeline
    GET    /videos/               → List videos in a project
    GET    /videos/{id}           → Get video details
    GET    /videos/{id}/status    → Poll generation status (lightweight)
    DELETE /videos/{id}           → Delete video

All implementations: Phase 8.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.video import (
    VideoGenerationRequest,
    VideoResponse,
    VideoStatusResponse,
)

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post(
    "/generate",
    response_model=SuccessResponse[VideoResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Initiate AI video generation",
)
async def generate_video(
    payload: VideoGenerationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[VideoResponse]:
    """Start video pipeline. Returns 202 Accepted. Implementation: Phase 8."""
    raise NotImplementedError("generate_video — Phase 8")


@router.get(
    "/",
    response_model=PaginatedResponse[VideoResponse],
    summary="List videos in a project",
)
async def list_videos(
    project_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[VideoResponse]:
    """List videos. Implementation: Phase 8."""
    raise NotImplementedError("list_videos — Phase 8")


@router.get(
    "/{video_id}",
    response_model=SuccessResponse[VideoResponse],
    summary="Get a video by ID",
)
async def get_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[VideoResponse]:
    """Get video. Implementation: Phase 8."""
    raise NotImplementedError("get_video — Phase 8")


@router.get(
    "/{video_id}/status",
    response_model=SuccessResponse[VideoStatusResponse],
    summary="Poll video generation status",
)
async def get_video_status(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[VideoStatusResponse]:
    """Lightweight status poll. Implementation: Phase 8."""
    raise NotImplementedError("get_video_status — Phase 8")


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a video",
)
async def delete_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete video. Implementation: Phase 8."""
    raise NotImplementedError("delete_video — Phase 8")
