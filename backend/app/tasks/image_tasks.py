"""
Image Generation Celery Tasks — Placeholders.

Tasks in the 'image' queue. GPU-bound; concurrency = 1 per GPU.
All tasks will be implemented in Phase 4.
"""

from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.tasks.image_tasks.generate_image",
    queue="image",
    max_retries=1,
    default_retry_delay=30,
    soft_time_limit=300,   # 5 minute soft limit
    time_limit=360,        # 6 minute hard limit
)
def generate_image(self, image_id: str, prompt: str, params: dict) -> dict:
    """
    Generate a single image using the configured image provider.

    Args:
        image_id:  UUID string of the Image record to update.
        prompt:    Image generation prompt.
        params:    Generation parameters (width, height, steps, seed, etc.)

    Returns:
        Dict with "status" and "file_path" keys.

    Implementation: Phase 4.
    """
    raise NotImplementedError("generate_image task — Phase 4")
