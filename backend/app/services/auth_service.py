"""
Authentication service.

Responsibilities:
  - Email/password login with token pair issuance
  - Refresh token rotation (old refresh token blacklisted on each use)
  - Logout (both access and refresh token JTIs blacklisted in Redis)
  - Google OAuth 2.0 authorization-code flow
  - Token blacklist management via Redis

Design decisions:
  - Token blacklisting uses Redis with TTL = remaining token lifetime.
    This means blacklist entries expire naturally — no cleanup job needed.
  - Refresh token rotation: each refresh call issues a NEW refresh token
    and blacklists the submitted one. This limits the window of exposure
    if a refresh token is stolen.
  - State tokens for Google OAuth are stored in Redis with a 10-minute
    TTL. On callback, the state is verified and immediately deleted (single use).
  - We use httpx (already in requirements) for Google API calls to avoid
    adding another OAuth library dependency.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    CacheError,
    InvalidInputError,
    ProviderNotConfiguredError,
    TokenExpiredError,
    TokenInvalidError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_state_token,
    get_token_remaining_seconds,
)
from app.db.redis_client import get_redis_client
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AccessTokenResponse, GoogleOAuthUrlResponse, TokenPairResponse
from app.services.user_service import UserService

logger = get_logger(__name__)

# Redis key prefixes
_BLACKLIST_PREFIX = "token_blacklist:"
_OAUTH_STATE_PREFIX = "oauth_state:"

# Google OAuth endpoints
_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# ---------------------------------------------------------------------------
# Token blacklist helpers
# ---------------------------------------------------------------------------


async def _blacklist_jti(jti: str, ttl_seconds: int) -> None:
    """Add a token JTI to the Redis blacklist with the given TTL."""
    if ttl_seconds <= 0:
        return  # Already expired — no point storing
    try:
        client = await get_redis_client()
        await client.setex(f"{_BLACKLIST_PREFIX}{jti}", ttl_seconds, "1")
    except Exception as exc:
        logger.warning("token_blacklist_write_failed", jti=jti, error=str(exc))


async def is_token_blacklisted(jti: str) -> bool:
    """Return True if the token JTI is in the blacklist."""
    try:
        client = await get_redis_client()
        return await client.exists(f"{_BLACKLIST_PREFIX}{jti}") > 0
    except Exception as exc:
        logger.warning("token_blacklist_check_failed", jti=jti, error=str(exc))
        # Fail open — don't reject valid tokens if Redis is down
        return False


# ---------------------------------------------------------------------------
# Token issuance helpers
# ---------------------------------------------------------------------------


def _issue_token_pair(user_id: str, settings) -> tuple[TokenPairResponse, str, str]:
    """
    Issue an access + refresh token pair.

    Returns:
        (TokenPairResponse, access_jti, refresh_jti)
    """
    access_token, access_jti = create_access_token(subject=user_id)
    refresh_token, refresh_jti = create_refresh_token(subject=user_id)

    response = TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt.access_token_expire_minutes * 60,
    )
    return response, access_jti, refresh_jti


# ---------------------------------------------------------------------------
# AuthService
# ---------------------------------------------------------------------------


class AuthService:
    """Orchestrates token lifecycle and OAuth flows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserRepository(session)
        self._user_service = UserService(session)

    # ------------------------------------------------------------------
    # Email / password
    # ------------------------------------------------------------------

    async def login(self, email: str, password: str) -> TokenPairResponse:
        """
        Authenticate with email + password and issue a token pair.

        Raises:
            AuthenticationError: Bad credentials or deactivated account.
        """
        user = await self._user_service.authenticate(email, password)

        # Update last_login_at (fire and forget — don't fail on error)
        try:
            await self._repo.set_last_login(user.id)
        except Exception as exc:
            logger.warning("last_login_update_failed", user_id=str(user.id), error=str(exc))

        settings = get_settings()
        tokens, _, _ = _issue_token_pair(str(user.id), settings)

        logger.info("login_successful", user_id=str(user.id))
        return tokens

    # ------------------------------------------------------------------
    # Token rotation
    # ------------------------------------------------------------------

    async def refresh(self, refresh_token: str) -> AccessTokenResponse:
        """
        Issue a new access token (and optionally rotate the refresh token).

        The submitted refresh token's JTI is blacklisted immediately.
        A new refresh token is returned so the client's session stays alive.

        Raises:
            TokenExpiredError / TokenInvalidError: Invalid refresh token.
            AuthenticationError: User deactivated or deleted.
        """
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except (TokenExpiredError, TokenInvalidError):
            raise

        jti = payload.get("jti")
        user_id_str = payload.get("sub")

        if not jti or not user_id_str:
            raise TokenInvalidError("Refresh token is missing required claims.")

        # Check blacklist — prevents re-use of a rotated token
        if await is_token_blacklisted(jti):
            logger.warning(
                "refresh_token_reuse_detected",
                jti=jti,
                user_id=user_id_str,
            )
            raise TokenInvalidError(
                "Refresh token has already been used. Please log in again."
            )

        # Verify user still exists and is active
        user = await self._repo.get_by_id(uuid.UUID(user_id_str))
        if user is None or not user.is_active:
            raise AuthenticationError("User account does not exist or is deactivated.")

        # Blacklist the submitted refresh token
        remaining = get_token_remaining_seconds(refresh_token)
        await _blacklist_jti(jti, remaining)

        # Issue fresh access token + new refresh token
        settings = get_settings()
        new_access_token, _ = create_access_token(subject=user_id_str)
        new_refresh_token, _ = create_refresh_token(subject=user_id_str)

        logger.info("token_rotated", user_id=user_id_str)

        return AccessTokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.jwt.access_token_expire_minutes * 60,
        )

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    async def logout(
        self, access_token: str, refresh_token: str
    ) -> None:
        """
        Invalidate both the access and refresh tokens.

        Blacklists each token's JTI in Redis with TTL = remaining lifetime.
        After this, neither token can be used — even if they haven't expired.
        """
        for token, token_type in [
            (access_token, "access"),
            (refresh_token, "refresh"),
        ]:
            try:
                payload = decode_token(token, expected_type=token_type)
                jti = payload.get("jti")
                if jti:
                    remaining = get_token_remaining_seconds(token)
                    await _blacklist_jti(jti, remaining)
            except (TokenExpiredError, TokenInvalidError):
                # Already expired tokens are effectively revoked — no action needed
                pass
            except Exception as exc:
                logger.warning("logout_blacklist_error", error=str(exc))

        logger.info("logout_successful")

    # ------------------------------------------------------------------
    # Google OAuth
    # ------------------------------------------------------------------

    async def get_google_oauth_url(self) -> GoogleOAuthUrlResponse:
        """
        Build the Google OAuth authorization URL.

        The state token is stored in Redis for 10 minutes to validate
        the callback and prevent CSRF.

        Raises:
            ProviderNotConfiguredError: Google credentials are not set.
        """
        settings = get_settings()
        if not settings.oauth.google_enabled:
            raise ProviderNotConfiguredError("Google OAuth")

        state = generate_state_token()

        # Store state in Redis with TTL
        try:
            client = await get_redis_client()
            await client.setex(
                f"{_OAUTH_STATE_PREFIX}{state}",
                settings.oauth.state_token_ttl,
                "1",
            )
        except Exception as exc:
            raise CacheError(f"Failed to store OAuth state: {exc}") from exc

        params = {
            "client_id": settings.oauth.google_client_id,
            "redirect_uri": settings.oauth.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
            "prompt": "select_account",
        }

        url = f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"
        return GoogleOAuthUrlResponse(url=url, state=state)

    async def google_callback(
        self, code: str, state: str
    ) -> TokenPairResponse:
        """
        Handle the Google OAuth callback.

        1. Validate state token (CSRF check).
        2. Exchange code for Google user info.
        3. Find or create the local user.
        4. Issue a JWT token pair.

        Raises:
            AuthenticationError: State mismatch, exchange failure.
            ProviderNotConfiguredError: Google credentials not set.
        """
        settings = get_settings()
        if not settings.oauth.google_enabled:
            raise ProviderNotConfiguredError("Google OAuth")

        # Validate state — single-use check
        await self._validate_and_consume_state(state)

        # Exchange authorization code for user info
        google_user = await self._exchange_google_code(code, settings)

        # Find or create the local user
        user = await self._get_or_create_google_user(google_user)

        if not user.is_active:
            raise AuthenticationError("Your account has been deactivated.")

        await self._repo.set_last_login(user.id)

        tokens, _, _ = _issue_token_pair(str(user.id), settings)
        logger.info(
            "google_oauth_login",
            user_id=str(user.id),
            email=user.email,
        )
        return tokens

    async def _validate_and_consume_state(self, state: str) -> None:
        """Verify and delete the OAuth state token from Redis."""
        try:
            client = await get_redis_client()
            key = f"{_OAUTH_STATE_PREFIX}{state}"
            deleted = await client.delete(key)
            if not deleted:
                raise AuthenticationError(
                    "Invalid or expired OAuth state. Please try again."
                )
        except AuthenticationError:
            raise
        except Exception as exc:
            raise CacheError(f"Failed to validate OAuth state: {exc}") from exc

    async def _exchange_google_code(
        self, code: str, settings
    ) -> dict:
        """Exchange the authorization code for Google user info."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: exchange code for tokens
            token_resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.oauth.google_client_id,
                    "client_secret": settings.oauth.google_client_secret,
                    "redirect_uri": settings.oauth.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if token_resp.status_code != 200:
                logger.error(
                    "google_token_exchange_failed",
                    status=token_resp.status_code,
                )
                raise AuthenticationError(
                    "Failed to exchange Google authorization code."
                )

            google_access_token = token_resp.json().get("access_token")
            if not google_access_token:
                raise AuthenticationError("Google did not return an access token.")

            # Step 2: fetch user info
            userinfo_resp = await client.get(
                _GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {google_access_token}"},
            )

            if userinfo_resp.status_code != 200:
                raise AuthenticationError("Failed to fetch Google user information.")

            return userinfo_resp.json()

    async def _get_or_create_google_user(self, google_info: dict) -> User:
        """
        Find an existing user by OAuth ID, then by email, or create a new one.

        Priority:
          1. Exact match on (oauth_provider="google", oauth_provider_id=sub)
          2. Email match — link OAuth to existing email/password account
          3. Create new user
        """
        google_id = google_info.get("sub", "")
        email = google_info.get("email", "").lower()
        name = google_info.get("name", "")
        picture = google_info.get("picture")
        email_verified = google_info.get("email_verified", False)

        if not email or not google_id:
            raise AuthenticationError(
                "Google account did not provide a valid email or user ID."
            )

        # 1. Look up by OAuth provider ID
        user = await self._repo.get_by_oauth("google", google_id)
        if user:
            # Update avatar if changed
            if picture and user.avatar_url != picture:
                await self._repo.update_by_id(user.id, avatar_url=picture)
            return user

        # 2. Look up by email — link OAuth to existing account
        user = await self._repo.get_by_email(email)
        if user:
            await self._repo.update_by_id(
                user.id,
                oauth_provider="google",
                oauth_provider_id=google_id,
                avatar_url=picture or user.avatar_url,
                email_verified=True,
            )
            return user

        # 3. Create a new user
        username = await self._generate_unique_username(email)
        user = await self._repo.create(
            email=email,
            username=username,
            full_name=name or None,
            hashed_password=None,  # No local password for OAuth users
            avatar_url=picture,
            role=UserRole.USER,
            is_active=True,
            is_superuser=False,
            email_verified=bool(email_verified),
            oauth_provider="google",
            oauth_provider_id=google_id,
        )
        logger.info("oauth_user_created", user_id=str(user.id), provider="google")
        return user

    async def _generate_unique_username(self, email: str) -> str:
        """Derive a unique username from an email address."""
        base = email.split("@")[0].lower()
        # Keep only alphanumeric + underscore
        base = "".join(c if c.isalnum() or c == "_" else "_" for c in base)
        base = base[:30] or "user"

        candidate = base
        for i in range(1, 20):
            if not await self._repo.username_exists(candidate):
                return candidate
            candidate = f"{base}_{i}"

        # Ultimate fallback
        return f"user_{uuid.uuid4().hex[:8]}"
