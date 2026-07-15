"""
Llama LLM Provider.

WHY this file exists:
    Provides the Meta Llama implementation of the LLMProvider protocol,
    running a GGUF checkpoint through llama.cpp (llama-cpp-python).

    Structurally identical to GemmaProvider — same shared base, a different
    checkpoint and chat template. This is the plug-in architecture in action:
    swapping Gemma ↔ Llama is a single environment variable and requires zero
    changes to any service or business logic.

Configuration:
    LLM_PROVIDER=llama
    LLM_MODEL_PATH=/models/llm/llama-3-8b-instruct.gguf
"""

from app.providers.llm._llama_cpp_base import LlamaCppProvider


class LlamaProvider(LlamaCppProvider):
    """
    LLMProvider implementation backed by Meta Llama via llama.cpp.

    Satisfies the LLMProvider Protocol structurally.
    """

    model_name = "llama"
    model_version = "3-8b"
    #: Llama 3 instruct template (``<|begin_of_text|>`` / header markers).
    chat_format = "llama-3"
