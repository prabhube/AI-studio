"""
Project Pydantic Schemas.

WHY separate schemas instead of exposing the ORM model directly?
    ORM models contain SQLAlchemy internals and should never leave
    the data layer. Pydantic schemas are pure data contracts that
    are safe to serialize and validated at the API boundary.

    ProjectCreate   → POST /projects  (request body)
    ProjectUpdate   → PATCH /projects/{id}  (request body)
    ProjectResponse → all responses (no internal fields)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Request body for creating a new project."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdate(BaseModel):
    """Partial update for a project. All fields are optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectResponse(BaseModel):
    """Public-facing project representation."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    thumbnail_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime
