"""
Pipeline Service — Orchestrates the full AI video generation pipeline.

WHY this file exists:
    This is the highest-level service in the application.
    It coordinates all other AI services in sequence:

    Step 1: LLM generates a structured script from the user's prompt
    Step 2: LLM generates image prompts for each script scene
    Step 3: Stable Diffusion generates one image per scene (parallel)
    Step 4: Piper TTS synthesizes narration from the script
    Step 5: FFmpeg assembles frames + audio into the final video

    The pipeline runs entirely within a Celery task (video_tasks.py).
    This service provides the logic; tasks provide the async execution.

All methods will be implemented in Phase 8 (end-to-end pipeline).
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession


class PipelineService:
    """
    Coordinates multi-step AI generation pipeline.

    Each step produces output consumed by the next step.
    Failures at any step mark the Video record as 'failed'
    and preserve the error message for debugging.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def run_video_pipeline(
        self, video_id: uuid.UUID, prompt: str, options: dict
    ) -> str:
        """
        Execute the full video generation pipeline.

        Args:
            video_id:  ID of the Video record to update throughout.
            prompt:    Original user prompt.
            options:   Dictionary of pipeline parameters.

        Returns:
            Path to the completed video file.

        Raises:
            VideoProviderError: If any pipeline step fails.
        """
        ...

    async def generate_script(self, prompt: str) -> dict:
        """
        Use the LLM to expand a short prompt into a structured script.

        Returns a dict with:
          { "title": str, "scenes": [{"narration": str, "image_prompt": str}] }
        """
        ...

    async def generate_frames(
        self, image_prompts: list[str], project_id: uuid.UUID
    ) -> list[str]:
        """
        Generate one image per scene using the image provider.

        Returns an ordered list of image file paths.
        """
        ...

    async def generate_narration(self, script_text: str, project_id: uuid.UUID) -> str:
        """
        Synthesize narration from the script using the TTS provider.

        Returns the path to the audio file.
        """
        ...

    async def assemble_video(
        self,
        video_id: uuid.UUID,
        frame_paths: list[str],
        audio_path: str,
        options: dict,
    ) -> str:
        """
        Assemble frames and audio into the final video.

        Returns the path to the completed video file.
        """
        ...
