"""
Prompt Analyzer Service.

Responsibilities:
  - Turn a free-form, natural-language video prompt into a structured
    PromptAnalysis (topic, audience, mood, characters, style, camera,
    duration, language, voice) that downstream pipeline stages consume.

Design decisions:
  - Model-agnostic: depends only on the ``LLMProvider`` protocol via
    ``get_llm_provider()``. Swapping Gemma ↔ Llama (or any future model)
    requires zero changes here — that is the whole point of the abstraction.
  - Near-deterministic: uses a low temperature and a strict JSON instruction
    so the extracted brief is stable and machine-parseable.
  - Self-healing parsing: local models occasionally wrap JSON in prose or omit
    keys. The service extracts the JSON object and normalises every field
    (defaults, clamping, controlled vocabularies, truncation) before schema
    validation, so callers always receive a fully-populated, valid
    ``PromptAnalysis`` — or a clear domain error.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import InvalidInputError, LLMProviderError
from app.core.logging import get_logger
from app.providers.llm import get_llm_provider
from app.schemas.prompt import PromptAnalysis, PromptCharacter
from app.utils.llm_json import extract_json_object

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Controlled vocabularies
#
# These steer the model toward a stable set of values and let the service snap
# free-form output onto terms the generation pipeline understands. The first
# entry of each tuple doubles as the safe default.
# ---------------------------------------------------------------------------

MOODS: tuple[str, ...] = (
    "neutral", "calm", "cheerful", "energetic", "dramatic",
    "suspenseful", "inspirational", "somber", "playful", "serious",
)
STYLES: tuple[str, ...] = (
    "realistic", "cinematic", "animated", "cartoon", "documentary",
    "minimalist", "vintage", "futuristic", "fantasy", "abstract",
)
CAMERAS: tuple[str, ...] = (
    "static", "pan", "zoom", "tracking", "aerial",
    "close-up", "wide-shot", "handheld", "dolly", "time-lapse",
)

_DEFAULT_DURATION = 30
_MIN_DURATION = 1
_MAX_DURATION = 3600
_MAX_CHARACTERS = 12

# Field length ceilings, mirrored from schemas/prompt.py so normalisation never
# produces a value the schema would reject.
_MAX_TOPIC = 300
_MAX_AUDIENCE = 200
_MAX_SHORT = 60
_MAX_VOICE = 120
_MAX_CHAR_NAME = 120
_MAX_CHAR_DESC = 500
_MAX_CHAR_ROLE = 60

_SYSTEM_PROMPT = (
    "You are a video prompt analyzer for an AI video generation studio.\n"
    "Given a natural-language description, extract a concise, structured brief.\n"
    "Respond with a SINGLE JSON object and NOTHING else — no markdown, no prose.\n"
    "\n"
    "Use exactly these keys:\n"
    '  "topic": string — the core subject, in a few words.\n'
    '  "audience": string — the intended viewers (e.g. "children", "developers").\n'
    f'  "mood": one of {list(MOODS)}.\n'
    f'  "style": one of {list(STYLES)}.\n'
    f'  "camera": one of {list(CAMERAS)}.\n'
    '  "characters": array of {"name": string, "description": string, '
    '"role": string}; use [] if there are none.\n'
    '  "duration_seconds": integer between 1 and 3600 — a sensible length.\n'
    '  "language": string — the narration language (e.g. "English").\n'
    '  "voice": string — recommended narration voice (e.g. "warm female narrator").\n'
    "\n"
    "If a detail is not specified, infer a sensible default. "
    "Never leave a field empty."
)


class PromptAnalyzerService:
    """Analyses natural-language prompts into a structured ``PromptAnalysis``."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        """
        Args:
            session: Optional DB session. The analyzer is stateless today, but
                accepting a session matches the project's service constructor
                convention and leaves room for future persistence (e.g. caching
                analyses per project).
        """
        self._session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(self, prompt: str) -> PromptAnalysis:
        """
        Analyse a natural-language prompt into a structured video brief.

        Args:
            prompt: The user's free-form description of the desired video.

        Returns:
            A fully-populated, validated ``PromptAnalysis``.

        Raises:
            InvalidInputError: The prompt is empty or too short.
            ProviderNotConfiguredError: No LLM provider is configured.
            LLMProviderError: Inference failed or produced unparseable output.
        """
        cleaned = (prompt or "").strip()
        if len(cleaned) < 3:
            raise InvalidInputError("Prompt must be at least 3 characters long.")

        settings = get_settings()
        provider = await get_llm_provider()

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": cleaned},
        ]

        logger.info(
            "prompt_analysis_started",
            provider=provider.model_info().get("name"),
            prompt_length=len(cleaned),
        )

        raw = await provider.chat(
            messages,
            max_tokens=settings.llm.analyzer_max_tokens,
            temperature=settings.llm.analyzer_temperature,
        )

        try:
            data = extract_json_object(raw)
        except ValueError as exc:
            logger.error("prompt_analysis_parse_failed", error=str(exc))
            raise LLMProviderError(
                message="The language model returned an unparseable analysis.",
                detail={"reason": str(exc)},
            ) from exc

        analysis = self._normalise(data, fallback_topic=cleaned)
        logger.info(
            "prompt_analysis_completed",
            topic=analysis.topic,
            mood=analysis.mood,
            style=analysis.style,
            camera=analysis.camera,
            duration_seconds=analysis.duration_seconds,
            character_count=len(analysis.characters),
        )
        return analysis

    # ------------------------------------------------------------------
    # Normalisation — repair raw model output into a valid PromptAnalysis
    # ------------------------------------------------------------------

    def _normalise(
        self, data: dict[str, Any], *, fallback_topic: str
    ) -> PromptAnalysis:
        """Coerce a raw parsed dict into a valid, fully-populated analysis."""
        return PromptAnalysis(
            topic=_clean_str(data.get("topic"), _MAX_TOPIC)
            or _truncate(fallback_topic, _MAX_TOPIC),
            audience=_clean_str(data.get("audience"), _MAX_AUDIENCE)
            or "general audience",
            mood=_snap(data.get("mood"), MOODS),
            style=_snap(data.get("style"), STYLES),
            camera=_snap(data.get("camera"), CAMERAS),
            characters=_coerce_characters(data.get("characters")),
            duration_seconds=_coerce_duration(data.get("duration_seconds")),
            language=_clean_str(data.get("language"), _MAX_SHORT) or "English",
            voice=_clean_str(data.get("voice"), _MAX_VOICE) or "neutral narrator",
        )


# ---------------------------------------------------------------------------
# Module-level normalisation helpers
# ---------------------------------------------------------------------------


def _clean_str(value: Any, max_length: int) -> str:
    """Return a trimmed, length-capped string, or '' for non-string input."""
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]


def _truncate(value: str, max_length: int) -> str:
    return value[:max_length]


def _snap(value: Any, vocabulary: tuple[str, ...]) -> str:
    """
    Map a raw value onto the controlled vocabulary.

    Exact (case-insensitive) matches are canonicalised. Unrecognised but
    non-empty values are kept (trimmed/lowercased) so genuine nuance is not
    discarded. Empty/invalid input falls back to the vocabulary's default
    (its first entry).
    """
    default = vocabulary[0]
    cleaned = _clean_str(value, _MAX_SHORT).lower()
    if not cleaned:
        return default
    for term in vocabulary:
        if cleaned == term:
            return term
    return cleaned


def _coerce_duration(value: Any) -> int:
    """Coerce a duration into a clamped integer number of seconds."""
    seconds: int
    if isinstance(value, bool):  # bool is an int subclass — reject explicitly
        return _DEFAULT_DURATION
    if isinstance(value, int):
        seconds = value
    elif isinstance(value, float):
        seconds = int(value)
    elif isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if not digits:
            return _DEFAULT_DURATION
        seconds = int(digits)
    else:
        return _DEFAULT_DURATION
    return max(_MIN_DURATION, min(_MAX_DURATION, seconds))


def _coerce_characters(value: Any) -> list[PromptCharacter]:
    """Coerce raw character data into a capped list of PromptCharacter."""
    if not isinstance(value, list):
        return []

    characters: list[PromptCharacter] = []
    for item in value:
        if len(characters) >= _MAX_CHARACTERS:
            break

        if isinstance(item, str):
            name = _clean_str(item, _MAX_CHAR_NAME)
            if name:
                characters.append(PromptCharacter(name=name))
            continue

        if isinstance(item, dict):
            name = _clean_str(item.get("name"), _MAX_CHAR_NAME)
            if not name:
                continue
            description = _clean_str(item.get("description"), _MAX_CHAR_DESC) or None
            role = _clean_str(item.get("role"), _MAX_CHAR_ROLE) or None
            characters.append(
                PromptCharacter(name=name, description=description, role=role)
            )

    return characters
