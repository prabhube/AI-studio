"""
Piper TTS Provider — Placeholder.

WHY: Piper is a fast, local, neural TTS engine by Rhasspy.
     It runs entirely offline, produces natural-sounding speech,
     and supports multiple English and multilingual voices.

Implementation notes (for Phase 5):
    - Run piper CLI as subprocess: piper --model voice.onnx
    - Or use the piper-tts Python package directly
    - Save .wav to settings.tts.output_dir / UUID.wav
    - Convert to mp3 using FFmpeg if output_format="mp3"
"""

from pathlib import Path

from app.core.logging import get_logger
from app.providers.base.tts_provider import TTSSynthesisRequest, TTSSynthesisResult

logger = get_logger(__name__)


class PiperProvider:
    """TTSProvider implementation backed by Piper TTS."""

    def __init__(self, settings) -> None:
        self._settings = settings
        logger.info("piper_provider_initialized", model_path=settings.model_path)

    async def synthesize(self, request: TTSSynthesisRequest) -> TTSSynthesisResult:
        """Synthesize speech. Implementation: Phase 5."""
        raise NotImplementedError("PiperProvider.synthesize() — Phase 5")

    async def list_voices(self) -> list[str]:
        """Return available Piper voice IDs. Implementation: Phase 5."""
        raise NotImplementedError("PiperProvider.list_voices() — Phase 5")

    async def is_available(self) -> bool:
        return False

    def model_info(self) -> dict[str, str]:
        return {
            "name": "piper",
            "provider": "PiperProvider",
            "version": "1.0",
            "backend": "piper-tts",
            "model_path": self._settings.model_path,
        }
