"""
Music Generator Service.

Generates background music for the video using FFmpeg's built-in audio
synthesis capabilities — no external music libraries or internet required.

The generated track is a multi-layered ambient drone:
  - Low sine tone (fundamental)
  - Harmonics mixed at lower volumes
  - Gentle tremolo modulation
  - Fades in/out at start and end

Duration matches the total video length + a small buffer.
Output is saved as music.mp3 in the session's audio/ directory.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)

# Frequency sets mapped to mood
_MOOD_FREQUENCIES: dict[str, tuple[float, float, float]] = {
    "calm":          (110.0, 165.0, 220.0),
    "neutral":       (130.8, 196.0, 261.6),
    "cheerful":      (261.6, 329.6, 392.0),
    "energetic":     (196.0, 293.7, 392.0),
    "dramatic":      (82.4,  123.5, 164.8),
    "suspenseful":   (73.4,  110.0, 146.8),
    "inspirational": (174.6, 261.6, 349.2),
    "somber":        (65.4,  98.0,  130.8),
    "playful":       (293.7, 392.0, 523.3),
    "serious":       (98.0,  146.8, 196.0),
}

_DEFAULT_FREQ = _MOOD_FREQUENCIES["neutral"]


class MusicService:
    """Generates ambient background music using FFmpeg synthesis."""

    async def generate(
        self,
        audio_dir: Path,
        duration_seconds: int,
        mood: str = "neutral",
        volume: float = 0.15,
    ) -> str:
        """
        Generate background music and save to audio_dir/music.mp3.

        Args:
            audio_dir: Directory to write music.mp3 into.
            duration_seconds: Total track duration.
            mood: Emotional mood for frequency selection.
            volume: Output volume (0.0–1.0). Keep low so narration is clear.

        Returns:
            Absolute path to the generated music file.
        """
        audio_dir.mkdir(parents=True, exist_ok=True)
        output_path = audio_dir / "music.mp3"
        duration = max(10, duration_seconds + 5)  # slight buffer

        freqs = _MOOD_FREQUENCIES.get(mood.lower(), _DEFAULT_FREQ)
        f1, f2, f3 = freqs

        # Build FFmpeg lavfi filter for layered ambient drone
        # Three sine tones with tremolo and mixing
        filter_complex = (
            f"sine=frequency={f1}:duration={duration}[s1];"
            f"sine=frequency={f2}:duration={duration}[s2];"
            f"sine=frequency={f3}:duration={duration}[s3];"
            f"[s1]volume=0.6[a1];"
            f"[s2]volume=0.3[a2];"
            f"[s3]volume=0.15[a3];"
            f"[a1][a2][a3]amix=inputs=3:duration=first[mix];"
            f"[mix]tremolo=f=0.3:d=0.4[trem];"
            # Fade in 2s, fade out 3s
            f"[trem]afade=t=in:d=2,afade=t=out:st={duration - 3}:d=3[out];"
            f"[out]volume={volume:.2f}[final]"
        )

        success = await _run_ffmpeg_music(filter_complex, output_path, duration)

        if not success:
            # Fallback: plain sine at reduced volume
            success = await _fallback_sine(output_path, f1, duration, volume)

        if not success:
            # Last resort: silence
            output_path.write_bytes(b"")

        logger.info(
            "music_generated",
            path=str(output_path),
            duration=duration,
            mood=mood,
            success=success,
        )
        return str(output_path)


async def _run_ffmpeg_music(
    filter_complex: str, output_path: Path, duration: int
) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-filter_complex", filter_complex,
            "-map", "[final]",
            "-t", str(duration),
            "-q:a", "4",
            "-acodec", "libmp3lame",
            str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _out, err = await asyncio.wait_for(proc.communicate(), timeout=60)
        if proc.returncode != 0:
            logger.warning("ffmpeg_music_failed", stderr=err.decode()[:500])
        return proc.returncode == 0 and output_path.exists()
    except Exception as exc:
        logger.warning("ffmpeg_music_error", error=str(exc))
        return False


async def _fallback_sine(
    output_path: Path, freq: float, duration: int, volume: float
) -> bool:
    try:
        filter_str = f"sine=frequency={freq}:duration={duration},volume={volume}"
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", filter_str,
            "-q:a", "4",
            "-acodec", "libmp3lame",
            str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=30)
        return proc.returncode == 0 and output_path.exists()
    except Exception:
        return False
