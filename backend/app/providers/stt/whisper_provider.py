"""
Whisper STT Provider — Placeholder.

WHY: OpenAI Whisper is the best open-source speech recognition model.
     The "base" model runs well on CPU; "large" requires a GPU.
     It handles 99 languages and produces timed segments.

Implementation notes (for Phase 6):
    - Load via openai-whisper: whisper.load_model("base")
    - Run in asyncio.ThreadPoolExecutor (Whisper is synchronous)
    - Return timed segments for subtitle generation
    - Output SRT files alongside the transcript
"""

from pathlib import Path

from app.core.logging import get_logger
from app.providers.base.stt_provider import (
    STTTranscriptionRequest,
    STTTranscriptionResult,
)

logger = get_logger(__name__)


class WhisperProvider:
    """STTProvider implementation backed by OpenAI Whisper."""

    def __init__(self, settings) -> None:
        self._settings = settings
        self._model = None  # Loaded in Phase 6
        logger.info("whisper_provider_initialized", model_size=settings.model_size)

    async def transcribe(
        self, request: STTTranscriptionRequest
    ) -> STTTranscriptionResult:
        """Transcribe audio to text. Implementation: Phase 6."""
        raise NotImplementedError("WhisperProvider.transcribe() — Phase 6")

    async def detect_language(self, audio_path: Path) -> str:
        """Detect spoken language. Implementation: Phase 6."""
        raise NotImplementedError("WhisperProvider.detect_language() — Phase 6")

    async def is_available(self) -> bool:
        return False

    def model_info(self) -> dict[str, str]:
        return {
            "name": "whisper",
            "provider": "WhisperProvider",
            "version": self._settings.model_size,
            "backend": "openai-whisper",
        }
