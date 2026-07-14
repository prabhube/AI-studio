"""
Background Tasks Package.

WHY Celery for background tasks?
    AI generation is slow (seconds to minutes). Handling it in an
    HTTP request would cause timeouts and block the server.
    Celery runs tasks asynchronously in separate worker processes.

    Flow:
      1. API receives request → creates DB record → dispatches task → returns 202
      2. Celery worker picks up task → runs AI generation → updates DB record
      3. Frontend polls the status endpoint → shows progress → loads result

    Redis serves as both the Celery broker (task queue) and result backend
    (task state storage).

Task queues (routing):
    video   — long-running full pipeline tasks (high memory)
    image   — Stable Diffusion generation (GPU memory)
    audio   — TTS synthesis (CPU, fast)
    default — everything else

This separation allows running different worker concurrencies
per queue. GPU tasks need 1 concurrency; audio tasks can run 4.
"""
