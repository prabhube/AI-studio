"""
Audio API Endpoints — Placeholders.

Routes:
    POST   /audio/synthesize   → Synthesize speech via Piper TTS
    GET    /audio/voices       → List available voice IDs
    GET    /audio/             → List audio clips in a project
    GET    /audio/{id}         → Get audio clip details
    DELETE /audio/{id}         → Delete audio clip

All implementations: Phase 5.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.audio import AudioResponse, TTSRequest
from app.schemas.common import PaginatedResponse, SuccessResponse

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.post(
    "/synthesize",
    response_model=SuccessResponse[AudioResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Synthesize speech from text using Piper TTS",
)
async def synthesize_speech(
    payload: TTSRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[AudioResponse]:
    """Synthesize TTS. Implementation: Phase 5."""
    raise NotImplementedError("synthesize_speech — Phase 5")


@router.get(
    "/voices",
    response_model=SuccessResponse[list[str]],
    summary="List available TTS voice IDs",
)
async def list_voices(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[str]]:
    """List voices. Implementation: Phase 5."""
    raise NotImplementedError("list_voices — Phase 5")


@router.get(
    "/",
    response_model=PaginatedResponse[AudioResponse],
    summary="List audio clips in a project",
)
async def list_audio(
    project_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[AudioResponse]:
    """List audio clips. Implementation: Phase 5."""
    raise NotImplementedError("list_audio — Phase 5")


@router.get(
    "/{clip_id}",
    response_model=SuccessResponse[AudioResponse],
    summary="Get an audio clip by ID",
)
async def get_audio(
    clip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[AudioResponse]:
    """Get audio clip. Implementation: Phase 5."""
    raise NotImplementedError("get_audio — Phase 5")


@router.delete(
    "/{clip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an audio clip",
)
async def delete_audio(
    clip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete audio clip. Implementation: Phase 5."""
    raise NotImplementedError("delete_audio — Phase 5")
