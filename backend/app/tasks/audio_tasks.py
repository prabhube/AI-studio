"""
Audio Generation Celery Tasks — Placeholders.

Tasks in the 'audio' queue. CPU-bound; concurrency = 2-4.
All tasks will be implemented in Phase 5.
"""

from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    name="app.tasks.audio_tasks.synthesize_speech",
    queue="audio",
    max_retries=2,
    default_retry_delay=15,
    soft_time_limit=120,   # 2 minute soft limit
    time_limit=180,        # 3 minute hard limit
)
def synthesize_speech(self, clip_id: str, text: str, params: dict) -> dict:
    """
    Synthesize speech from text using the configured TTS provider.

    Args:
        clip_id:  UUID string of the AudioClip record to update.
        text:     Text to synthesize.
        params:   TTS parameters (voice_id, speed, output_format).

    Returns:
        Dict with "status", "file_path", and "duration_seconds" keys.

    Implementation: Phase 5.
    """
    raise NotImplementedError("synthesize_speech task — Phase 5")


@celery_app.task(
    bind=True,
    name="app.tasks.audio_tasks.transcribe_audio",
    queue="audio",
    max_retries=1,
    soft_time_limit=300,
    time_limit=360,
)
def transcribe_audio(self, clip_id: str, audio_path: str, params: dict) -> dict:
    """
    Transcribe uploaded audio using the configured STT provider.

    Args:
        clip_id:    UUID string of the AudioClip record to update.
        audio_path: Path to the uploaded audio file.
        params:     STT parameters (language, task).

    Returns:
        Dict with "status", "full_text", and "segments".

    Implementation: Phase 6.
    """
    raise NotImplementedError("transcribe_audio task — Phase 6")
