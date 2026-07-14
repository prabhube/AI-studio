"""
Pydantic schemas for all authentication operations.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Email / password login
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    """Credentials for the /auth/login endpoint."""
    email: EmailStr
    password: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Token responses
# ---------------------------------------------------------------------------

class TokenPairResponse(BaseModel):
    """Full token pair returned on successful login or OAuth."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token TTL in seconds


# Keep old name as alias for backward-compat with existing code
TokenResponse = TokenPairResponse


class AccessTokenResponse(BaseModel):
    """New access token returned by the /auth/refresh endpoint."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ---------------------------------------------------------------------------
# Refresh / logout
# ---------------------------------------------------------------------------

class RefreshTokenRequest(BaseModel):
    """Payload for the /auth/refresh endpoint."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """
    Payload for /auth/logout.

    Both tokens should be provided so both JTIs can be blacklisted.
    refresh_token is required; access_token is read from the Authorization header.
    """
    refresh_token: str


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

class GoogleOAuthUrlResponse(BaseModel):
    """URL the frontend should redirect the user to."""
    url: str
    state: str


class GoogleCallbackRequest(BaseModel):
    """Payload sent by the frontend after Google redirects back."""
    code: str
    state: str


# ---------------------------------------------------------------------------
# Password management
# ---------------------------------------------------------------------------

class PasswordResetRequest(BaseModel):
    """Request a password reset email (Phase 5+)."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Submit the reset token and new password (Phase 5+)."""
    token: str
    new_password: str = Field(min_length=8, max_length=128)
