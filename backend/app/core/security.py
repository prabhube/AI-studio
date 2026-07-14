"""
Security utilities: password hashing, JWT management, and CSRF tokens.

Design decisions:
  - Every token includes a `jti` (JWT ID) — a UUID4 unique to that token.
    This enables per-token revocation: on logout or token rotation, the
    jti is stored in Redis until the token naturally expires.
  - Access and refresh tokens embed different `type` claims to prevent
    refresh tokens from being accepted where access tokens are expected.
  - bcrypt work factor is locked at 12 rounds — a deliberate trade-off
    between security (slow enough to resist brute force) and UX
    (fast enough for interactive login, ~250ms on modern hardware).
  - Password strength validation lives here, not in Pydantic schemas,
    so it can be reused without importing schemas (avoids circular imports).
  - generate_csrf_token() is used for the OAuth state parameter —
    a cryptographically secure random string, not a JWT.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import TokenExpiredError, TokenInvalidError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Work factor 12 — deliberately slow enough to resist offline brute force.
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt (work factor 12)."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> list[str]:
    """
    Return a list of unmet password requirements.

    Returns an empty list if the password passes all checks.
    Callers should raise InvalidInputError if the list is non-empty.

    Requirements:
      - At least 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
      - At least one special character
    """
    errors: list[str] = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter.")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit.")
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        errors.append("Password must contain at least one special character.")
    return errors


# ---------------------------------------------------------------------------
# JWT token management
# ---------------------------------------------------------------------------


def _jwt_settings() -> tuple[str, str]:
    """Return (secret_key, algorithm) from the current settings."""
    settings = get_settings()
    return settings.jwt.secret_key, settings.jwt.algorithm


def _build_payload(
    subject: str,
    token_type: str,
    expires_at: datetime,
    jti: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": datetime.now(UTC),
        "exp": expires_at,
    }
    if extra:
        payload.update(extra)
    return payload


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """
    Create a signed JWT access token.

    Returns:
        (token_string, jti) — the jti is needed to blacklist the token on logout.
    """
    settings = get_settings()
    secret_key, algorithm = _jwt_settings()
    jti = str(uuid.uuid4())

    expire = datetime.now(UTC) + (
        expires_delta
        or timedelta(minutes=settings.jwt.access_token_expire_minutes)
    )

    payload = _build_payload(
        subject=subject,
        token_type="access",
        expires_at=expire,
        jti=jti,
        extra=extra_claims,
    )

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    logger.debug("access_token_created", subject=subject, jti=jti)
    return token, jti


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """
    Create a signed JWT refresh token.

    Returns:
        (token_string, jti) — the jti is used for token rotation tracking.
    """
    settings = get_settings()
    secret_key, algorithm = _jwt_settings()
    jti = str(uuid.uuid4())

    expire = datetime.now(UTC) + (
        expires_delta
        or timedelta(days=settings.jwt.refresh_token_expire_days)
    )

    payload = _build_payload(
        subject=subject,
        token_type="refresh",
        expires_at=expire,
        jti=jti,
    )

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    logger.debug("refresh_token_created", subject=subject, jti=jti)
    return token, jti


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        TokenExpiredError: Token's exp has passed.
        TokenInvalidError: Malformed, wrong signature, or wrong type.
    """
    secret_key, algorithm = _jwt_settings()

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError as exc:
        msg = str(exc).lower()
        if "expired" in msg or "exp" in msg:
            raise TokenExpiredError("Token has expired.") from exc
        raise TokenInvalidError(f"Token is invalid: {exc}") from exc

    if payload.get("type") != expected_type:
        raise TokenInvalidError(
            f"Expected token type '{expected_type}', got '{payload.get('type')}'."
        )

    return payload


def extract_subject(token: str, expected_type: str = "access") -> str:
    """Decode a token and return the 'sub' claim."""
    payload = decode_token(token, expected_type=expected_type)
    sub = payload.get("sub")
    if not sub:
        raise TokenInvalidError("Token payload is missing the 'sub' claim.")
    return sub


def extract_jti(token: str, expected_type: str = "access") -> str:
    """Decode a token and return the 'jti' claim."""
    payload = decode_token(token, expected_type=expected_type)
    jti = payload.get("jti")
    if not jti:
        raise TokenInvalidError("Token payload is missing the 'jti' claim.")
    return jti


def get_token_remaining_seconds(token: str) -> int:
    """
    Return how many seconds until the token expires.

    Used to set the TTL when blacklisting a token in Redis.
    Returns 0 if the token is already expired.
    """
    secret_key, algorithm = _jwt_settings()
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        exp = payload.get("exp", 0)
        remaining = int(exp - datetime.now(UTC).timestamp())
        return max(0, remaining)
    except JWTError:
        return 0


# ---------------------------------------------------------------------------
# CSRF / state token (used for OAuth state parameter)
# ---------------------------------------------------------------------------


def generate_state_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random state token.

    Used as the OAuth `state` parameter to prevent CSRF attacks.
    The token is stored in Redis for 10 minutes, then verified on callback.
    """
    return secrets.token_urlsafe(length)
