"""
AI Provider Base Abstractions.

WHY this package exists:
    Every AI capability (LLM, image generation, TTS, STT, video) is
    defined as a Protocol here. Concrete providers implement the protocol.

    This is the key architectural decision that makes AI models swappable.
    The rest of the application only imports from this package — it never
    imports a concrete provider directly.

    Swap Gemma for Llama? Change one environment variable. Zero code changes.
"""
