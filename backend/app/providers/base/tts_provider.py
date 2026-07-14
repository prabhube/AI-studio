"""
TTS (Text-to-Speech) Provider Protocol.

WHY this file exists:
    Defines the contract for voice synthesis backends.
    Piper TTS today; Coqui, Bark, or a future model tomorrow.
    All calling code type-hints against TTSProvider, never PiperProvider.

Protocol methods:
    synthesize()      → Convert text to an audio file
    list_voices()     → Available voice IDs
    is_available()    → Model readiness check
    model_info()      → Provider metadata
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class TTSSynthesisRequest:
    """
    Immutable value object for a TTS synthesis request.
    """

    text: str
    voice_id: str = "en_US-lessac-medium"
    speed: float = 1.0           # 1.0 = normal speed
    output_format: str = "wav"   # wav | mp3 | ogg


@dataclass(frozen=True)
class TTSSynthesisResult:
    """Result returned by any TTS provider."""

    file_path: Path
    duration_seconds: float
    voice_id: str
    output_format: str
    synthesis_time_seconds: float


@runtime_checkable
class TTSProvider(Protocol):
    """Structural protocol for all text-to-speech providers."""

    async def synthesize(self, request: TTSSynthesisRequest) -> TTSSynthesisResult:
        """
        Convert text to speech and save to disk.

        Args:
            request: Immutable synthesis parameters.

        Returns:
            TTSSynthesisResult with path to the audio file.
        """
        ...

    async def list_voices(self) -> list[str]:
        """
        Return a list of available voice IDs for this provider.

        Returns:
            List of voice ID strings (e.g. ["en_US-lessac-medium", ...]).
        """
        ...

    async def is_available(self) -> bool:
        """Return True if the model is loaded and ready."""
        ...

    def model_info(self) -> dict[str, str]:
        """Return provider metadata."""
        ...
