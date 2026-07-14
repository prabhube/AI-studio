"""
Audio Pydantic Schemas.

TTSRequest    → POST /audio/synthesize
AudioResponse → all responses
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    """Request body to synthesize speech from text."""

    project_id: uuid.UUID
    text: str = Field(min_length=1, max_length=10000)
    voice_id: str = Field(default="en_US-lessac-medium")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    output_format: str = Field(default="wav", pattern="^(wav|mp3|ogg)$")


class AudioResponse(BaseModel):
    """Public-facing audio clip representation."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    text: str | None
    voice_id: str | None
    output_format: str
    file_path: str | None
    file_size_bytes: int | None
    duration_seconds: float | None
    clip_type: str
    status: str
    error_message: str | None
    generation_time_seconds: float | None
    created_at: datetime
    updated_at: datetime
