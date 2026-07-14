"""
STT (Speech-to-Text) Provider Protocol.

WHY this file exists:
    Defines the contract for speech recognition backends.
    Whisper today; future models plug in without touching services.

Protocol methods:
    transcribe()      → Convert audio file to text
    detect_language() → Identify spoken language
    is_available()    → Model readiness check
    model_info()      → Provider metadata
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class STTTranscriptionRequest:
    """Immutable value object for a transcription request."""

    audio_path: Path
    language: str | None = None   # None = auto-detect
    task: str = "transcribe"      # "transcribe" | "translate"


@dataclass(frozen=True)
class TranscriptionSegment:
    """A single timed segment from the transcription result."""

    start_seconds: float
    end_seconds: float
    text: str
    confidence: float


@dataclass(frozen=True)
class STTTranscriptionResult:
    """Result returned by any STT provider."""

    full_text: str
    language: str
    segments: list[TranscriptionSegment]
    duration_seconds: float
    transcription_time_seconds: float


@runtime_checkable
class STTProvider(Protocol):
    """Structural protocol for all speech-to-text providers."""

    async def transcribe(
        self, request: STTTranscriptionRequest
    ) -> STTTranscriptionResult:
        """
        Transcribe an audio file to text.

        Args:
            request: Immutable transcription parameters.

        Returns:
            STTTranscriptionResult with full text and timed segments.
        """
        ...

    async def detect_language(self, audio_path: Path) -> str:
        """
        Detect the spoken language in an audio file.

        Args:
            audio_path: Path to the audio file.

        Returns:
            ISO 639-1 language code (e.g. "en", "fr", "hi").
        """
        ...

    async def is_available(self) -> bool:
        """Return True if the model is loaded and ready."""
        ...

    def model_info(self) -> dict[str, str]:
        """Return provider metadata."""
        ...
