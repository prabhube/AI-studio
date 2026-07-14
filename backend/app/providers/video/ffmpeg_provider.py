"""
FFmpeg Video Provider — Placeholder.

WHY: FFmpeg is the gold standard for video processing.
     It handles frame assembly, transitions, audio sync,
     subtitle burning, thumbnail extraction, and format conversion.
     It runs entirely locally with no GPU required.

Implementation notes (for Phase 7):
    - Run FFmpeg as an async subprocess via asyncio.create_subprocess_exec
    - Build FFmpeg filter graphs programmatically (not shell strings)
    - Capture stderr for progress and error reporting
    - Clean up temp files on failure
"""

from pathlib import Path

from app.core.logging import get_logger
from app.providers.base.video_provider import VideoAssemblyRequest, VideoAssemblyResult

logger = get_logger(__name__)


class FFmpegProvider:
    """VideoProvider implementation backed by FFmpeg."""

    def __init__(self, settings) -> None:
        self._settings = settings
        logger.info("ffmpeg_provider_initialized", output_dir=settings.output_dir)

    async def assemble(self, request: VideoAssemblyRequest) -> VideoAssemblyResult:
        """Assemble images + audio into video. Implementation: Phase 7."""
        raise NotImplementedError("FFmpegProvider.assemble() — Phase 7")

    async def add_subtitles(
        self, video_path: Path, subtitle_path: Path, output_path: Path
    ) -> Path:
        """Burn SRT subtitles into video. Implementation: Phase 7."""
        raise NotImplementedError("FFmpegProvider.add_subtitles() — Phase 7")

    async def extract_thumbnail(
        self, video_path: Path, timestamp_seconds: float = 0.0
    ) -> Path:
        """Extract a frame as JPEG thumbnail. Implementation: Phase 7."""
        raise NotImplementedError("FFmpegProvider.extract_thumbnail() — Phase 7")

    async def get_duration(self, video_path: Path) -> float:
        """Get video duration via ffprobe. Implementation: Phase 7."""
        raise NotImplementedError("FFmpegProvider.get_duration() — Phase 7")

    async def is_available(self) -> bool:
        """Check if ffmpeg binary is in PATH. Implementation: Phase 7."""
        return False

    def model_info(self) -> dict[str, str]:
        return {
            "name": "ffmpeg",
            "provider": "FFmpegProvider",
            "version": "6.x",
            "backend": "ffmpeg-subprocess",
        }
