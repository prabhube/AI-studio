"""
Scene Reviewer Service.

Reviews generated SceneDetail objects to ensure:
- Image prompts are clear and suitable for Stable Diffusion
- Narration is coherent and appropriately timed
- Scenes flow well together as a video

Returns a SceneReview with score, issues, and optionally revised scenes.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger
from app.providers.llm import get_llm_provider
from app.schemas.story import SceneDetail, SceneReview, SceneReviewRequest
from app.utils.llm_json import extract_json_object

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a quality-control reviewer for an AI video generation studio.\n"
    "Review the provided scenes and evaluate their readiness for image + video generation.\n"
    "Respond with a SINGLE JSON object and NOTHING else.\n\n"
    "The JSON must have exactly:\n"
    '  "quality_score": integer 1–10.\n'
    '  "approved": boolean — true if score >= 7.\n'
    '  "issues": array of strings — specific problems found.\n'
    '  "suggestions": array of strings — improvements to make.\n'
    '  "revised_scenes": null OR array of corrected scene objects (same structure as input).\n\n'
    "Focus on: image prompt specificity, negative prompt effectiveness, "
    "narration length vs duration, scene-to-scene visual consistency, "
    "and Stable Diffusion generation suitability."
)


class SceneReviewerService:
    """Reviews scene details for image generation readiness."""

    async def review(self, request: SceneReviewRequest) -> SceneReview:
        """
        Review scene details and return a SceneReview.

        Raises:
            LLMProviderError: LLM failed or returned unparseable output.
        """
        settings = get_settings()
        provider = await get_llm_provider()

        user_content = (
            f"Story: {request.story_title}\n\n"
            f"Scenes:\n{json.dumps([s.model_dump() for s in request.scenes], indent=2)}"
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        logger.info(
            "scene_review_started",
            story_title=request.story_title,
            scene_count=len(request.scenes),
        )

        raw = await provider.chat(
            messages,
            max_tokens=settings.llm.analyzer_max_tokens * 4,
            temperature=0.3,
        )

        try:
            data = extract_json_object(raw)
        except ValueError as exc:
            raise LLMProviderError(
                message="Scene review returned unparseable output.",
                detail={"reason": str(exc)},
            ) from exc

        review = self._normalise(data, request.scenes)
        logger.info(
            "scene_review_completed",
            quality_score=review.quality_score,
            approved=review.approved,
        )
        return review

    def _normalise(
        self, data: dict[str, Any], original: list[SceneDetail]
    ) -> SceneReview:
        score = _clamp(data.get("quality_score"), 1, 10, 5)
        approved = bool(data.get("approved", score >= 7))

        revised: list[SceneDetail] | None = None
        raw_revised = data.get("revised_scenes")
        if isinstance(raw_revised, list) and not approved:
            try:
                revised = _build_scenes(raw_revised, original)
            except Exception:
                revised = None

        return SceneReview(
            quality_score=score,
            approved=approved,
            issues=_str_list(data.get("issues")),
            suggestions=_str_list(data.get("suggestions")),
            revised_scenes=revised,
        )


def _clamp(value: Any, lo: int, hi: int, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return max(lo, min(hi, int(value)))
    return default


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if isinstance(v, str) and str(v).strip()]


def _build_scenes(raw_list: list[Any], originals: list[SceneDetail]) -> list[SceneDetail]:
    scenes = []
    for i, orig in enumerate(originals):
        raw = raw_list[i] if i < len(raw_list) and isinstance(raw_list[i], dict) else {}
        scenes.append(
            SceneDetail(
                index=i,
                title=(raw.get("title") or orig.title)[:200],
                narration=(raw.get("narration") or orig.narration)[:2000],
                image_prompt=(raw.get("image_prompt") or orig.image_prompt)[:1000],
                negative_prompt=(raw.get("negative_prompt") or orig.negative_prompt)[:500],
                duration_seconds=_clamp(raw.get("duration_seconds"), 1, 120, orig.duration_seconds),
                setting=(raw.get("setting") or orig.setting)[:300],
                mood=(raw.get("mood") or orig.mood)[:60],
                camera_angle=(raw.get("camera_angle") or orig.camera_angle)[:60],
                lighting=(raw.get("lighting") or orig.lighting)[:120],
                characters_present=raw.get("characters_present") or orig.characters_present,
            )
        )
    return scenes
