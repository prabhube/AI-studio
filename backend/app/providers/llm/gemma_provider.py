"""
Gemma LLM Provider.

WHY this file exists:
    Provides the Google Gemma implementation of the LLMProvider protocol,
    running a GGUF checkpoint through llama.cpp (llama-cpp-python).

    All of the loading / threading / inference machinery lives in
    ``LlamaCppProvider``. This class only declares Gemma's identity and the
    chat template llama.cpp should apply — which is exactly what makes Gemma
    and Llama interchangeable behind the factory.

Configuration:
    LLM_PROVIDER=gemma
    LLM_MODEL_PATH=/models/llm/gemma-2b-it.gguf
"""

from app.providers.llm._llama_cpp_base import LlamaCppProvider


class GemmaProvider(LlamaCppProvider):
    """
    LLMProvider implementation backed by Google Gemma via llama.cpp.

    Satisfies the LLMProvider Protocol structurally — no inheritance from the
    Protocol itself is required.
    """

    model_name = "gemma"
    model_version = "2b-it"
    #: Gemma uses its own instruction template (``<start_of_turn>`` markers).
    chat_format = "gemma"
