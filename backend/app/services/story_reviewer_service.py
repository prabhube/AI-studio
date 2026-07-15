"""
Story Reviewer Service.

Uses the LLM to critically evaluate a generated Story and optionally produce
a revised version. Returns a StoryReview with a quality score, issues list,
and (if needed) an improved story.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger
from app.providers.llm import get_llm_provider
from app.schemas.story import Scene, Story, StoryReview, StoryReviewRequest
from app.utils.llm_json import extract_json_object

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior video content editor reviewing an AI-generated video story.\n"
    "Your job is to evaluate quality and suggest improvements.\n"
    "Respond with a SINGLE JSON object and NOTHING else.\n\n"
    "The JSON must have exactly these keys:\n"
    '  "quality_score": integer 1–10.\n'
    '  "approved": boolean — true if quality_score >= 7 and story is ready to use.\n'
    '  "issues": array of strings — specific problems found (empty if none).\n'
    '  "suggestions": array of strings — actionable improvements.\n'
    '  "revised_story": null OR a full revised story object with the same structure '
    "as the input story (only provide if quality_score < 7 and major revision needed).\n\n"
    "Evaluate for: narrative coherence, scene variety, image prompt quality, "
    "narration quality, appropriate duration, and audience fit."
)


class StoryReviewerService:
    """Evaluates and optionally revises a Story using the LLM."""

    async def review(self, request: StoryReviewRequest) -> StoryReview:
        """
        Review a Story and return a StoryReview.

        Raises:
            LLMProviderError: LLM failed or returned unparseable output.
        """
        settings = get_settings()
        provider = await get_llm_provider()

        user_content = (
            f"Original prompt: {request.original_prompt}\n\n"
            f"Story to review:\n{json.dumps(request.story.model_dump(), indent=2)}"
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        logger.info(
            "story_review_started",
            story_title=request.story.title,
            scene_count=len(request.story.scenes),
        )

        raw = await provider.chat(
            messages,
            max_tokens=settings.llm.analyzer_max_tokens * 4,
            temperature=0.3,
        )

        try:
            data = extract_json_object(raw)
        except ValueError as exc:
            logger.error("story_review_parse_failed", error=str(exc))
            raise LLMProviderError(
                message="The language model returned an unparseable review.",
                detail={"reason": str(exc)},
            ) from exc

        review = self._normalise(data, request.story)
        logger.info(
            "story_review_completed",
            quality_score=review.quality_score,
            approved=review.approved,
            issue_count=len(review.issues),
        )
        return review

    def _normalise(self, data: dict[str, Any], original: Story) -> StoryReview:
        score = _clamp_int(data.get("quality_score"), 1, 10, 5)
        approved = bool(data.get("approved", score >= 7))

        revised_story: Story | None = None
        raw_revised = data.get("revised_story")
        if isinstance(raw_revised, dict) and not approved:
            try:
                revised_story = _build_story(raw_revised, original)
            except Exception:
                revised_story = None

        return StoryReview(
            quality_score=score,
            approved=approved,
            issues=_str_list(data.get("issues")),
            suggestions=_str_list(data.get("suggestions")),
            revised_story=revised_story,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp_int(value: Any, lo: int, hi: int, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return max(lo, min(hi, int(value)))
    return default


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if isinstance(v, str) and str(v).strip()]


def _build_story(data: dict[str, Any], original: Story) -> Story:
    raw_scenes = data.get("scenes") or []
    scenes = []
    for i, item in enumerate(raw_scenes):
        if not isinstance(item, dict):
            continue
        scenes.append(
            Scene(
                index=i,
                title=(item.get("title") or f"Scene {i+1}")[:200],
                narration=(item.get("narration") or "")[:2000],
                image_prompt=(item.get("image_prompt") or "")[:1000],
                duration_seconds=_clamp_int(item.get("duration_seconds"), 1, 120, 10),
                setting=(item.get("setting") or "")[:300],
                mood=(item.get("mood") or "")[:60],
            )
        )
    if not scenes:
        scenes = original.scenes

    total = sum(s.duration_seconds for s in scenes)
    return Story(
        title=(data.get("title") or original.title)[:300],
        synopsis=(data.get("synopsis") or original.synopsis)[:1000],
        scenes=scenes,
        total_duration_seconds=max(1, total),
        style_notes=(data.get("style_notes") or original.style_notes)[:500],
        target_audience=(data.get("target_audience") or original.target_audience)[:200],
        genre=(data.get("genre") or original.genre)[:60],
    )
