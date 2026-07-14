"""
Video Provider Protocol.

WHY this file exists:
    Defines the contract for video assembly backends.
    FFmpeg today; future GPU-accelerated assemblers tomorrow.

    The VideoProvider is responsible for the final assembly step:
    combining images, audio, transitions, and subtitles into
    a complete video file.

Protocol methods:
    assemble()           → Combine images + audio into video
    add_subtitles()      → Burn subtitles into a video
    extract_thumbnail()  → Pull a single frame from video
    get_duration()       → Get video duration in seconds
    is_available()       → FFmpeg readiness check
    model_info()         → Provider metadata
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable


@dataclass(frozen=True)
class VideoAssemblyRequest:
    """
    Immutable value object describing a video assembly job.

    WHY: One object containing all the inputs prevents partial
         state bugs — you can't forget to set audio_path.
    """

    image_paths: list[Path]             # Ordered list of frames
    audio_path: Path                    # Narration audio
    output_path: Path                   # Where to save the result
    frame_duration_seconds: float = 3.0 # How long each image shows
    transition: Literal[
        "none", "fade", "slide_left", "slide_right", "zoom_in"
    ] = "fade"
    fps: int = 30
    resolution: tuple[int, int] = field(default=(1920, 1080))


@dataclass(frozen=True)
class VideoAssemblyResult:
    """Result returned by any video provider."""

    file_path: Path
    duration_seconds: float
    resolution: tuple[int, int]
    fps: int
    file_size_bytes: int
    assembly_time_seconds: float


@runtime_checkable
class VideoProvider(Protocol):
    """Structural protocol for all video assembly providers."""

    async def assemble(
        self, request: VideoAssemblyRequest
    ) -> VideoAssemblyResult:
        """
        Assemble images and audio into a complete video file.

        Args:
            request: Immutable assembly parameters.

        Returns:
            VideoAssemblyResult with path and metadata of the output.
        """
        ...

    async def add_subtitles(
        self,
        video_path: Path,
        subtitle_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Burn subtitles (SRT format) into an existing video.

        Args:
            video_path:    Source video.
            subtitle_path: Path to .srt subtitle file.
            output_path:   Where to save the resulting video.

        Returns:
            Path to the video with burned-in subtitles.
        """
        ...

    async def extract_thumbnail(
        self, video_path: Path, timestamp_seconds: float = 0.0
    ) -> Path:
        """
        Extract a single frame from a video as a JPEG thumbnail.

        Args:
            video_path:          Path to the source video.
            timestamp_seconds:   Position in the video to extract.

        Returns:
            Path to the extracted thumbnail image.
        """
        ...

    async def get_duration(self, video_path: Path) -> float:
        """Return the video duration in seconds."""
        ...

    async def is_available(self) -> bool:
        """Return True if FFmpeg is installed and accessible."""
        ...

    def model_info(self) -> dict[str, str]:
        """Return provider metadata."""
        ...
