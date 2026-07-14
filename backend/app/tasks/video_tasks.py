"""
Video Generation Celery Tasks — Placeholders.

WHY this file exists:
    Defines the Celery tasks that execute video generation in the background.
    Tasks are the bridge between the API layer (fast, async) and the
    AI processing layer (slow, CPU/GPU-bound).

    Task lifecycle:
      1. FastAPI calls .delay() or .apply_async() → task ID returned
      2. Worker picks task from 'video' queue
      3. Task calls PipelineService.run_video_pipeline()
      4. Task updates Video record status throughout
      5. On completion, Video.status = 'completed', Video.file_path set

All tasks will be implemented in Phase 8.
"""

from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.tasks.video_tasks.generate_video",
    queue="video",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=1800,  # 30 minute soft limit
    time_limit=2100,       # 35 minute hard limit
)
def generate_video(self, video_id: str, prompt: str, options: dict) -> dict:
    """
    Execute the full video generation pipeline.

    Args:
        video_id:  UUID string of the Video record to update.
        prompt:    Original user prompt.
        options:   Pipeline parameters (frames, resolution, voice, etc.)

    Returns:
        Dict with "status" and "file_path" keys.

    Implementation: Phase 8.
    """
    raise NotImplementedError("generate_video task — Phase 8")
