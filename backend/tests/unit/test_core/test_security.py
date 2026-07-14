"""
Unit tests for app.core.security module.

Covers password hashing and JWT token lifecycle.
"""

from datetime import timedelta

import pytest

from app.core.exceptions import TokenExpiredError, TokenInvalidError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    extract_subject,
    hash_password,
    verify_password,
)


# ============================================================
# Password Hashing
# ============================================================


class TestPasswordHashing:
    def test_hash_returns_non_empty_string(self):
        result = hash_password("SomePassword1")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_is_not_plaintext(self):
        result = hash_password("SomePassword1")
        assert result != "SomePassword1"

    def test_verify_correct_password(self):
        hashed = hash_password("CorrectPass1")
        assert verify_password("CorrectPass1", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("CorrectPass1")
        assert verify_password("WrongPass1", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses random salt — same input never yields the same hash."""
        h1 = hash_password("SamePass1")
        h2 = hash_password("SamePass1")
        assert h1 != h2

    def test_verify_works_with_different_hash_of_same_password(self):
        """Despite different hashes, verification should still pass."""
        hashed = hash_password("SamePass1")
        assert verify_password("SamePass1", hashed) is True


# ============================================================
# JWT Tokens
# ============================================================


class TestJWTTokens:
    def test_create_access_token_returns_string(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_contains_subject(self):
        token = create_access_token("user-456")
        payload = decode_token(token, expected_type="access")
        assert payload["sub"] == "user-456"

    def test_decode_access_token_has_correct_type(self):
        token = create_access_token("user-789")
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token("user-123")
        assert isinstance(token, str)

    def test_decode_refresh_token_has_correct_type(self):
        token = create_refresh_token("user-123")
        payload = decode_token(token, expected_type="refresh")
        assert payload["type"] == "refresh"

    def test_access_token_rejected_as_refresh(self):
        token = create_access_token("user-123")
        with pytest.raises(TokenInvalidError):
            decode_token(token, expected_type="refresh")

    def test_refresh_token_rejected_as_access(self):
        token = create_refresh_token("user-123")
        with pytest.raises(TokenInvalidError):
            decode_token(token, expected_type="access")

    def test_expired_token_raises_token_expired_error(self):
        token = create_access_token("user-123", expires_delta=timedelta(seconds=-1))
        with pytest.raises(TokenExpiredError):
            decode_token(token)

    def test_tampered_token_raises_token_invalid_error(self):
        token = create_access_token("user-123")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(TokenInvalidError):
            decode_token(tampered)

    def test_extract_subject_returns_correct_subject(self):
        token = create_access_token("user-999")
        subject = extract_subject(token)
        assert subject == "user-999"

    def test_extra_claims_are_embedded(self):
        token = create_access_token("user-123", extra_claims={"role": "admin"})
        payload = decode_token(token)
        assert payload.get("role") == "admin"
