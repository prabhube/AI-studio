"""
Subtitle Generator Service.

Generates SRT subtitle files from scene narration text and timing data.

No Whisper/STT required — since we have the narration text from the story
generation step, we can produce exact subtitles by distributing the text
evenly across each scene's duration.

SRT format:
  1
  00:00:00,000 --> 00:00:05,000
  Scene narration text here.

  2
  00:00:05,000 --> 00:00:12,000
  Next scene narration text.
"""

from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.schemas.story import SceneDetail

logger = get_logger(__name__)

# Maximum characters per subtitle line before wrapping
_MAX_LINE_CHARS = 60
# Maximum lines per subtitle block
_MAX_LINES = 2


class SubtitleService:
    """Generates SRT subtitle files from scene narration text."""

    async def generate(
        self,
        scenes: list[SceneDetail],
        subtitles_dir: Path,
        chars_per_second: float = 15.0,
    ) -> str:
        """
        Generate an SRT file from scene narrations and timings.

        Args:
            scenes: Scene details with narration and duration.
            subtitles_dir: Directory to write subtitles.srt into.
            chars_per_second: Reading speed for timing fine-grained blocks.

        Returns:
            Absolute path to the generated SRT file.
        """
        subtitles_dir.mkdir(parents=True, exist_ok=True)
        output_path = subtitles_dir / "subtitles.srt"

        blocks = self._build_blocks(scenes, chars_per_second)
        srt_content = self._render_srt(blocks)

        output_path.write_text(srt_content, encoding="utf-8")
        logger.info(
            "subtitles_generated",
            path=str(output_path),
            block_count=len(blocks),
        )
        return str(output_path)

    def _build_blocks(
        self,
        scenes: list[SceneDetail],
        chars_per_second: float,
    ) -> list[dict]:
        """
        Convert scenes into subtitle time blocks.

        Each scene's narration is split into chunks that each span a portion
        of the scene's duration.
        """
        blocks = []
        current_time = 0.0
        idx = 1

        for scene in scenes:
            narration = scene.narration.strip()
            if not narration:
                current_time += scene.duration_seconds
                continue

            chunks = _split_into_chunks(narration, _MAX_LINE_CHARS, _MAX_LINES)
            scene_duration = float(scene.duration_seconds)

            if not chunks:
                current_time += scene_duration
                continue

            chunk_duration = scene_duration / len(chunks)

            for chunk in chunks:
                start = current_time
                end = current_time + chunk_duration
                blocks.append({
                    "index": idx,
                    "start": start,
                    "end": end,
                    "text": chunk,
                })
                current_time = end
                idx += 1

        return blocks

    def _render_srt(self, blocks: list[dict]) -> str:
        lines = []
        for block in blocks:
            lines.append(str(block["index"]))
            lines.append(
                f"{_format_time(block['start'])} --> {_format_time(block['end'])}"
            )
            lines.append(block["text"])
            lines.append("")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_time(seconds: float) -> str:
    """Convert float seconds to SRT timestamp HH:MM:SS,mmm."""
    ms = int((seconds % 1) * 1000)
    total_s = int(seconds)
    h = total_s // 3600
    m = (total_s % 3600) // 60
    s = total_s % 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _split_into_chunks(
    text: str, max_chars: int, max_lines: int
) -> list[str]:
    """
    Split narration text into subtitle-sized chunks.

    Each chunk contains at most max_lines lines of at most max_chars characters.
    Words are not split.
    """
    words = text.split()
    chunks = []
    current_lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        if len(test_line) <= max_chars:
            current_line.append(word)
        else:
            if current_line:
                current_lines.append(" ".join(current_line))
            current_line = [word]

            if len(current_lines) >= max_lines:
                chunks.append("\n".join(current_lines))
                current_lines = []

    if current_line:
        current_lines.append(" ".join(current_line))
    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks if chunks else [text[:max_chars * max_lines]]
