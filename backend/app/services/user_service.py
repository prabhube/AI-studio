"""
User service — business logic for user management.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationError,
    InvalidInputError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from app.core.logging import get_logger
from app.core.security import hash_password, validate_password_strength, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserService:
    """Orchestrates all user-related business operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self, payload: UserCreate) -> User:
        """
        Create a new email/password user account.

        Raises:
            ResourceAlreadyExistsError: Email or username already taken.
        """
        email = payload.email.lower()

        if await self._repo.email_exists(email):
            raise ResourceAlreadyExistsError("User", email)

        if await self._repo.username_exists(payload.username):
            raise ResourceAlreadyExistsError("User", payload.username)

        user = await self._repo.create(
            email=email,
            username=payload.username,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=UserRole.USER,
            is_active=True,
            is_superuser=False,
            email_verified=False,
            oauth_provider=None,
            oauth_provider_id=None,
        )

        logger.info("user_registered", user_id=str(user.id), email=email)
        return user

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        """
        Retrieve a user by ID.

        Raises:
            ResourceNotFoundError: User does not exist.
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError("User", user_id)
        return user

    async def get_by_email(self, email: str) -> User:
        """
        Retrieve a user by email.

        Raises:
            ResourceNotFoundError: Email not registered.
        """
        user = await self._repo.get_by_email(email.lower())
        if user is None:
            raise ResourceNotFoundError("User", email)
        return user

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def authenticate(self, email: str, password: str) -> User:
        """
        Verify credentials and return the authenticated user.

        Returns a generic error to avoid leaking which field is wrong.

        Raises:
            AuthenticationError: Invalid credentials or deactivated account.
        """
        user = await self._repo.get_by_email(email.lower())

        if user is None:
            # Constant-time: always call verify to prevent timing attacks
            verify_password(password, "$2b$12$unused_hash_for_timing_resistance")
            raise AuthenticationError("Invalid email or password.")

        if not user.hashed_password:
            raise AuthenticationError(
                "This account uses social login. Please sign in with Google."
            )

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("This account has been deactivated.")

        logger.info("user_authenticated", user_id=str(user.id))
        return user

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    async def update_profile(
        self, user_id: uuid.UUID, payload: UserUpdate
    ) -> User:
        """Update a user's profile fields."""
        await self.get_by_id(user_id)  # ensures existence

        updates: dict = {}
        if payload.full_name is not None:
            updates["full_name"] = payload.full_name
        if payload.avatar_url is not None:
            updates["avatar_url"] = payload.avatar_url

        if not updates:
            return await self.get_by_id(user_id)

        user = await self._repo.update_by_id(user_id, **updates)
        if user is None:
            raise ResourceNotFoundError("User", user_id)

        logger.info("user_profile_updated", user_id=str(user_id))
        return user

    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change a user's password after verifying the current one.

        OAuth-only users (no hashed_password) cannot use this endpoint.

        Raises:
            AuthenticationError: Current password is incorrect.
            InvalidInputError: New password fails strength requirements.
        """
        user = await self.get_by_id(user_id)

        if not user.hashed_password:
            raise InvalidInputError(
                "This account uses social login and does not have a local password."
            )

        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect.")

        if current_password == new_password:
            raise InvalidInputError(
                "New password must be different from the current password."
            )

        errors = validate_password_strength(new_password)
        if errors:
            raise InvalidInputError("; ".join(errors))

        await self._repo.update_by_id(
            user_id, hashed_password=hash_password(new_password)
        )
        logger.info("password_changed", user_id=str(user_id))

    # ------------------------------------------------------------------
    # Role management (admin only)
    # ------------------------------------------------------------------

    async def assign_role(self, user_id: uuid.UUID, role: str) -> User:
        """
        Assign a role to a user.

        Raises:
            ResourceNotFoundError: User does not exist.
            InvalidInputError: Role is invalid.
        """
        if role not in UserRole.ALL:
            raise InvalidInputError(
                f"Invalid role '{role}'. Must be one of: {', '.join(UserRole.ALL)}"
            )

        await self.get_by_id(user_id)  # ensures existence

        user = await self._repo.set_role(user_id, role)
        if user is None:
            raise ResourceNotFoundError("User", user_id)

        logger.info("user_role_assigned", user_id=str(user_id), role=role)
        return user

    async def deactivate(self, user_id: uuid.UUID, admin_user_id: uuid.UUID) -> User:
        """
        Deactivate a user account (admin action).

        An admin cannot deactivate themselves.

        Raises:
            InvalidInputError: Admin attempted to deactivate themselves.
            ResourceNotFoundError: User does not exist.
        """
        if user_id == admin_user_id:
            raise InvalidInputError("You cannot deactivate your own account.")

        await self.get_by_id(user_id)
        user = await self._repo.deactivate(user_id)
        if user is None:
            raise ResourceNotFoundError("User", user_id)

        logger.info(
            "user_deactivated",
            user_id=str(user_id),
            by_admin=str(admin_user_id),
        )
        return user

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    async def list_users(
        self, offset: int = 0, limit: int = 50
    ) -> tuple[list[User], int]:
        """Return a paginated list of active users with total count."""
        users = await self._repo.get_active_users(offset=offset, limit=limit)
        total = await self._repo.count()
        return users, total
