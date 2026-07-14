"""
User repository — data access layer for the users table.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Encapsulates all database operations for the User model."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by email address (case-insensitive), or None."""
        result = await self._session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        """Return a user by username, or None."""
        result = await self._session.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().first()

    async def get_by_oauth(
        self, provider: str, provider_id: str
    ) -> User | None:
        """Return a user by their OAuth provider + provider-specific ID."""
        result = await self._session.execute(
            select(User).where(
                and_(
                    User.oauth_provider == provider,
                    User.oauth_provider_id == provider_id,
                )
            )
        )
        return result.scalars().first()

    async def get_by_role(
        self, role: str, offset: int = 0, limit: int = 100
    ) -> list[User]:
        """Return active users with a specific role."""
        result = await self._session.execute(
            select(User)
            .where(User.role == role, User.is_active.is_(True))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Existence checks
    # ------------------------------------------------------------------

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None

    async def username_exists(self, username: str) -> bool:
        return await self.get_by_username(username) is not None

    # ------------------------------------------------------------------
    # State mutations
    # ------------------------------------------------------------------

    async def set_last_login(self, user_id: uuid.UUID) -> None:
        """Record the current UTC timestamp as the user's last login."""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(UTC))
        )

    async def set_email_verified(self, user_id: uuid.UUID) -> None:
        """Mark the user's email as verified."""
        await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(email_verified=True)
        )

    async def deactivate(self, user_id: uuid.UUID) -> User | None:
        """Set is_active=False without deleting the user."""
        return await self.update_by_id(user_id, is_active=False)

    async def set_role(self, user_id: uuid.UUID, role: str) -> User | None:
        """Assign a new role to a user and update is_superuser accordingly."""
        from app.models.user import UserRole
        is_superuser = role == UserRole.SUPERUSER
        return await self.update_by_id(
            user_id, role=role, is_superuser=is_superuser
        )

    # ------------------------------------------------------------------
    # Active users list
    # ------------------------------------------------------------------

    async def get_active_users(
        self, offset: int = 0, limit: int = 100
    ) -> list[User]:
        """Return only active, non-soft-deleted users."""
        result = await self._session.execute(
            select(User)
            .where(User.is_active.is_(True), User.deleted_at.is_(None))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
