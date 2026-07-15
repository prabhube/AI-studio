"""
Character Generator Service.

Takes characters extracted by the Prompt Analyzer and generates full
CharacterSheet objects with:
  - Detailed physical appearance for image generation
  - Stable Diffusion-optimised character prompts
  - Personality traits (for narration voice selection)
  - Voice description (for TTS configuration)
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import LLMProviderError
from app.core.logging import get_logger
from app.providers.llm import get_llm_provider
from app.schemas.story import CharacterGenRequest, CharacterSheet
from app.utils.llm_json import extract_json_object

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a character designer for an AI video generation studio.\n"
    "Create detailed character sheets for each character provided.\n"
    "Respond with a SINGLE JSON object and NOTHING else.\n\n"
    'The JSON must have: "characters": array of character sheet objects.\n\n'
    "Each character sheet must have:\n"
    '  "name": string — character name.\n'
    '  "role": string — narrative role (e.g. "protagonist", "narrator").\n'
    '  "appearance": string — detailed physical description (age, build, hair, '
    "eyes, clothing, distinguishing features).\n"
    '  "image_prompt": string — Stable Diffusion optimised prompt for generating '
    "this character (include style, quality tags like '4k, detailed portrait, "
    "photorealistic').\n"
    '  "personality": string — key personality traits affecting story tone.\n'
    '  "voice_description": string — voice characteristics for TTS '
    '(e.g. "warm, authoritative male voice, mid-40s").\n\n'
    "Make character designs consistent, vivid, and suitable for AI image generation."
)


class CharacterService:
    """Generates full CharacterSheet objects from prompt analysis characters."""

    async def generate(self, request: CharacterGenRequest) -> list[CharacterSheet]:
        """
        Generate character sheets for all characters in the analysis.

        Returns an empty list if no characters are present.

        Raises:
            LLMProviderError: LLM failed or returned unparseable output.
        """
        if not request.analysis.characters:
            return []

        settings = get_settings()
        provider = await get_llm_provider()

        chars_json = json.dumps(
            [c.model_dump() for c in request.analysis.characters], indent=2
        )
        user_content = (
            f"Story topic: {request.analysis.topic}\n"
            f"Visual style: {request.analysis.style}\n"
            f"Mood: {request.analysis.mood}\n\n"
            f"Characters to develop:\n{chars_json}"
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        logger.info(
            "character_generation_started",
            character_count=len(request.analysis.characters),
        )

        raw = await provider.chat(
            messages,
            max_tokens=settings.llm.analyzer_max_tokens * 3,
            temperature=0.7,
        )

        try:
            data = extract_json_object(raw)
        except ValueError as exc:
            raise LLMProviderError(
                message="Character generation returned unparseable output.",
                detail={"reason": str(exc)},
            ) from exc

        sheets = self._normalise(data, request)
        logger.info("character_generation_completed", count=len(sheets))
        return sheets

    def _normalise(
        self, data: dict[str, Any], request: CharacterGenRequest
    ) -> list[CharacterSheet]:
        raw_chars = data.get("characters") or []
        sheets: list[CharacterSheet] = []

        for i, orig_char in enumerate(request.analysis.characters):
            raw = raw_chars[i] if i < len(raw_chars) and isinstance(raw_chars[i], dict) else {}
            sheets.append(
                CharacterSheet(
                    name=_s(raw.get("name"), 120) or orig_char.name,
                    role=_s(raw.get("role"), 60) or (orig_char.role or ""),
                    appearance=_s(raw.get("appearance"), 500)
                    or (orig_char.description or f"A character named {orig_char.name}"),
                    image_prompt=_s(raw.get("image_prompt"), 500)
                    or f"detailed portrait of {orig_char.name}, {request.analysis.style} style, 4k",
                    personality=_s(raw.get("personality"), 300) or "",
                    voice_description=_s(raw.get("voice_description"), 200)
                    or request.analysis.voice,
                )
            )
        return sheets


def _s(value: Any, max_len: int) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]
