"""
Image Reviewer Service.

Reviews generated scene images by evaluating the quality of their prompts
and metadata. Since the backend cannot directly view images (no vision model),
this review focuses on:
  - Prompt specificity and Stable Diffusion suitability
  - Consistency across scenes (color palette, style)
  - Missing elements (negative prompts, quality tags)
  - Scene-to-scene narrative flow

Returns a structured review with a score and approved flag per scene.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger
from app.providers.llm import get_llm_provider
from app.schemas.story import SceneDetail
from app.utils.llm_json import extract_json_object

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are an AI image quality reviewer for a video generation pipeline.\n"
    "You cannot see the images directly, but you can evaluate their generation prompts.\n"
    "Review the provided scene image data and return quality assessments.\n"
    "Respond with a SINGLE JSON object and NOTHING else.\n\n"
    "The JSON must have:\n"
    '  "overall_score": integer 1–10.\n'
    '  "approved": boolean — true if overall_score >= 7.\n'
    '  "scene_scores": array of {index, score, issues} for each scene.\n'
    '  "consistency_issues": array of strings — cross-scene problems.\n'
    '  "suggestions": array of strings — global improvements.\n'
    '  "ready_for_video": boolean — true if images are suitable for video assembly.\n\n'
    "Evaluate prompt quality, style consistency, subject clarity, and negative prompt effectiveness."
)


class ImageReviewerService:
    """Reviews generated image quality based on prompts and file metadata."""

    async def review(
        self,
        scenes: list[SceneDetail],
        image_paths: list[str],
        style: str = "realistic",
    ) -> dict[str, Any]:
        """
        Review all scene images and return a structured assessment.

        Args:
            scenes: Scene details with image prompts.
            image_paths: Paths to generated image files.
            style: The intended visual style.

        Returns:
            Dict with overall_score, approved, scene_scores, suggestions, etc.
        """
        settings = get_settings()
        provider = await get_llm_provider()

        # Build scene review data (include file existence, size, prompt)
        scene_data = []
        for scene, path in zip(scenes, image_paths):
            img_path = Path(path)
            scene_data.append({
                "index": scene.index,
                "title": scene.title,
                "image_prompt": scene.image_prompt,
                "negative_prompt": scene.negative_prompt,
                "camera_angle": scene.camera_angle,
                "lighting": scene.lighting,
                "file_exists": img_path.exists(),
                "file_size_kb": round(img_path.stat().st_size / 1024, 1) if img_path.exists() else 0,
            })

        user_content = (
            f"Visual style: {style}\n"
            f"Total scenes: {len(scenes)}\n\n"
            f"Scene data:\n{json.dumps(scene_data, indent=2)}"
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        logger.info("image_review_started", scene_count=len(scenes))

        raw = await provider.chat(
            messages,
            max_tokens=settings.llm.analyzer_max_tokens * 2,
            temperature=0.3,
        )

        try:
            data = extract_json_object(raw)
        except ValueError as exc:
            raise LLMProviderError(
                message="Image review returned unparseable output.",
                detail={"reason": str(exc)},
            ) from exc

        # Normalise
        result = {
            "overall_score": _clamp(data.get("overall_score"), 1, 10, 7),
            "approved": bool(data.get("approved", True)),
            "scene_scores": data.get("scene_scores") or [],
            "consistency_issues": data.get("consistency_issues") or [],
            "suggestions": data.get("suggestions") or [],
            "ready_for_video": bool(data.get("ready_for_video", True)),
            "image_count": len(image_paths),
        }

        logger.info(
            "image_review_completed",
            score=result["overall_score"],
            approved=result["approved"],
        )
        return result


def _clamp(value: Any, lo: int, hi: int, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return max(lo, min(hi, int(value)))
    return default
