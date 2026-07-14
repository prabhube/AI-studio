"""
Video Pydantic Schemas.

VideoGenerationRequest  → POST /videos/generate
VideoResponse           → all responses
VideoStatusResponse     → polling endpoint for generation status
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class VideoGenerationRequest(BaseModel):
    """Request body to initiate AI video generation."""

    project_id: uuid.UUID
    prompt: str = Field(min_length=10, max_length=4000)
    negative_prompt: str | None = Field(default=None, max_length=2000)
    num_frames: int = Field(default=5, ge=1, le=30)
    frame_duration_seconds: float = Field(default=3.0, ge=0.5, le=10.0)
    transition: str = Field(default="fade")
    include_narration: bool = True
    voice_id: str | None = None
    fps: int = Field(default=30, ge=15, le=60)
    width: int = Field(default=1920)
    height: int = Field(default=1080)


class VideoResponse(BaseModel):
    """Public-facing video representation."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    prompt: str
    file_path: str | None
    thumbnail_path: str | None
    duration_seconds: float | None
    width: int | None
    height: int | None
    fps: int | None
    file_size_bytes: int | None
    status: str
    error_message: str | None
    celery_task_id: str | None
    generation_time_seconds: float | None
    created_at: datetime
    updated_at: datetime


class VideoStatusResponse(BaseModel):
    """Lightweight status-only response for polling."""

    id: uuid.UUID
    status: str
    progress_percent: int | None = None
    error_message: str | None = None
