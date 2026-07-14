"""
User management API endpoints.

Role access:
  - /users/me, /users/me (PATCH)  → any authenticated user
  - /users/ (GET), /users/{id}    → admin or superuser
  - /users/{id}/role              → superuser only
  - /users/{id}/deactivate        → admin or superuser
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_admin,
    get_current_superuser,
    get_current_user,
)
from app.core.exceptions import InvalidInputError, ResourceNotFoundError
from app.core.logging import bind_user_context
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.user import RoleUpdate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Get the current user's profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[UserResponse]:
    bind_user_context(user_id=str(current_user.id))
    return SuccessResponse(data=UserResponse.model_validate(current_user))


@router.patch(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="Update the current user's profile",
)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[UserResponse]:
    bind_user_context(user_id=str(current_user.id))
    try:
        user_service = UserService(session)
        updated = await user_service.update_profile(current_user.id, payload)
        return SuccessResponse(
            data=UserResponse.model_validate(updated),
            message="Profile updated.",
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


# ---------------------------------------------------------------------------
# Admin: list + lookup
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users (admin)",
    dependencies=[Depends(get_current_admin)],
)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse[UserResponse]:
    user_service = UserService(session)
    offset = (page - 1) * page_size
    users, total = await user_service.list_users(offset=offset, limit=page_size)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        data=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserResponse],
    summary="Get a user by ID (admin)",
    dependencies=[Depends(get_current_admin)],
)
async def get_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[UserResponse]:
    try:
        user_service = UserService(session)
        user = await user_service.get_by_id(user_id)
        return SuccessResponse(data=UserResponse.model_validate(user))
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


# ---------------------------------------------------------------------------
# Admin: role assignment
# ---------------------------------------------------------------------------


@router.patch(
    "/{user_id}/role",
    response_model=SuccessResponse[UserResponse],
    summary="Assign a role to a user (superuser only)",
    dependencies=[Depends(get_current_superuser)],
)
async def assign_role(
    user_id: uuid.UUID,
    payload: RoleUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[UserResponse]:
    try:
        user_service = UserService(session)
        user = await user_service.assign_role(user_id, payload.role)
        return SuccessResponse(
            data=UserResponse.model_validate(user),
            message=f"Role updated to '{payload.role}'.",
        )
    except (ResourceNotFoundError, InvalidInputError) as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if isinstance(exc, ResourceNotFoundError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(code, detail=exc.message) from exc


# ---------------------------------------------------------------------------
# Admin: account deactivation
# ---------------------------------------------------------------------------


@router.post(
    "/{user_id}/deactivate",
    response_model=SuccessResponse[UserResponse],
    summary="Deactivate a user account (admin)",
)
async def deactivate_user(
    user_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[UserResponse]:
    try:
        user_service = UserService(session)
        user = await user_service.deactivate(user_id, current_admin.id)
        return SuccessResponse(
            data=UserResponse.model_validate(user),
            message="Account deactivated.",
        )
    except InvalidInputError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    except ResourceNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
