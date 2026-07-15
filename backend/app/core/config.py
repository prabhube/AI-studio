"""
Application configuration management.

Design decisions:
  - Single Settings class with nested Pydantic models for grouping.
    Sub-settings are instantiated ONCE via model_validator, not re-created
    on every property access (the previous anti-pattern).
  - model_validator(mode='after') blocks startup if unsafe defaults are
    used in production, preventing silent security failures.
  - @lru_cache ensures settings are parsed exactly once per process.
  - All env var aliases are UPPER_CASE to match .env convention.
  - computed_field builds derived values (e.g. safe DSN for logging)
    without duplicating configuration.
"""

from __future__ import annotations

import warnings
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Grouped sub-settings (not BaseSettings — avoids double env-var parsing)
# ---------------------------------------------------------------------------


class DatabaseSettings(BaseSettings):
    """PostgreSQL async connection configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    user: str = Field(default="prabhu", alias="POSTGRES_USER")
    password: str = Field(default="prabhu_secret", alias="POSTGRES_PASSWORD")
    db: str = Field(default="prabhu_ai_studio", alias="POSTGRES_DB")

    # Explicit URL overrides the constructed one when set.
    url: str = Field(
        default="postgresql+asyncpg://prabhu:prabhu_secret@localhost:5432/prabhu_ai_studio",
        alias="DATABASE_URL",
    )

    # Pool tuning
    pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")
    echo: bool = Field(default=False, alias="DB_ECHO")

    @computed_field  # type: ignore[misc]
    @property
    def safe_url(self) -> str:
        """URL with password redacted — safe to log."""
        try:
            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(self.url)
            if parsed.password:
                netloc = f"{parsed.username}:***@{parsed.hostname}:{parsed.port}"
                return urlunparse(parsed._replace(netloc=netloc))
        except Exception:
            pass
        return self.url.split("@")[-1]


class RedisSettings(BaseSettings):
    """Redis connection configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    password: str = Field(default="redis_secret", alias="REDIS_PASSWORD")
    db: int = Field(default=0, alias="REDIS_DB")
    url: str = Field(
        default="redis://:redis_secret@localhost:6379/0",
        alias="REDIS_URL",
    )

    # Connection behaviour
    socket_connect_timeout: int = Field(default=5, alias="REDIS_CONNECT_TIMEOUT")
    socket_timeout: int = Field(default=5, alias="REDIS_TIMEOUT")
    max_connections: int = Field(default=20, alias="REDIS_MAX_CONNECTIONS")
    health_check_interval: int = Field(default=30, alias="REDIS_HEALTH_CHECK_INTERVAL")

    # Retry behaviour (exponential backoff)
    retry_on_timeout: bool = Field(default=True, alias="REDIS_RETRY_ON_TIMEOUT")
    retry_max_attempts: int = Field(default=3, alias="REDIS_RETRY_MAX_ATTEMPTS")


class RateLimitSettings(BaseSettings):
    """SlowAPI rate-limiting configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    requests_per_minute: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")
    burst_multiplier: int = Field(default=2, alias="RATE_LIMIT_BURST")


class LLMSettings(BaseSettings):
    """Language model provider configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    provider: Literal["gemma", "llama", "none"] = Field(
        default="none", alias="LLM_PROVIDER"
    )
    model_path: str = Field(
        default="/models/llm/gemma-2b-it.gguf", alias="LLM_MODEL_PATH"
    )
    max_tokens: int = Field(default=2048, alias="LLM_MAX_TOKENS")
    temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    context_length: int = Field(default=4096, alias="LLM_CONTEXT_LENGTH")
    n_threads: int = Field(default=4, alias="LLM_THREADS")

    # Prompt analysis — structured extraction wants near-deterministic output,
    # so it overrides the conversational defaults above.
    analyzer_temperature: float = Field(
        default=0.2, alias="LLM_ANALYZER_TEMPERATURE"
    )
    analyzer_max_tokens: int = Field(
        default=1024, alias="LLM_ANALYZER_MAX_TOKENS"
    )


class ImageSettings(BaseSettings):
    """Image generation provider configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    provider: Literal["stable_diffusion", "none"] = Field(
        default="none", alias="IMAGE_PROVIDER"
    )
    model_path: str = Field(
        default="/models/sd/v1-5-pruned-emaonly.safetensors",
        alias="SD_MODEL_PATH",
    )
    output_dir: str = Field(default="/app/media/images", alias="SD_OUTPUT_DIR")
    default_width: int = Field(default=512, alias="SD_DEFAULT_WIDTH")
    default_height: int = Field(default=512, alias="SD_DEFAULT_HEIGHT")
    default_steps: int = Field(default=20, alias="SD_DEFAULT_STEPS")
    device: Literal["cpu", "cuda", "mps"] = Field(default="cpu", alias="SD_DEVICE")


class TTSSettings(BaseSettings):
    """Text-to-speech provider configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    provider: Literal["piper", "none"] = Field(
        default="none", alias="TTS_PROVIDER"
    )
    model_path: str = Field(
        default="/models/tts/en_US-lessac-medium.onnx",
        alias="PIPER_MODEL_PATH",
    )
    output_dir: str = Field(default="/app/media/audio", alias="TTS_OUTPUT_DIR")


