"""
LLM Provider Protocol.

WHY this file exists:
    Defines the contract that ALL language model providers must satisfy.
    The application's services import and type-hint against this Protocol —
    never against GemmaProvider or LlamaProvider directly.

    This means:
      - Gemma and Llama are interchangeable at runtime.
      - Future models (Mistral, Phi, Qwen, etc.) plug in with zero
        changes to services.
      - The Protocol is verifiable: `isinstance(provider, LLMProvider)`
        works via structural subtyping.

Protocol methods:
    generate()        → Single-turn text completion
    chat()            → Multi-turn conversation
    is_available()    → Checks if the model is loaded
    model_info()      → Returns model metadata
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """
    Structural protocol for all language model providers.

    Any class that implements these methods satisfies the protocol,
    whether or not it explicitly inherits from LLMProvider.
    """

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """
        Generate a text completion for the given prompt.

        Args:
            prompt:          The input prompt text.
            max_tokens:      Maximum number of tokens to generate.
            temperature:     Sampling temperature (0.0 = deterministic).
            stop_sequences:  List of strings that stop generation.

        Returns:
            The generated text string.
        """
        ...

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Multi-turn chat completion.

        Args:
            messages:    List of {"role": "user"|"assistant"|"system", "content": str}
            max_tokens:  Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            The assistant's reply as a plain string.
        """
        ...

    async def is_available(self) -> bool:
        """
        Return True if the model is loaded and ready for inference.

        Used by the health check and provider factory to validate
        the provider before routing requests to it.
        """
        ...

    def model_info(self) -> dict[str, str]:
        """
        Return metadata about the loaded model.

        Returns a dict with at least:
            { "name": str, "provider": str, "version": str }
        """
        ...
