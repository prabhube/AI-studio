"""
GenerationJob Pydantic Schemas.

GenerationJobResponse → all responses (used for polling job status)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class GenerationJobResponse(BaseModel):
    """Public-facing generation job representation."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID | None
    job_type: str
    status: str
    progress_percent: int
    celery_task_id: str | None
    result_url: str | None
    error_message: str | None
    duration_seconds: float | None
    created_at: datetime
    updated_at: datetime
