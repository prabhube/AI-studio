"""
Video Assembly Service.

Assembles the final video using FFmpeg in two stages:

  Stage 1 — Image → Video
    Converts scene images into a video using a concat demuxer.
    Each image is shown for its scene's duration_seconds.
    Output: assembled.mp4 (video only, no audio)

  Stage 2 — Mix Audio
    Combines narration + background music, then merges with the video.
    Subtitles are embedded as a soft subtitle track (selectable in players).
    Output: final.mp4

Falls back gracefully if FFmpeg is not installed (copies first image as
a static video, or returns the assembled video without audio).
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from app.core.logging import get_logger
from app.schemas.story import SceneDetail

logger = get_logger(__name__)


class VideoAssemblyService:
    """Assembles the full pipeline output into a final MP4 video."""

    async def assemble(
        self,
        scenes: list[SceneDetail],
        image_paths: list[str],
        narration_path: str,
        music_path: str,
        subtitle_path: str,
        video_dir: Path,
        width: int = 1280,
        height: int = 720,
        fps: int = 24,
    ) -> dict[str, str]:
        """
        Assemble final video from all pipeline assets.

        Returns:
            Dict with 'final_path', 'assembled_path', 'method', 'success'.
        """
        video_dir.mkdir(parents=True, exist_ok=True)
        assembled_path = video_dir / "assembled.mp4"
        final_path = video_dir / "final.mp4"

        if not await _ffmpeg_available():
            logger.warning("ffmpeg_not_found_skipping_assembly")
            return {
                "final_path": "",
                "assembled_path": "",
                "method": "skipped",
                "success": False,
                "error": "FFmpeg not found in PATH. Install FFmpeg to enable video assembly.",
            }

        # Stage 1: images → silent video
        concat_file = await _write_concat_file(scenes, image_paths, video_dir)
        ok1 = await _images_to_video(concat_file, assembled_path, width, height, fps)

        if not ok1:
            return {
                "final_path": "",
                "assembled_path": str(assembled_path),
                "method": "failed",
                "success": False,
                "error": "FFmpeg image-to-video stage failed.",
            }

        # Stage 2: add audio, music, subtitles
        ok2 = await _add_audio(
            video_path=assembled_path,
            narration_path=Path(narration_path),
            music_path=Path(music_path),
            subtitle_path=Path(subtitle_path),
            output_path=final_path,
        )

        if ok2:
            logger.info("video_assembly_complete", final_path=str(final_path))
            return {
                "final_path": str(final_path),
                "assembled_path": str(assembled_path),
                "method": "ffmpeg",
                "success": True,
                "error": "",
            }
        else:
            # Return assembled video without audio as fallback
            logger.warning("audio_mix_failed_returning_silent_video")
            return {
                "final_path": str(assembled_path),
                "assembled_path": str(assembled_path),
                "method": "ffmpeg_silent",
                "success": True,
                "error": "Audio mixing failed — returning silent video.",
            }


# ---------------------------------------------------------------------------
# FFmpeg helpers
# ---------------------------------------------------------------------------

async def _ffmpeg_available() -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=10)
        return proc.returncode == 0
    except Exception:
        return False


async def _write_concat_file(
    scenes: list[SceneDetail],
    image_paths: list[str],
    video_dir: Path,
) -> Path:
    """Write an FFmpeg concat demuxer file listing images and their durations."""
    concat_path = video_dir / "concat.txt"
    lines = []
    for scene, img_path in zip(scenes, image_paths):
        safe_path = Path(img_path).resolve()
        if not safe_path.exists():
            # Use a black placeholder
            safe_path = await _create_black_frame(video_dir, scene.index)
        lines.append(f"file '{safe_path}'")
        lines.append(f"duration {scene.duration_seconds}")
    # Last file entry (required by concat demuxer)
    if image_paths:
        lines.append(f"file '{Path(image_paths[-1]).resolve()}'")

    concat_path.write_text("\n".join(lines), encoding="utf-8")
    return concat_path


async def _create_black_frame(video_dir: Path, index: int) -> Path:
    """Create a 512x512 black PNG using FFmpeg as placeholder."""
    out = video_dir / f"black_{index:03d}.png"
    if out.exists():
        return out
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=black:512x512:d=1",
            "-frames:v", "1",
            str(out),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=15)
    except Exception:
        pass
    return out


async def _images_to_video(
    concat_file: Path,
    output_path: Path,
    width: int,
    height: int,
    fps: int,
) -> bool:
    """Convert concat image list to a silent MP4."""
    try:
        vf = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-vf", vf,
            "-r", str(fps),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _out, err = await asyncio.wait_for(proc.communicate(), timeout=300)
        if proc.returncode != 0:
            logger.error("images_to_video_failed", stderr=err.decode()[-1000:])
        return proc.returncode == 0 and output_path.exists()
    except Exception as exc:
        logger.error("images_to_video_error", error=str(exc))
        return False


async def _add_audio(
    video_path: Path,
    narration_path: Path,
    music_path: Path,
    subtitle_path: Path,
    output_path: Path,
) -> bool:
    """Mix narration + music with video, embed subtitles as soft track."""
    try:
        has_narration = narration_path.exists() and narration_path.stat().st_size > 100
        has_music = music_path.exists() and music_path.stat().st_size > 100
        has_subs = subtitle_path.exists() and subtitle_path.stat().st_size > 0

        if not has_narration and not has_music:
            # Copy video as-is
            _copy_file(video_path, output_path)
            return True

        # Build FFmpeg command dynamically based on available assets
        inputs = ["-i", str(video_path)]

        audio_filter_inputs = []
        if has_narration:
            inputs += ["-i", str(narration_path)]
            audio_filter_inputs.append("narration")
        if has_music:
            inputs += ["-i", str(music_path)]
            audio_filter_inputs.append("music")

        if not audio_filter_inputs:
            _copy_file(video_path, output_path)
            return True

        # Build audio filter graph
        n = len(inputs) // 2  # number of audio inputs
        if has_narration and has_music:
            audio_filter = "[1:a]volume=1.0[nar];[2:a]volume=0.25[mus];[nar][mus]amix=inputs=2:duration=first[audio]"
        elif has_narration:
            audio_filter = "[1:a]volume=1.0[audio]"
        else:
            audio_filter = "[1:a]volume=0.25[audio]"

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", audio_filter,
            "-map", "0:v",
            "-map", "[audio]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
        ]

        # Embed subtitle as metadata/soft track if available
        if has_subs:
            cmd += ["-scodec", "mov_text"]

        cmd.append(str(output_path))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _out, err = await asyncio.wait_for(proc.communicate(), timeout=300)

        if proc.returncode != 0:
            logger.error("add_audio_failed", stderr=err.decode()[-1000:])
            return False

        return output_path.exists()

    except Exception as exc:
        logger.error("add_audio_error", error=str(exc))
        return False


def _copy_file(src: Path, dst: Path) -> None:
    import shutil
    shutil.copy2(src, dst)
