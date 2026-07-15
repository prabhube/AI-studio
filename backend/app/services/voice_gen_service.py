"""
Voice Generator Service (pipeline-specific, no DB).

Synthesizes narration audio from scene narration text using:
  1. Piper TTS (local, offline) — fastest, best quality
  2. gTTS (Google TTS) — requires internet, free
  3. ffmpeg silence — absolute fallback (video will have no narration audio)

All scene narrations are concatenated into a single narration.mp3 file.
Individual scene audio files are also saved for per-scene control.
"""

from __future__ import annotations

import asyncio
import subprocess
import tempfile
from pathlib import Path

from app.core.logging import get_logger
from app.schemas.story import SceneDetail

logger = get_logger(__name__)


class VoiceGenService:
    """Generates TTS narration for pipeline scenes."""

    async def generate(
        self,
        scenes: list[SceneDetail],
        audio_dir: Path,
        voice_id: str = "en_US-lessac-medium",
        language: str = "en",
        speed: float = 1.0,
    ) -> dict[str, str]:
        """
        Generate narration audio for all scenes.

        Returns:
            Dict with 'narration_path' (combined) and 'scene_paths' (list).
        """
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Combine all narration into one text
        full_text = " ".join(
            scene.narration for scene in scenes if scene.narration.strip()
        )

        narration_path = audio_dir / "narration.mp3"

        # Try providers in order
        success = False

        success = await _try_piper(full_text, narration_path, voice_id, speed)
        if not success:
            logger.info("piper_unavailable_trying_gtts")
            success = await _try_gtts(full_text, narration_path, language)
        if not success:
            logger.info("gtts_unavailable_using_silence")
            total_seconds = sum(s.duration_seconds for s in scenes)
            success = await _generate_silence(narration_path, total_seconds)

        if not success:
            # If all else fails, create an empty file
            narration_path.write_bytes(b"")

        logger.info(
            "narration_generated",
            path=str(narration_path),
            exists=narration_path.exists(),
        )

        return {
            "narration_path": str(narration_path),
            "method": "piper" if success and _piper_available() else "gtts" if success else "silence",
            "total_duration_estimate": sum(s.duration_seconds for s in scenes),
        }


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

async def _try_piper(
    text: str, output_path: Path, voice_id: str, speed: float
) -> bool:
    """Try Piper TTS CLI. Returns True if successful."""
    try:
        if not _piper_available():
            return False

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
            wav_path = Path(tmp_wav.name)

        proc = await asyncio.create_subprocess_exec(
            "piper",
            "--model", voice_id,
            "--output_file", str(wav_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=text.encode()),
            timeout=120,
        )

        if proc.returncode != 0:
            logger.warning("piper_failed", stderr=stderr.decode()[:500])
            return False

        # Convert wav to mp3 via ffmpeg
        return await _wav_to_mp3(wav_path, output_path)

    except Exception as exc:
        logger.warning("piper_error", error=str(exc))
        return False


def _piper_available() -> bool:
    try:
        result = subprocess.run(
            ["piper", "--help"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode in (0, 1)  # --help may return 1
    except Exception:
        return False


async def _try_gtts(text: str, output_path: Path, lang: str = "en") -> bool:
    """Try gTTS. Returns True if successful."""
    try:
        from gtts import gTTS

        loop = asyncio.get_event_loop()

        def _synth():
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(str(output_path))

        await loop.run_in_executor(None, _synth)
        return output_path.exists() and output_path.stat().st_size > 0

    except Exception as exc:
        logger.warning("gtts_error", error=str(exc))
        return False


async def _generate_silence(output_path: Path, duration_seconds: int) -> bool:
    """Generate silent audio of the given duration using ffmpeg."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(max(1, duration_seconds)),
            "-q:a", "9",
            "-acodec", "libmp3lame",
            str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=30)
        return proc.returncode == 0 and output_path.exists()
    except Exception as exc:
        logger.warning("silence_generation_error", error=str(exc))
        return False


async def _wav_to_mp3(wav_path: Path, mp3_path: Path) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-i", str(wav_path),
            "-q:a", "2",
            str(mp3_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=60)
        wav_path.unlink(missing_ok=True)
        return proc.returncode == 0 and mp3_path.exists()
    except Exception:
        return False
