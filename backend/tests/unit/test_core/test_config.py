"""
Unit tests for application configuration.

Tests the model_validator guards and derived properties
without touching the real environment.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.core.config import Settings, get_settings


class TestSettingsDefaults:
    """Settings should load successfully with all defaults."""

    def test_default_environment_is_development(self):
        settings = Settings()
        assert settings.app_env == "development"

    def test_default_is_not_production(self):
        settings = Settings()
        assert not settings.is_production

    def test_database_sub_settings_are_accessible(self):
        settings = Settings()
        assert settings.database.host == "localhost"
        assert settings.database.port == 5432

    def test_redis_sub_settings_are_accessible(self):
        settings = Settings()
        assert settings.redis.host == "localhost"
        assert settings.redis.port == 6379

    def test_media_root_path_is_path_object(self):
        from pathlib import Path

        settings = Settings()
        assert isinstance(settings.media_root_path, Path)

    def test_max_upload_size_bytes_conversion(self):
        settings = Settings(MAX_UPLOAD_SIZE_MB=10)
        assert settings.max_upload_size_bytes == 10 * 1024 * 1024


class TestSettingsValidation:
    """model_validator guards should enforce production safety rules."""

    def test_insecure_secret_in_production_raises(self):
        with pytest.raises(ValueError, match="APP_SECRET_KEY must be changed"):
            Settings(
                APP_ENV="production",
                APP_DEBUG=False,
                APP_SECRET_KEY="change-this-to-a-secure-random-64-char-string",
            )

    def test_debug_true_in_production_raises(self):
        import secrets

        with pytest.raises(ValueError, match="APP_DEBUG must be False"):
            Settings(
                APP_ENV="production",
                APP_DEBUG=True,
                APP_SECRET_KEY=secrets.token_hex(64),
            )

    def test_secure_secret_in_production_succeeds(self):
        import secrets

        settings = Settings(
            APP_ENV="production",
            APP_DEBUG=False,
            APP_SECRET_KEY=secrets.token_hex(64),
        )
        assert settings.is_production

    def test_insecure_secret_in_development_emits_warning(self):
        import warnings

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Settings(
                APP_ENV="development",
                APP_SECRET_KEY="change-this-to-a-secure-random-64-char-string",
            )
        messages = [str(w.message) for w in caught]
        assert any("insecure default" in m for m in messages)


class TestGetSettings:
    """get_settings() should return the same instance on repeated calls."""

    def test_returns_settings_instance(self):
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_lru_cache_returns_same_instance(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
