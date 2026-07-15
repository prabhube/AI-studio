"""
Story Generator Service.

Turns a structured PromptAnalysis into a complete Story with ordered Scenes.
Each scene has narration text and a Stable Diffusion image prompt.

Uses the configured LLM provider (Gemma/Llama) with a strict JSON instruction
so the output is machine-parseable. Follows the same self-healing pattern as
PromptAnalyzerService.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import InvalidInputError, LLMProviderError
from app.core.logging import get_logger
from app.providers.llm import get_llm_provider
from app.schemas.prompt import PromptAnalysis
from app.schemas.story import Scene, Story, StoryGenerateRequest
from app.utils.llm_json import extract_json_object

logger = get_logger(__name__)

_MAX_SCENE_TITLE = 200
_MAX_NARRATION = 2000
_MAX_IMAGE_PROMPT = 1000
_MAX_SETTING = 300
_MAX_MOOD = 60
_DEFAULT_SCENE_DURATION = 10


def _make_system_prompt(num_scenes: int, analysis: PromptAnalysis) -> str:
    return (
        "You are a professional video scriptwriter for an AI video generation studio.\n"
        "Given a structured video brief, write a complete story with scenes.\n"
        "Respond with a SINGLE JSON object and NOTHING else — no markdown, no prose.\n\n"
        "The JSON must have exactly these keys:\n"
        '  "title": string — catchy video title.\n'
        '  "synopsis": string — one paragraph overview (max 1000 chars).\n'
        '  "genre": string — e.g. "documentary", "narrative", "explainer".\n'
        '  "style_notes": string — visual style guidance.\n'
        f'  "scenes": array of exactly {num_scenes} scene objects.\n\n'
        "Each scene object must have:\n"
        '  "index": integer (0-based).\n'
        '  "title": string — short scene title.\n'
        '  "narration": string — voiceover text for this scene (2–4 sentences).\n'
        '  "image_prompt": string — Stable Diffusion prompt describing the visual '
        "(style, subject, lighting, camera angle, quality tags like "
        '"4k, photorealistic, cinematic lighting").\n'
        '  "duration_seconds": integer between 5 and 30.\n'
        '  "setting": string — location or environment.\n'
        '  "mood": string — emotional tone of this scene.\n\n'
        f"Brief:\n{json.dumps(analysis.model_dump(), indent=2)}\n\n"
        "Make the story coherent, engaging, and appropriate for the target audience. "
        "Ensure each image_prompt is rich and specific for image generation."
    )


class StoryService:
    """Generates a full story from a PromptAnalysis using the LLM."""

    async def generate(self, request: StoryGenerateRequest) -> Story:
        """
        Generate a Story from a PromptAnalysis.

        Raises:
            InvalidInputError: The analysis has no topic.
            LLMProviderError: LLM failed or returned unparseable output.
        """
        if not request.analysis.topic.strip():
            raise InvalidInputError("Prompt analysis must have a topic.")

        settings = get_settings()
        provider = await get_llm_provider()

        system_prompt = _make_system_prompt(request.num_scenes, request.analysis)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Generate a {request.num_scenes}-scene video story about: "
                    f"{request.analysis.topic}"
                ),
            },
        ]

        logger.info(
            "story_generation_started",
            topic=request.analysis.topic,
            num_scenes=request.num_scenes,
            provider=provider.model_info().get("name"),
        )

        raw = await provider.chat(
            messages,
            max_tokens=settings.llm.analyzer_max_tokens * 4,
            temperature=0.7,
        )

        try:
            data = extract_json_object(raw)
        except ValueError as exc:
            logger.error("story_generation_parse_failed", error=str(exc))
            raise LLMProviderError(
                message="The language model returned an unparseable story.",
                detail={"reason": str(exc)},
            ) from exc

        story = self._normalise(data, request)
        logger.info(
            "story_generation_completed",
            title=story.title,
            scene_count=len(story.scenes),
            total_duration=story.total_duration_seconds,
        )
        return story

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalise(self, data: dict[str, Any], request: StoryGenerateRequest) -> Story:
        raw_scenes = data.get("scenes") or []
        scenes = self._normalise_scenes(raw_scenes, request.num_scenes, request.analysis)
        total_duration = sum(s.duration_seconds for s in scenes)

        return Story(
            title=_s(data.get("title"), _MAX_SCENE_TITLE) or request.analysis.topic,
            synopsis=_s(data.get("synopsis"), 1000) or "",
            genre=_s(data.get("genre"), 60) or "narrative",
            style_notes=_s(data.get("style_notes"), 500) or request.analysis.style,
            target_audience=request.analysis.audience,
            scenes=scenes,
            total_duration_seconds=max(1, total_duration),
        )

    def _normalise_scenes(
        self,
        raw: list[Any],
        num_scenes: int,
        analysis: PromptAnalysis,
    ) -> list[Scene]:
        scenes: list[Scene] = []
        for i, item in enumerate(raw[:num_scenes]):
            if not isinstance(item, dict):
                continue
            scenes.append(
                Scene(
                    index=i,
                    title=_s(item.get("title"), _MAX_SCENE_TITLE) or f"Scene {i + 1}",
                    narration=_s(item.get("narration"), _MAX_NARRATION) or "",
                    image_prompt=_s(item.get("image_prompt"), _MAX_IMAGE_PROMPT)
                    or f"{analysis.style} style, {analysis.topic}",
                    duration_seconds=_int(item.get("duration_seconds"), 5, 30, _DEFAULT_SCENE_DURATION),
                    setting=_s(item.get("setting"), _MAX_SETTING) or "",
                    mood=_s(item.get("mood"), _MAX_MOOD) or analysis.mood,
                )
            )
        # Pad with placeholder scenes if LLM returned fewer than requested
        while len(scenes) < num_scenes:
            i = len(scenes)
            scenes.append(
                Scene(
                    index=i,
                    title=f"Scene {i + 1}",
                    narration="",
                    image_prompt=f"{analysis.style} style, {analysis.topic}",
                    duration_seconds=_DEFAULT_SCENE_DURATION,
                    setting="",
                    mood=analysis.mood,
                )
            )
        return scenes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s(value: Any, max_len: int) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]


def _int(value: Any, lo: int, hi: int, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return max(lo, min(hi, int(value)))
    if isinstance(value, str):
        digits = "".join(c for c in value if c.isdigit())
        if digits:
            return max(lo, min(hi, int(digits)))
    return default
