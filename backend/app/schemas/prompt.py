"""
Prompt Analyzer Pydantic Schemas.

PromptAnalyzeRequest  → POST /prompts/analyze  (request body)
PromptAnalysis        → POST /prompts/analyze  (response payload)
PromptCharacter       → nested inside PromptAnalysis

WHY defaults on every analysis field?
    The values are produced by a language model. Even with a strict
    instruction, a local model may omit a key or return an odd value. Defaults
    guarantee a stable, fully-populated response shape; the service normalises
    and repairs the raw model output *before* it reaches this schema, so
    validation never fails on well-formed-but-incomplete model responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PromptCharacter(BaseModel):
    """A character or entity detected in the prompt."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    role: str | None = Field(
        default=None,
        max_length=60,
        description="Narrative role, e.g. 'protagonist', 'narrator'.",
    )


class PromptAnalyzeRequest(BaseModel):
    """Request body for prompt analysis."""

    prompt: str = Field(
        min_length=3,
        max_length=4000,
        description="Natural-language description of the desired video.",
    )


class PromptAnalysis(BaseModel):
    """
    Structured interpretation of a natural-language video prompt.

    This is the machine-readable brief the generation pipeline consumes to
    drive script, image, narration, and assembly stages.
    """

    topic: str = Field(
        default="",
        max_length=300,
        description="The core subject of the video.",
    )
    audience: str = Field(
        default="general audience",
        max_length=200,
        description="The intended viewers.",
    )
    mood: str = Field(
        default="neutral",
        max_length=60,
        description="Overall emotional tone.",
    )
    characters: list[PromptCharacter] = Field(
        default_factory=list,
        description="Characters or entities featured in the video.",
    )
    style: str = Field(
        default="realistic",
        max_length=60,
        description="Visual style of the video.",
    )
    camera: str = Field(
        default="static",
        max_length=60,
        description="Dominant camera treatment.",
    )
    duration_seconds: int = Field(
        default=30,
        ge=1,
        le=3600,
        description="Estimated video length in seconds.",
    )
    language: str = Field(
        default="English",
        max_length=60,
        description="Narration / caption language.",
    )
    voice: str = Field(
        default="neutral narrator",
        max_length=120,
        description="Recommended narration voice characteristics.",
    )
