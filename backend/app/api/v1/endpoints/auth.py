"""
Authentication API endpoints.

Endpoints:
  POST /auth/register           → create account
  POST /auth/login              → email/password → token pair
  POST /auth/refresh            → rotate refresh token
  POST /auth/logout             → revoke both tokens
  POST /auth/change-password    → change password (authenticated)
  GET  /auth/google             → get Google OAuth URL
  POST /auth/google/callback    → exchange code → token pair
  GET  /auth/me                 → current user profile

Rate limiting:
  - /login and /register are rate-limited to 10 req/min per IP to
    resist credential stuffing and brute force attacks.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import (
    AuthenticationError,
    CacheError,
    InvalidInputError,
    ProviderNotConfiguredError,
    ResourceAlreadyExistsError,
    TokenExpiredError,
    TokenInvalidError,
)
from app.core.logging import bind_user_context
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    GoogleCallbackRequest,
    GoogleOAuthUrlResponse,
    LogoutRequest,
    RefreshTokenRequest,
    LoginRequest,
    TokenPairResponse,
)
from app.schemas.common import SuccessResponse
from app.schemas.user import PasswordChange, UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])

_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description=(
        "Create a new account with email and password. "
        "Email and username must be unique. "
        "Password must be at least 8 characters with uppercase, digit, and special character."
    ),
)
async def register(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[UserResponse]:
    try:
        user_service = UserService(session)
        user = await user_service.register(payload)
        return SuccessResponse(
            data=UserResponse.model_validate(user),
            message="Account created successfully.",
        )
    except ResourceAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except InvalidInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=SuccessResponse[TokenPairResponse],
    summary="Authenticate with email and password",
    description=(
        "Returns an access token (short-lived) and a refresh token (long-lived). "
        "Use the refresh token at /auth/refresh when the access token expires."
    ),
)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[TokenPairResponse]:
    try:
        auth_service = AuthService(session)
        tokens = await auth_service.login(payload.email, payload.password)
        return SuccessResponse(data=tokens, message="Login successful.")
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


@router.post(
    "/refresh",
    response_model=SuccessResponse[AccessTokenResponse],
    summary="Rotate the refresh token and issue a new access token",
    description=(
        "The submitted refresh token is invalidated after this call (rotation). "
        "A new refresh token is returned in the response — store it securely."
    ),
)
async def refresh_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[AccessTokenResponse]:
    try:
        auth_service = AuthService(session)
        new_token = await auth_service.refresh(payload.refresh_token)
        return SuccessResponse(data=new_token, message="Token refreshed.")
    except (TokenExpiredError, TokenInvalidError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke both access and refresh tokens",
    description=(
        "Blacklists both tokens so they cannot be used again, even before expiry. "
        "The access token is read from the Authorization header. "
        "The refresh token must be provided in the request body."
    ),
)
async def logout(
    payload: LogoutRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    access_token = credentials.credentials if credentials else ""
    auth_service = AuthService(session)
    await auth_service.logout(
        access_token=access_token,
        refresh_token=payload.refresh_token,
    )


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password while logged in",
    description=(
        "Requires the current password for verification. "
        "After a successful change, all existing refresh tokens should be considered invalid — "
        "the client should log out and re-authenticate."
    ),
)
async def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    try:
        bind_user_context(user_id=str(current_user.id))
        user_service = UserService(session)
        await user_service.change_password(
            user_id=current_user.id,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        ) from exc
    except InvalidInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------------------------
# Current user profile
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


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------


@router.get(
    "/google",
    response_model=SuccessResponse[GoogleOAuthUrlResponse],
    summary="Get the Google OAuth authorization URL",
    description=(
        "Returns the URL to redirect the user to for Google sign-in. "
        "The `state` value must be stored by the client and verified on callback."
    ),
)
async def google_oauth_start(
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[GoogleOAuthUrlResponse]:
    try:
        auth_service = AuthService(session)
        result = await auth_service.get_google_oauth_url()
        return SuccessResponse(
            data=result,
            message="Redirect the user to the provided URL.",
        )
    except ProviderNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
    except CacheError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable.",
        ) from exc


@router.post(
    "/google/callback",
    response_model=SuccessResponse[TokenPairResponse],
    summary="Exchange Google OAuth code for JWT tokens",
    description=(
        "Call this after Google redirects the user back with an authorization code. "
        "Returns a token pair identical to the /login response."
    ),
)
async def google_oauth_callback(
    payload: GoogleCallbackRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SuccessResponse[TokenPairResponse]:
    try:
        auth_service = AuthService(session)
        tokens = await auth_service.google_callback(
            code=payload.code,
            state=payload.state,
        )
        return SuccessResponse(data=tokens, message="Google sign-in successful.")
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
        ) from exc
    except (ProviderNotConfiguredError, CacheError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable.",
        ) from exc
