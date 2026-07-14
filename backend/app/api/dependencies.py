"""
FastAPI dependency injection definitions.

Design decisions:
  - get_current_user checks the token JTI against the Redis blacklist on
    EVERY request. This is the only way to guarantee a logged-out token
    cannot be reused before its natural expiry.
  - require_role() is a dependency factory — it returns a Depends()-able
    function that accepts a role (or list of roles) and raises 403 if the
    authenticated user doesn't qualify.
  - get_optional_user returns None (no 401) if no token is present. Used
    for endpoints that serve both anonymous and authenticated users.
  - All 401 responses include WWW-Authenticate: Bearer per RFC 6750.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import (
    ResourceNotFoundError,
    TokenExpiredError,
    TokenInvalidError,
)
from app.core.logging import get_logger
from app.core.security import decode_token
from app.db.session import AsyncSession, get_db_session
from app.models.user import User, UserRole
from app.services.auth_service import is_token_blacklisted
from app.services.user_service import UserService

logger = get_logger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

_WWW_BEARER = {"WWW-Authenticate": "Bearer"}


# ---------------------------------------------------------------------------
# Core user dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Decode the Bearer token and return the authenticated User.

    Performs these checks in order:
      1. Token is present in the Authorization header.
      2. Token is a valid, unexpired JWT.
      3. Token's JTI is NOT in the Redis blacklist.
      4. User exists in the database.
      5. User account is active.

    Raises HTTP 401 for any auth failure.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing.",
            headers=_WWW_BEARER,
        )

    token = credentials.credentials

    # Decode token — raises on expired / invalid
    try:
        payload = decode_token(token, expected_type="access")
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Please refresh your session.",
            headers=_WWW_BEARER,
        )
    except TokenInvalidError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers=_WWW_BEARER,
        )

    jti = payload.get("jti")
    user_id_str = payload.get("sub")

    if not jti or not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required claims.",
            headers=_WWW_BEARER,
        )

    # Check blacklist — ensures logged-out tokens are rejected
    if await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers=_WWW_BEARER,
        )

    # Load the user
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token contains an invalid user ID.",
            headers=_WWW_BEARER,
        )

    try:
        user_service = UserService(session)
        user = await user_service.get_by_id(user_id)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist.",
            headers=_WWW_BEARER,
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated.",
        )

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User | None:
    """
    Return the authenticated user, or None if no token is present.

    Does NOT raise 401 — intended for endpoints that serve both anonymous
    and authenticated users differently.
    """
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials=credentials, session=session)
    except HTTPException:
        return None


# ---------------------------------------------------------------------------
# Role-based dependencies
# ---------------------------------------------------------------------------


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the user to have admin or superuser role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the user to have the superuser role."""
    if current_user.role != UserRole.SUPERUSER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required.",
        )
    return current_user


def require_role(*roles: str):
    """
    Dependency factory: require the current user to have one of the given roles.

    Usage:
        @router.delete("/{id}", dependencies=[Depends(require_role("admin", "superuser"))])
        async def delete_thing(...):
            ...
    """
    async def _dep(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of the following roles is required: {', '.join(roles)}",
            )
        return current_user
    return _dep
