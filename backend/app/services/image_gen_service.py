"""
Image Generation Service (pipeline-specific, no DB).

Generates one image per scene using:
  1. AUTOMATIC1111 Stable Diffusion WebUI API (http://localhost:7860)
  2. Fallback: PIL-generated gradient placeholder images

Images are saved as scene_000.png, scene_001.png, … in the session's
images/ directory and served via /pipeline/assets/{session_id}/images/{filename}.
"""

from __future__ import annotations

import asyncio
import base64
import io
import random
import time
from pathlib import Path

from app.core.logging import get_logger
from app.schemas.story import SceneDetail

logger = get_logger(__name__)

# SD WebUI default API endpoint
_SD_API_URL = "http://localhost:7860/sdapi/v1/txt2img"
_SD_TIMEOUT = 120  # seconds per image


# ---------------------------------------------------------------------------
# Public service
# ---------------------------------------------------------------------------

class ImageGenService:
    """Generates scene images, falling back to placeholder if SD not available."""

    async def generate_all(
        self,
        scenes: list[SceneDetail],
        images_dir: Path,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
    ) -> list[str]:
        """
        Generate one image per scene.

        Returns a list of absolute file paths in scene order.
        """
        images_dir.mkdir(parents=True, exist_ok=True)
        sd_available = await _check_sd_available()

        tasks = [
            self._generate_one(
                scene=scene,
                output_path=images_dir / f"scene_{scene.index:03d}.png",
                width=width,
                height=height,
                steps=steps,
                use_sd=sd_available,
            )
            for scene in scenes
        ]
        paths = await asyncio.gather(*tasks)
        logger.info("image_generation_done", count=len(paths), sd_used=sd_available)
        return [str(p) for p in paths]

    async def _generate_one(
        self,
        scene: SceneDetail,
        output_path: Path,
        width: int,
        height: int,
        steps: int,
        use_sd: bool,
    ) -> Path:
        if use_sd:
            try:
                return await _generate_sd(
                    prompt=scene.image_prompt,
                    negative_prompt=scene.negative_prompt,
                    output_path=output_path,
                    width=width,
                    height=height,
                    steps=steps,
                )
            except Exception as exc:
                logger.warning("sd_generation_failed", scene=scene.index, error=str(exc))

        return _generate_placeholder(
            scene_index=scene.index,
            title=scene.title,
            output_path=output_path,
            width=width,
            height=height,
        )


# ---------------------------------------------------------------------------
# SD WebUI implementation
# ---------------------------------------------------------------------------

async def _check_sd_available() -> bool:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://localhost:7860/api/v1/options")
            return r.status_code == 200
    except Exception:
        return False


async def _generate_sd(
    prompt: str,
    negative_prompt: str,
    output_path: Path,
    width: int,
    height: int,
    steps: int,
) -> Path:
    import httpx

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt or "blurry, low quality, deformed, watermark",
        "width": width,
        "height": height,
        "steps": steps,
        "cfg_scale": 7.5,
        "sampler_name": "DPM++ 2M Karras",
    }

    async with httpx.AsyncClient(timeout=_SD_TIMEOUT) as client:
        response = await client.post(_SD_API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        image_bytes = base64.b64decode(data["images"][0])

    output_path.write_bytes(image_bytes)
    logger.info("sd_image_saved", path=str(output_path))
    return output_path


# ---------------------------------------------------------------------------
# PIL placeholder fallback
# ---------------------------------------------------------------------------

# Palette of cinematic gradient pairs (start_color, end_color)
_PALETTES = [
    ((15, 20, 40), (80, 40, 120)),    # deep navy → purple
    ((10, 30, 20), (30, 100, 60)),    # dark forest green
    ((40, 10, 10), (120, 50, 20)),    # dark red → amber
    ((5, 15, 40), (20, 60, 120)),     # midnight blue
    ((30, 20, 5), (100, 80, 20)),     # dark brown → gold
    ((20, 5, 30), (70, 20, 90)),      # dark violet
    ((5, 30, 35), (15, 80, 100)),     # teal abyss
    ((35, 10, 10), (90, 30, 30)),     # crimson dark
]


def _generate_placeholder(
    scene_index: int,
    title: str,
    output_path: Path,
    width: int,
    height: int,
) -> Path:
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont

        palette = _PALETTES[scene_index % len(_PALETTES)]
        img = _gradient_image(width, height, palette[0], palette[1])

        # Add subtle noise/texture overlay
        draw = ImageDraw.Draw(img)

        # Dark vignette corners
        for i in range(min(width, height) // 4):
            alpha = int(180 * (1 - i / (min(width, height) // 4)))
            draw.rectangle([i, i, width - i, height - i], outline=(0, 0, 0, alpha))

        # Scene number badge
        badge_x, badge_y = 24, 24
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + 40, badge_y + 24],
            radius=6,
            fill=(255, 255, 255, 30),
        )
        draw.text(
            (badge_x + 8, badge_y + 4),
            f"#{scene_index + 1}",
            fill=(255, 255, 255, 200),
        )

        # Title text (centered)
        max_chars = 40
        display_title = title[:max_chars] + ("…" if len(title) > max_chars else "")
        _draw_centered_text(draw, display_title, width, height, (255, 255, 255, 220))

        # "AI Placeholder" watermark
        draw.text(
            (width - 130, height - 24),
            "SD Placeholder",
            fill=(255, 255, 255, 80),
        )

        img.save(str(output_path), "PNG")
        logger.info("placeholder_image_saved", path=str(output_path))
        return output_path

    except ImportError:
        # No PIL — write a minimal 1x1 transparent PNG
        output_path.write_bytes(_minimal_png())
        return output_path


def _gradient_image(
    width: int,
    height: int,
    start: tuple[int, int, int],
    end: tuple[int, int, int],
) -> "Image":
    from PIL import Image as PILImage

    img = PILImage.new("RGB", (width, height))
    for y in range(height):
        t = y / height
        r = int(start[0] + (end[0] - start[0]) * t)
        g = int(start[1] + (end[1] - start[1]) * t)
        b = int(start[2] + (end[2] - start[2]) * t)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    return img


def _draw_centered_text(draw, text: str, width: int, height: int, color) -> None:
    try:
        # Estimate text position without a font (basic)
        char_width, char_height = 7, 14
        x = (width - len(text) * char_width) // 2
        y = (height - char_height) // 2
        draw.text((x, y), text, fill=color)
    except Exception:
        pass


def _minimal_png() -> bytes:
    """1×1 gray PNG as absolute last fallback."""
    import struct
    import zlib

    def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = png_chunk(b"IDAT", zlib.compress(b"\x00\x80\x80\x80"))
    iend = png_chunk(b"IEND", b"")
    return header + ihdr + idat + iend
