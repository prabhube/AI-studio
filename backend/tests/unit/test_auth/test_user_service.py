"""
Unit tests for UserService.

Uses the in-memory SQLite test database via the db_session fixture.
"""

import pytest
import pytest_asyncio

from app.core.exceptions import (
    AuthenticationError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


@pytest.mark.asyncio
class TestUserServiceRegister:
    async def test_register_creates_user_successfully(self, db_session):
        service = UserService(db_session)
        payload = UserCreate(
            email="new@example.com",
            username="newuser",
            password="NewPass1",
        )
        user = await service.register(payload)

        assert user.email == "new@example.com"
        assert user.username == "newuser"
        assert user.hashed_password != "NewPass1"
        assert user.is_active is True
        assert user.is_superuser is False

    async def test_register_normalizes_email_to_lowercase(self, db_session):
        service = UserService(db_session)
        payload = UserCreate(
            email="UPPER@EXAMPLE.COM",
            username="upperuser",
            password="UpperPass1",
        )
        user = await service.register(payload)
        assert user.email == "upper@example.com"

    async def test_register_duplicate_email_raises_conflict(self, db_session, test_user):
        service = UserService(db_session)
        payload = UserCreate(
            email=test_user.email,
            username="differentuser",
            password="DiffPass1",
        )
        with pytest.raises(ResourceAlreadyExistsError):
            await service.register(payload)

    async def test_register_duplicate_username_raises_conflict(self, db_session, test_user):
        service = UserService(db_session)
        payload = UserCreate(
            email="different@example.com",
            username=test_user.username,
            password="DiffPass1",
        )
        with pytest.raises(ResourceAlreadyExistsError):
            await service.register(payload)


@pytest.mark.asyncio
class TestUserServiceAuthenticate:
    async def test_authenticate_with_valid_credentials(self, db_session, test_user):
        service = UserService(db_session)
        user = await service.authenticate(test_user.email, "TestPass1")
        assert user.id == test_user.id

    async def test_authenticate_wrong_password_raises_error(self, db_session, test_user):
        service = UserService(db_session)
        with pytest.raises(AuthenticationError):
            await service.authenticate(test_user.email, "WrongPassword1")

    async def test_authenticate_unknown_email_raises_error(self, db_session):
        service = UserService(db_session)
        with pytest.raises(AuthenticationError):
            await service.authenticate("ghost@example.com", "AnyPass1")

    async def test_authenticate_inactive_user_raises_error(self, db_session, test_user):
        test_user.is_active = False
        await db_session.flush()

        service = UserService(db_session)
        with pytest.raises(AuthenticationError):
            await service.authenticate(test_user.email, "TestPass1")

        # Restore
        test_user.is_active = True
        await db_session.flush()


@pytest.mark.asyncio
class TestUserServiceGetBy:
    async def test_get_by_id_returns_user(self, db_session, test_user):
        service = UserService(db_session)
        user = await service.get_by_id(test_user.id)
        assert user.id == test_user.id

    async def test_get_by_id_not_found_raises_error(self, db_session):
        import uuid

        service = UserService(db_session)
        with pytest.raises(ResourceNotFoundError):
            await service.get_by_id(uuid.uuid4())

    async def test_get_by_email_returns_user(self, db_session, test_user):
        service = UserService(db_session)
        user = await service.get_by_email(test_user.email)
        assert user.email == test_user.email


@pytest.mark.asyncio
class TestUserServiceUpdateProfile:
    async def test_update_full_name(self, db_session, test_user):
        service = UserService(db_session)
        updated = await service.update_profile(
            test_user.id, UserUpdate(full_name="New Name")
        )
        assert updated.full_name == "New Name"

    async def test_update_password_changes_hash(self, db_session, test_user):
        from app.core.security import verify_password

        old_hash = test_user.hashed_password
        service = UserService(db_session)
        updated = await service.update_profile(
            test_user.id, UserUpdate(password="NewPassword1")
        )
        assert updated.hashed_password != old_hash
        assert verify_password("NewPassword1", updated.hashed_password)

    async def test_update_nonexistent_user_raises_error(self, db_session):
        import uuid

        service = UserService(db_session)
        with pytest.raises(ResourceNotFoundError):
            await service.update_profile(
                uuid.uuid4(), UserUpdate(full_name="Ghost")
            )
