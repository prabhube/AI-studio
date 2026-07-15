"""
Scene Generator Service.

Expands a Story's scenes into rich SceneDetail objects with:
  - Detailed image prompts (with negative prompts)
  - Camera angle and lighting direction
  - Characters present in each scene

These SceneDetail objects feed directly into the image generation step.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger
from app.providers.llm import get_llm_provider
from app.schemas.story import Scene, SceneDetail, SceneGenerateRequest
from app.utils.llm_json import extract_json_object

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert AI art director for a video generation studio.\n"
    "Expand basic scene descriptions into detailed visual direction for Stable Diffusion.\n"
    "Respond with a SINGLE JSON object and NOTHING else.\n\n"
    'The JSON must have: "scenes": array of expanded scene objects.\n\n'
    "Each scene object must have:\n"
    '  "index": integer (same as input).\n'
    '  "title": string.\n'
    '  "narration": string (keep from input, do not change).\n'
    '  "image_prompt": string — detailed Stable Diffusion prompt with:\n'
    "    * Subject description\n"
    "    * Setting/background\n"
    "    * Lighting (e.g. 'golden hour', 'dramatic rim lighting')\n"
    "    * Camera angle (e.g. 'low angle shot', 'bird\'s eye view')\n"
    "    * Quality tags (e.g. '4k, photorealistic, cinematic, sharp focus')\n"
    '  "negative_prompt": string — what to EXCLUDE (e.g. "blurry, low quality, '
    'deformed, watermark, text").\n'
    '  "duration_seconds": integer (keep from input).\n'
    '  "setting": string — detailed environment description.\n'
    '  "mood": string.\n'
    '  "camera_angle": string — specific camera direction.\n'
    '  "lighting": string — lighting description.\n'
    '  "characters_present": array of character name strings.\n\n'
    "Make image prompts rich, specific, and optimised for high-quality AI generation."
)


class SceneService:
    """Expands Story scenes into detailed SceneDetail objects."""

    async def generate(self, request: SceneGenerateRequest) -> list[SceneDetail]:
        """
        Expand story scenes into detailed visual directions.

        Raises:
            LLMProviderError: LLM failed or returned unparseable output.
        """
        settings = get_settings()
        provider = await get_llm_provider()

        scenes_json = json.dumps(
            [s.model_dump() for s in request.story.scenes], indent=2
        )
        user_content = (
            f"Story: {request.story.title}\n"
            f"Visual style: {request.style}\n"
            f"Synopsis: {request.story.synopsis}\n\n"
            f"Scenes to expand:\n{scenes_json}"
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        logger.info(
            "scene_generation_started",
            story_title=request.story.title,
            scene_count=len(request.story.scenes),
        )

        raw = await provider.chat(
            messages,
            max_tokens=settings.llm.analyzer_max_tokens * 4,
            temperature=0.6,
        )

        try:
            data = extract_json_object(raw)
        except ValueError as exc:
            logger.error("scene_generation_parse_failed", error=str(exc))
            raise LLMProviderError(
                message="The language model returned unparseable scene details.",
                detail={"reason": str(exc)},
            ) from exc

        details = self._normalise(data, request.story.scenes)
        logger.info("scene_generation_completed", count=len(details))
        return details

    def _normalise(
        self, data: dict[str, Any], original_scenes: list[Scene]
    ) -> list[SceneDetail]:
        raw_list = data.get("scenes") or []
        details: list[SceneDetail] = []

        for i, orig in enumerate(original_scenes):
            raw = raw_list[i] if i < len(raw_list) and isinstance(raw_list[i], dict) else {}
            details.append(
                SceneDetail(
                    index=i,
                    title=_s(raw.get("title"), 200) or orig.title,
                    narration=_s(raw.get("narration"), 2000) or orig.narration,
                    image_prompt=_s(raw.get("image_prompt"), 1000) or orig.image_prompt,
                    negative_prompt=_s(raw.get("negative_prompt"), 500)
                    or "blurry, low quality, deformed, watermark, text, ugly",
                    duration_seconds=_int(raw.get("duration_seconds"), 1, 120, orig.duration_seconds),
                    setting=_s(raw.get("setting"), 300) or orig.setting,
                    mood=_s(raw.get("mood"), 60) or orig.mood,
                    camera_angle=_s(raw.get("camera_angle"), 60) or "",
                    lighting=_s(raw.get("lighting"), 120) or "",
                    characters_present=[
                        str(c).strip()
                        for c in (raw.get("characters_present") or [])
                        if isinstance(c, str) and str(c).strip()
                    ],
                )
            )
        return details


def _s(value: Any, max_len: int) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def _int(value: Any, lo: int, hi: int, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return max(lo, min(hi, int(value)))
    return default
