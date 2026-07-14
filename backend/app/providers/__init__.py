"""
AI Providers package.

WHY this package exists:
    Provides a single abstraction layer between the application's
    business logic and the underlying AI model implementations.

    The application never imports concrete providers directly.
    It always uses factories from this package:

        from app.providers.llm.factory   import get_llm_provider
        from app.providers.image.factory import get_image_provider
        from app.providers.tts.factory   import get_tts_provider
        from app.providers.stt.factory   import get_stt_provider
        from app.providers.video.factory import get_video_provider

    The concrete provider is determined entirely by environment variables.
    No code changes are needed to swap AI models.

Package structure:
    base/     — Protocol definitions (the contracts)
    llm/      — Language model providers (Gemma, Llama, ...)
    image/    — Image generation providers (Stable Diffusion, ...)
    tts/      — Text-to-speech providers (Piper, ...)
    stt/      — Speech-to-text providers (Whisper, ...)
    video/    — Video assembly providers (FFmpeg, ...)
"""
