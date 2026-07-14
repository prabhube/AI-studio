"""
Generic async repository base class.

Implements the Repository Pattern with common CRUD operations.
All domain repositories inherit from this class.
"""

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository providing standard CRUD operations.

    Type parameter ModelT must be a SQLAlchemy ORM model class.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession) -> None:
                super().__init__(User, session)
    """

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self._model = model
        self._session = session

    async def get_by_id(self, record_id: uuid.UUID) -> ModelT | None:
        """Return a single record by primary key, or None if not found."""
        result = await self._session.execute(
            select(self._model).where(self._model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.scalars().first()

    async def get_all(
        self, offset: int = 0, limit: int = 100
    ) -> list[ModelT]:
        """Return a paginated list of all records."""
        result = await self._session.execute(
            select(self._model).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return the total number of records."""
        from sqlalchemy import func

        result = await self._session.execute(
            select(func.count()).select_from(self._model)
        )
        return result.scalar_one()

    async def create(self, **kwargs: Any) -> ModelT:
        """
        Create and persist a new record.

        Args:
            **kwargs: Column values for the new record.

        Returns:
            The created ORM instance (refreshed from DB).
        """
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def update_by_id(
        self, record_id: uuid.UUID, **kwargs: Any
    ) -> ModelT | None:
        """
        Update a record by ID and return the updated instance.

        Args:
            record_id: Primary key of the record to update.
            **kwargs: Column values to update.

        Returns:
            The updated instance, or None if not found.
        """
        await self._session.execute(
            update(self._model)
            .where(self._model.id == record_id)  # type: ignore[attr-defined]
            .values(**kwargs)
        )
        return await self.get_by_id(record_id)

    async def delete_by_id(self, record_id: uuid.UUID) -> bool:
        """
        Hard-delete a record by ID.

        Returns:
            True if a record was deleted, False if not found.
        """
        from sqlalchemy import delete

        result = await self._session.execute(
            delete(self._model).where(self._model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.rowcount > 0

    async def exists(self, record_id: uuid.UUID) -> bool:
        """Return True if a record with the given ID exists."""
        return await self.get_by_id(record_id) is not None
