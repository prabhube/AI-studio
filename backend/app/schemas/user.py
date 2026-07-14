"""
Pydantic schemas for the User domain.

Schema hierarchy:
  UserCreate    → POST /auth/register
  UserUpdate    → PATCH /users/me (profile fields)
  PasswordChange → POST /auth/change-password
  RoleUpdate    → PATCH /users/{id}/role (admin only)
  UserResponse  → all read responses (no hashed_password, no OAuth secrets)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Fields shared across create / response schemas."""
    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="3–50 alphanumeric characters, underscores, or hyphens.",
    )
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    """Request body for email/password registration."""

    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        from app.core.security import validate_password_strength
        errors = validate_password_strength(v)
        if errors:
            raise ValueError(" ".join(errors))
        return v


class UserUpdate(BaseModel):
    """Partial profile update — all fields optional."""
    full_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=2048)


class PasswordChange(BaseModel):
    """Request body for changing a password while logged in."""
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _new_password_strength(cls, v: str) -> str:
        from app.core.security import validate_password_strength
        errors = validate_password_strength(v)
        if errors:
            raise ValueError(" ".join(errors))
        return v


class RoleUpdate(BaseModel):
    """Admin-only: assign a role to a user."""
    role: str = Field(description="One of: user, admin, superuser")

    @field_validator("role")
    @classmethod
    def _valid_role(cls, v: str) -> str:
        from app.models.user import UserRole
        if v not in UserRole.ALL:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(UserRole.ALL)}")
        return v


class UserResponse(BaseModel):
    """Public-facing user representation. Never includes secrets."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    username: str
    full_name: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    is_superuser: bool
    email_verified: bool
    oauth_provider: str | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
