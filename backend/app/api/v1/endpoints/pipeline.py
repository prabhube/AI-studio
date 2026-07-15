"""
Pipeline API endpoints — all 15 steps.

Steps 1–6  (LLM-based, stateless):
  POST /pipeline/prompt/analyze       — Step 1: Analyze prompt
  POST /pipeline/story/generate       — Step 2: Generate story
  POST /pipeline/story/review         — Step 3: Review story
  POST /pipeline/scenes/generate      — Step 4: Expand scenes
  POST /pipeline/scenes/review        — Step 5: Review scenes
  POST /pipeline/characters/generate  — Step 6: Generate character sheets

Steps 7–15 (file-based, session-scoped):
  POST /pipeline/session              — Step 7: Create a pipeline session
  POST /pipeline/images/generate      — Step 8: Generate scene images
  POST /pipeline/images/review        — Step 9: Review generated images
  POST /pipeline/voice/generate       — Step 11: Synthesize narration (TTS)
  POST /pipeline/music/generate       — Step 12: Generate background music
  POST /pipeline/subtitles/generate   — Step 13: Generate SRT subtitles
  POST /pipeline/video/assemble       — Steps 10+14: Assemble final video
  GET  /pipeline/session/{id}         — Get session assets info
  GET  /pipeline/video/{id}/download  — Download final video
  GET  /pipeline/images/{id}/{file}   — Serve a scene image
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.core.exceptions import (
    InvalidInputError,
    LLMProviderError,
    ProviderNotConfiguredError,
)
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.prompt import PromptAnalysis, PromptAnalyzeRequest
from app.schemas.story import (
    CharacterGenRequest,
    CharacterSheet,
    SceneDetail,
    SceneGenerateRequest,
    SceneReview,
    SceneReviewRequest,
    Story,
    StoryGenerateRequest,
    StoryReview,
    StoryReviewRequest,
)
from app.services.asset_manager_service import AssetManagerService
from app.services.character_service import CharacterService
from app.services.image_gen_service import ImageGenService
from app.services.image_reviewer_service import ImageReviewerService
from app.services.music_service import MusicService
from app.services.prompt_analyzer_service import PromptAnalyzerService
from app.services.scene_reviewer_service import SceneReviewerService
from app.services.scene_service import SceneService
from app.services.story_reviewer_service import StoryReviewerService
from app.services.story_service import StoryService
from app.services.subtitle_service import SubtitleService
from app.services.video_assembly_service import VideoAssemblyService
from app.services.voice_gen_service import VoiceGenService

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


# ---------------------------------------------------------------------------
# Error helper
# ---------------------------------------------------------------------------

def _handle_llm_errors(exc: Exception) -> None:
    """Re-raise domain exceptions as appropriate HTTP errors."""
    if isinstance(exc, InvalidInputError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    if isinstance(exc, ProviderNotConfiguredError):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    if isinstance(exc, LLMProviderError):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=exc.message) from exc
    raise exc


# ---------------------------------------------------------------------------
# Step 1: Prompt Analysis
# ---------------------------------------------------------------------------

@router.post(
    "/prompt/analyze",
    response_model=SuccessResponse[PromptAnalysis],
    summary="Step 1 — Analyze a prompt into a structured video brief",
)
async def analyze_prompt(
    payload: PromptAnalyzeRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PromptAnalysis]:
    try:
        analysis = await PromptAnalyzerService().analyze(payload.prompt)
        return SuccessResponse(data=analysis, message="Prompt analyzed successfully.")
    except Exception as exc:
        _handle_llm_errors(exc)


# ---------------------------------------------------------------------------
# Step 2: Story Generation
# ---------------------------------------------------------------------------

@router.post(
    "/story/generate",
    response_model=SuccessResponse[Story],
    summary="Step 2 — Generate a story with scenes from a prompt analysis",
)
async def generate_story(
    payload: StoryGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[Story]:
    try:
        story = await StoryService().generate(payload)
        return SuccessResponse(
            data=story,
            message=f"Story '{story.title}' generated with {len(story.scenes)} scenes.",
        )
    except Exception as exc:
        _handle_llm_errors(exc)


# ---------------------------------------------------------------------------
# Step 3: Story Review
# ---------------------------------------------------------------------------

@router.post(
    "/story/review",
    response_model=SuccessResponse[StoryReview],
    summary="Step 3 — Review and optionally revise the generated story",
)
async def review_story(
    payload: StoryReviewRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[StoryReview]:
    try:
        review = await StoryReviewerService().review(payload)
        msg = (
            f"Story approved (score {review.quality_score}/10)."
            if review.approved
            else f"Story needs revision (score {review.quality_score}/10)."
        )
        return SuccessResponse(data=review, message=msg)
    except Exception as exc:
        _handle_llm_errors(exc)


# ---------------------------------------------------------------------------
# Step 4: Scene Generation
# ---------------------------------------------------------------------------

@router.post(
    "/scenes/generate",
    response_model=SuccessResponse[list[SceneDetail]],
    summary="Step 4 — Expand story scenes into detailed visual directions",
)
async def generate_scenes(
    payload: SceneGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[SceneDetail]]:
    try:
        scenes = await SceneService().generate(payload)
        return SuccessResponse(
            data=scenes,
            message=f"{len(scenes)} scenes expanded with visual directions.",
        )
    except Exception as exc:
        _handle_llm_errors(exc)


# ---------------------------------------------------------------------------
# Step 5: Scene Review
# ---------------------------------------------------------------------------

@router.post(
    "/scenes/review",
    response_model=SuccessResponse[SceneReview],
    summary="Step 5 — Review scene image prompts for generation readiness",
)
async def review_scenes(
    payload: SceneReviewRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[SceneReview]:
    try:
        review = await SceneReviewerService().review(payload)
        msg = (
            f"Scenes approved (score {review.quality_score}/10)."
            if review.approved
            else f"Scenes need revision (score {review.quality_score}/10)."
        )
        return SuccessResponse(data=review, message=msg)
    except Exception as exc:
        _handle_llm_errors(exc)


# ---------------------------------------------------------------------------
# Step 6: Character Generation
# ---------------------------------------------------------------------------

@router.post(
    "/characters/generate",
    response_model=SuccessResponse[list[CharacterSheet]],
    summary="Step 6 — Generate character sheets from analysis",
)
async def generate_characters(
    payload: CharacterGenRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[CharacterSheet]]:
    try:
        characters = await CharacterService().generate(payload)
        return SuccessResponse(
            data=characters,
            message=f"{len(characters)} character sheets generated.",
        )
    except Exception as exc:
        _handle_llm_errors(exc)


# ===========================================================================
# Steps 7–15: File-based, session-scoped pipeline
# ===========================================================================

# ---------------------------------------------------------------------------
# Shared request/response schemas for steps 7-15
# ---------------------------------------------------------------------------

class SessionCreateResponse(BaseModel):
    session_id: str
    root_dir: str
    images_dir: str
    audio_dir: str
    subtitles_dir: str
    video_dir: str
    status: str


class ImageGenRequest(BaseModel):
    session_id: str
    scenes: list[SceneDetail]
    width: int = Field(default=512, ge=128, le=1024)
    height: int = Field(default=512, ge=128, le=1024)
    steps: int = Field(default=20, ge=5, le=50)


class ImageGenResponse(BaseModel):
    session_id: str
    image_paths: list[str]
    image_urls: list[str]
    count: int
    sd_used: bool


class ImageReviewRequest(BaseModel):
    session_id: str
    scenes: list[SceneDetail]
    image_paths: list[str]
    style: str = "realistic"


class VoiceGenRequest(BaseModel):
    session_id: str
    scenes: list[SceneDetail]
    voice_id: str = "en_US-lessac-medium"
    language: str = "en"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class MusicGenRequest(BaseModel):
    session_id: str
    duration_seconds: int = Field(default=60, ge=5)
    mood: str = "neutral"
    volume: float = Field(default=0.15, ge=0.0, le=1.0)


class SubtitleGenRequest(BaseModel):
    session_id: str
    scenes: list[SceneDetail]


class VideoAssembleRequest(BaseModel):
    session_id: str
    scenes: list[SceneDetail]
    image_paths: list[str]
    narration_path: str = ""
    music_path: str = ""
    subtitle_path: str = ""
    width: int = Field(default=1280, ge=320, le=3840)
    height: int = Field(default=720, ge=240, le=2160)
    fps: int = Field(default=24, ge=12, le=60)


# ---------------------------------------------------------------------------
# Step 7: Session / Asset Manager
# ---------------------------------------------------------------------------

@router.post(
    "/session",
    response_model=SuccessResponse[SessionCreateResponse],
    summary="Step 7 — Create a new pipeline session and asset directories",
)
async def create_session(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[SessionCreateResponse]:
    svc = AssetManagerService()
    session = svc.create_session()
    return SuccessResponse(
        data=SessionCreateResponse(**session.to_dict()),
        message=f"Session {session.session_id} created.",
    )


@router.get(
    "/session/{session_id}",
    summary="Get session asset info",
)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    svc = AssetManagerService()
    session = svc.get_session(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return SuccessResponse(data=session.to_dict(), message="Session loaded.")


# ---------------------------------------------------------------------------
# Step 8: Image Generation
# ---------------------------------------------------------------------------

@router.post(
    "/images/generate",
    response_model=SuccessResponse[ImageGenResponse],
    summary="Step 8 — Generate scene images (SD WebUI or PIL placeholder)",
)
async def generate_images(
    payload: ImageGenRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[ImageGenResponse]:
    svc = AssetManagerService()
    session = svc.get_session(payload.session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")

    images_dir = Path(session.images_dir)
    image_svc = ImageGenService()
    paths = await image_svc.generate_all(
        scenes=payload.scenes,
        images_dir=images_dir,
        width=payload.width,
        height=payload.height,
        steps=payload.steps,
    )

    # Build URL paths for the frontend to display
    urls = [
        f"/api/v1/pipeline/images/{payload.session_id}/{Path(p).name}"
        for p in paths
    ]

    # Update session state
    session.image_paths = paths
    svc.update_session(session)

    return SuccessResponse(
        data=ImageGenResponse(
            session_id=payload.session_id,
            image_paths=paths,
            image_urls=urls,
            count=len(paths),
            sd_used=False,
        ),
        message=f"{len(paths)} scene images generated.",
    )


# ---------------------------------------------------------------------------
# Step 9: Image Review
# ---------------------------------------------------------------------------

@router.post(
    "/images/review",
    summary="Step 9 — Review generated scene images",
)
async def review_images(
    payload: ImageReviewRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    try:
        result = await ImageReviewerService().review(
            scenes=payload.scenes,
            image_paths=payload.image_paths,
            style=payload.style,
        )
        msg = (
            f"Images approved (score {result['overall_score']}/10)."
            if result["approved"]
            else f"Images need revision (score {result['overall_score']}/10)."
        )
        return SuccessResponse(data=result, message=msg)
    except Exception as exc:
        _handle_llm_errors(exc)


# ---------------------------------------------------------------------------
# Step 10: Video Generation (frame → silent video) is combined into Step 14
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Step 11: Voice Generation
# ---------------------------------------------------------------------------

@router.post(
    "/voice/generate",
    summary="Step 11 — Generate TTS narration audio",
)
async def generate_voice(
    payload: VoiceGenRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    svc = AssetManagerService()
    session = svc.get_session(payload.session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")

    audio_dir = Path(session.audio_dir)
    result = await VoiceGenService().generate(
        scenes=payload.scenes,
        audio_dir=audio_dir,
        voice_id=payload.voice_id,
        language=payload.language,
        speed=payload.speed,
    )

    session.narration_path = result["narration_path"]
    svc.update_session(session)

    return SuccessResponse(data=result, message="Narration audio generated.")


# ---------------------------------------------------------------------------
# Step 12: Music Generation
# ---------------------------------------------------------------------------

@router.post(
    "/music/generate",
    summary="Step 12 — Generate background music using FFmpeg synthesis",
)
async def generate_music(
    payload: MusicGenRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    svc = AssetManagerService()
    session = svc.get_session(payload.session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")

    audio_dir = Path(session.audio_dir)
    music_path = await MusicService().generate(
        audio_dir=audio_dir,
        duration_seconds=payload.duration_seconds,
        mood=payload.mood,
        volume=payload.volume,
    )

    session.music_path = music_path
    svc.update_session(session)

    return SuccessResponse(
        data={"music_path": music_path, "mood": payload.mood},
        message="Background music generated.",
    )


# ---------------------------------------------------------------------------
# Step 13: Subtitle Generation
# ---------------------------------------------------------------------------

@router.post(
    "/subtitles/generate",
    summary="Step 13 — Generate SRT subtitles from narration text",
)
async def generate_subtitles(
    payload: SubtitleGenRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    svc = AssetManagerService()
    session = svc.get_session(payload.session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")

    subtitles_dir = Path(session.subtitles_dir)
    subtitle_path = await SubtitleService().generate(
        scenes=payload.scenes,
        subtitles_dir=subtitles_dir,
    )

    session.subtitle_path = subtitle_path
    svc.update_session(session)

    # Read the SRT content to return for preview
    srt_content = ""
    try:
        srt_content = Path(subtitle_path).read_text(encoding="utf-8")
    except Exception:
        pass

    return SuccessResponse(
        data={"subtitle_path": subtitle_path, "srt_preview": srt_content[:1000]},
        message="SRT subtitles generated.",
    )


# ---------------------------------------------------------------------------
# Steps 10 + 14: Video Assembly (images → video → add audio/music/subs)
# ---------------------------------------------------------------------------

@router.post(
    "/video/assemble",
    summary="Steps 10+14 — Assemble final video with FFmpeg",
)
async def assemble_video(
    payload: VideoAssembleRequest,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    svc = AssetManagerService()
    session = svc.get_session(payload.session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")

    video_dir = Path(session.video_dir)
    result = await VideoAssemblyService().assemble(
        scenes=payload.scenes,
        image_paths=payload.image_paths or session.image_paths,
        narration_path=payload.narration_path or session.narration_path,
        music_path=payload.music_path or session.music_path,
        subtitle_path=payload.subtitle_path or session.subtitle_path,
        video_dir=video_dir,
        width=payload.width,
        height=payload.height,
        fps=payload.fps,
    )

    session.final_video_path = result.get("final_path", "")
    session.assembled_video_path = result.get("assembled_path", "")
    session.status = "complete" if result.get("success") else "error"
    session.error = result.get("error", "")
    svc.update_session(session)

    download_url = (
        f"/api/v1/pipeline/video/{payload.session_id}/download"
        if result.get("success")
        else ""
    )
    result["download_url"] = download_url

    msg = "Video assembled successfully." if result.get("success") else result.get("error", "Assembly failed.")
    return SuccessResponse(data=result, message=msg)


# ---------------------------------------------------------------------------
# Step 15: Export / Download
# ---------------------------------------------------------------------------

@router.get(
    "/video/{session_id}/download",
    summary="Step 15 — Download the final assembled video",
)
async def download_video(
    session_id: str,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    svc = AssetManagerService()
    session = svc.get_session(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")

    final_path = Path(session.final_video_path) if session.final_video_path else None
    if not final_path or not final_path.exists():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Final video not found. Run video assembly first.",
        )

    return FileResponse(
        path=str(final_path),
        media_type="video/mp4",
        filename=f"prabhu_ai_video_{session_id[:8]}.mp4",
    )


# ---------------------------------------------------------------------------
# Asset serving: serve generated images
# ---------------------------------------------------------------------------

@router.get(
    "/images/{session_id}/{filename}",
    summary="Serve a generated scene image",
)
async def serve_image(
    session_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    svc = AssetManagerService()
    session = svc.get_session(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Session not found.")

    # Security: only allow simple filenames (no path traversal)
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid filename.")

    image_path = Path(session.images_dir) / filename
    if not image_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Image not found.")

    return FileResponse(path=str(image_path), media_type="image/png")
