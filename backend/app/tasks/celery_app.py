"""
Celery Application Configuration.

WHY this file exists:
    Defines and configures the Celery application instance.
    All task modules import from this file to register their tasks.

    Configuration:
    - Broker: Redis (receives tasks from FastAPI)
    - Backend: Redis (stores task results and status)
    - Serializer: JSON (safe, human-readable, no pickle)
    - Timezone: UTC (consistent regardless of server location)
    - Task routing: Distributes tasks to appropriate queues

Usage:
    Start worker: celery -A app.tasks.celery_app worker --loglevel=info
    Monitor:      celery -A app.tasks.celery_app flower
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "prabhu_ai_studio",
    broker=settings.redis.url,
    backend=settings.redis.url,
    include=[
        "app.tasks.video_tasks",
        "app.tasks.image_tasks",
        "app.tasks.audio_tasks",
    ],
)

celery_app.conf.update(
    # Serialization — JSON is safe; avoid pickle (security risk)
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result storage — keep results for 24 hours
    result_expires=86400,

    # Task routing — each queue has a dedicated worker concurrency
    task_routes={
        "app.tasks.video_tasks.*": {"queue": "video"},
        "app.tasks.image_tasks.*": {"queue": "image"},
        "app.tasks.audio_tasks.*": {"queue": "audio"},
    },

    # Reliability — retry tasks on connection errors
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Beat schedule (for future periodic tasks like cleanup)
    beat_schedule={},
)
