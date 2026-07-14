"""
Image Pydantic Schemas.

ImageGenerationRequest  → POST /images/generate
ImageResponse           → all responses
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):
    """Request body to generate a single image."""

    project_id: uuid.UUID
    prompt: str = Field(min_length=5, max_length=2000)
    negative_prompt: str | None = Field(default=None, max_length=2000)
    width: int = Field(default=512, ge=256, le=2048, multiple_of=64)
    height: int = Field(default=512, ge=256, le=2048, multiple_of=64)
    num_inference_steps: int = Field(default=20, ge=1, le=150)
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0)
    seed: int | None = None


class ImageResponse(BaseModel):
    """Public-facing image representation."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    prompt: str
    negative_prompt: str | None
    width: int
    height: int
    num_inference_steps: int
    guidance_scale: float
    seed: int | None
    file_path: str | None
    file_size_bytes: int | None
    status: str
    error_message: str | None
    generation_time_seconds: float | None
    created_at: datetime
    updated_at: datetime
