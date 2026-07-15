"""
Story, Scene, and Character Pydantic schemas for the generation pipeline.

Flow:
  PromptAnalysis → StoryGenerateRequest → Story
  Story          → StoryReviewRequest   → StoryReview
  Story          → SceneGenerateRequest → list[SceneDetail]
  SceneDetail[]  → SceneReviewRequest   → SceneReview
  PromptAnalysis → CharacterGenRequest  → list[CharacterSheet]
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.prompt import PromptAnalysis


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class Scene(BaseModel):
    """A single scene in the video story."""

    index: int = Field(ge=0, description="Zero-based scene index.")
    title: str = Field(max_length=200, description="Short scene title.")
    narration: str = Field(max_length=2000, description="Narration text for this scene.")
    image_prompt: str = Field(
        max_length=1000,
        description="Stable-Diffusion-ready image generation prompt for this scene.",
    )
    duration_seconds: int = Field(ge=1, le=120, description="Approximate scene duration.")
    setting: str = Field(default="", max_length=300, description="Scene location/environment.")
    mood: str = Field(default="", max_length=60, description="Emotional tone for this scene.")


class SceneDetail(BaseModel):
    """Expanded scene with richer visual direction."""

    index: int = Field(ge=0)
    title: str = Field(max_length=200)
    narration: str = Field(max_length=2000)
    image_prompt: str = Field(max_length=1000)
    negative_prompt: str = Field(
        default="",
        max_length=500,
        description="Stable Diffusion negative prompt — what NOT to generate.",
    )
    duration_seconds: int = Field(ge=1, le=120)
    setting: str = Field(default="", max_length=300)
    mood: str = Field(default="", max_length=60)
    camera_angle: str = Field(default="", max_length=60)
    lighting: str = Field(default="", max_length=120)
    characters_present: list[str] = Field(
        default_factory=list,
        description="Names of characters appearing in this scene.",
    )


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

class Story(BaseModel):
    """A complete video story generated from a prompt analysis."""

    title: str = Field(max_length=300, description="Video title.")
    synopsis: str = Field(max_length=1000, description="One-paragraph synopsis.")
    scenes: list[Scene] = Field(description="Ordered list of scenes.")
    total_duration_seconds: int = Field(ge=1, description="Sum of all scene durations.")
    style_notes: str = Field(
        default="",
        max_length=500,
        description="Visual style guidance for the generation pipeline.",
    )
    target_audience: str = Field(default="", max_length=200)
    genre: str = Field(default="", max_length=60)


# ---------------------------------------------------------------------------
# Story request / response
# ---------------------------------------------------------------------------

class StoryGenerateRequest(BaseModel):
    """Request body: generate a story from a prompt analysis."""

    analysis: PromptAnalysis
    num_scenes: int = Field(
        default=5,
        ge=1,
        le=20,
        description="How many scenes to generate.",
    )


class StoryReviewRequest(BaseModel):
    """Request body: review a generated story."""

    story: Story
    original_prompt: str = Field(max_length=4000)


class StoryReview(BaseModel):
    """LLM review of a generated story."""

    quality_score: int = Field(ge=1, le=10, description="Overall quality (1–10).")
    approved: bool = Field(description="True if story is ready for scene generation.")
    issues: list[str] = Field(
        default_factory=list,
        description="List of identified problems.",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Improvement suggestions.",
    )
    revised_story: Story | None = Field(
        default=None,
        description="Improved story, if the reviewer made changes.",
    )


# ---------------------------------------------------------------------------
# Scene requests / responses
# ---------------------------------------------------------------------------

class SceneGenerateRequest(BaseModel):
    """Request body: expand story scenes into detailed scene directions."""

    story: Story
    style: str = Field(
        default="realistic",
        max_length=60,
        description="Visual style to embed in image prompts.",
    )


class SceneReviewRequest(BaseModel):
    """Request body: review generated scene details."""

    scenes: list[SceneDetail]
    story_title: str = Field(max_length=300)


class SceneReview(BaseModel):
    """LLM review of scene details."""

    quality_score: int = Field(ge=1, le=10)
    approved: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    revised_scenes: list[SceneDetail] | None = Field(default=None)


# ---------------------------------------------------------------------------
# Character
# ---------------------------------------------------------------------------

class CharacterSheet(BaseModel):
    """Full visual description of a character for the generation pipeline."""

    name: str = Field(max_length=120)
    role: str = Field(default="", max_length=60)
    appearance: str = Field(
        max_length=500,
        description="Detailed physical description for image generation.",
    )
    image_prompt: str = Field(
        max_length=500,
        description="Stable-Diffusion-ready character description.",
    )
    personality: str = Field(default="", max_length=300)
    voice_description: str = Field(default="", max_length=200)


class CharacterGenRequest(BaseModel):
    """Request body: generate character sheets from prompt analysis."""

    analysis: PromptAnalysis