class STTSettings(BaseSettings):
    """Speech-to-text provider configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    provider: Literal["whisper", "none"] = Field(
        default="none", alias="STT_PROVIDER"
    )
    model_size: Literal["tiny", "base", "small", "medium", "large"] = Field(
        default="base", alias="WHISPER_MODEL_SIZE"
    )
    output_dir: str = Field(
        default="/app/media/transcripts", alias="STT_OUTPUT_DIR"
    )
    device: Literal["cpu", "cuda"] = Field(default="cpu", alias="WHISPER_DEVICE")


class VideoSettings(BaseSettings):
    """Video assembly provider configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    provider: Literal["ffmpeg", "none"] = Field(
        default="none", alias="VIDEO_PROVIDER"
    )
    output_dir: str = Field(
        default="/app/media/videos", alias="FFMPEG_OUTPUT_DIR"
    )
    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")
    ffprobe_path: str = Field(default="ffprobe", alias="FFPROBE_PATH")


class JWTSettings(BaseSettings):
    """JWT token configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    secret_key: str = Field(
        default="change-this-to-a-secure-random-64-char-string",
        alias="APP_SECRET_KEY",
    )
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=30, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )


class OAuthSettings(BaseSettings):
    """Google OAuth 2.0 configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/google/callback",
        alias="GOOGLE_REDIRECT_URI",
    )

    # State token TTL (seconds) — how long an OAuth flow can be in-flight
    state_token_ttl: int = Field(default=600, alias="OAUTH_STATE_TTL")

    @property
    def google_enabled(self) -> bool:
        """Return True if Google OAuth is configured."""
        return bool(self.google_client_id and self.google_client_secret)


# ---------------------------------------------------------------------------
# Root settings
# ---------------------------------------------------------------------------

#: Default secret used only in development. Any matching value in production raises.
_INSECURE_DEFAULTS = frozenset(
    {
        "change-this-to-a-secure-random-64-char-string",
        "change-this-to-another-secure-random-64-char-string",
        "secret",
        "dev",
        "development",
    }
)


class Settings(BaseSettings):
    """
    Root application settings — single source of truth.

    Sub-settings are resolved ONCE on construction via model_validator.
    Access via `get_settings()` which is @lru_cache — one parse per process.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application identity
    # ------------------------------------------------------------------
    app_name: str = Field(default="Prabhu AI Studio", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_env: Literal["development", "testing", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_secret_key: str = Field(
        default="change-this-to-a-secure-random-64-char-string",
        alias="APP_SECRET_KEY",
    )

    # ------------------------------------------------------------------
    # Network / CORS
    # ------------------------------------------------------------------
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="ALLOWED_ORIGINS",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v: str | list[str]) -> list[str]:
        """Accept comma-separated string or list from environment."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ------------------------------------------------------------------
    # Media storage
    # ------------------------------------------------------------------
    media_root: str = Field(default="/app/media", alias="MEDIA_ROOT")
    max_upload_size_mb: int = Field(default=500, alias="MAX_UPLOAD_SIZE_MB")

    # ------------------------------------------------------------------
    # Sub-settings (resolved once in model_validator below)
    # ------------------------------------------------------------------
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    image: ImageSettings = Field(default_factory=ImageSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    stt: STTSettings = Field(default_factory=STTSettings)
    video: VideoSettings = Field(default_factory=VideoSettings)
    oauth: OAuthSettings = Field(default_factory=OAuthSettings)

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_production_security(self) -> "Settings":
        """
        Block startup if insecure defaults are used in production.

        In development, emit a warning instead of raising so that new
        developers can run the app without configuring every secret first.
        """
        if self.app_secret_key in _INSECURE_DEFAULTS:
            if self.is_production:
                raise ValueError(
                    "APP_SECRET_KEY must be changed from the default in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(64))\""
                )
            warnings.warn(
                "APP_SECRET_KEY is set to the insecure default. "
                "Set a proper value in .env before going to production.",
                stacklevel=2,
            )
        return self

    @model_validator(mode="after")
    def _validate_debug_in_production(self) -> "Settings":
        """Prevent running with debug=True in production."""
        if self.is_production and self.app_debug:
            raise ValueError("APP_DEBUG must be False in production.")
        return self

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"

    @property
    def media_root_path(self) -> Path:
        return Path(self.media_root)

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the application settings singleton.

    The @lru_cache ensures environment variables are parsed exactly once
    per process. Call `get_settings.cache_clear()` in tests when you need
    to reload settings with different environment variables.
    """
    return Settings()
