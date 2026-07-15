"""
LLM Provider Behaviour Tests.

WHY: Verifies the Gemma/Llama providers honour the LLMProvider contract
     without requiring a real GGUF weight file or the (heavy, native)
     llama-cpp-python package to be installed.

Everything here exercises the code paths that run *before* the model is
loaded — protocol conformance, metadata, cheap availability checks, input
validation, and error mapping — which is exactly where the abstraction's
guarantees live.
"""

from types import SimpleNamespace

import pytest

from app.core.exceptions import LLMProviderError
from app.providers.base.llm_provider import LLMProvider
from app.providers.llm.gemma_provider import GemmaProvider
from app.providers.llm.llama_provider import LlamaProvider


def _llm_settings(model_path: str = "/tmp/nonexistent-model.gguf") -> SimpleNamespace:
    return SimpleNamespace(
        provider="gemma",
        model_path=model_path,
        context_length=2048,
        n_threads=2,
    )


@pytest.fixture
def make_provider():
    """Factory that builds providers and tears down their thread pools."""
    created = []

    def _factory(cls, **overrides):
        provider = cls(_llm_settings(**overrides))
        created.append(provider)
        return provider

    yield _factory

    for provider in created:
        provider.close()


# ---------------------------------------------------------------------------
# Contract / metadata
# ---------------------------------------------------------------------------


def test_providers_satisfy_protocol(make_provider):
    assert isinstance(make_provider(GemmaProvider), LLMProvider)
    assert isinstance(make_provider(LlamaProvider), LLMProvider)


def test_gemma_model_info(make_provider):
    info = make_provider(GemmaProvider).model_info()
    assert info["name"] == "gemma"
    assert info["provider"] == "GemmaProvider"
    assert info["backend"] == "llama.cpp"
    assert info["loaded"] == "False"


def test_llama_model_info(make_provider):
    info = make_provider(LlamaProvider).model_info()
    assert info["name"] == "llama"
    assert info["provider"] == "LlamaProvider"


def test_providers_use_distinct_chat_formats():
    """Same interface, different template — the plug-in point between models."""
    assert GemmaProvider.chat_format == "gemma"
    assert LlamaProvider.chat_format == "llama-3"


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


async def test_is_available_false_when_model_missing(make_provider):
    provider = make_provider(GemmaProvider)
    assert await provider.is_available() is False


# ---------------------------------------------------------------------------
# Input validation (fails fast, before any model load)
# ---------------------------------------------------------------------------


async def test_generate_empty_prompt_raises(make_provider):
    provider = make_provider(GemmaProvider)
    with pytest.raises(LLMProviderError):
        await provider.generate("   ")


async def test_chat_empty_messages_raises(make_provider):
    provider = make_provider(GemmaProvider)
    with pytest.raises(LLMProviderError):
        await provider.chat([])


async def test_chat_invalid_role_raises(make_provider):
    provider = make_provider(GemmaProvider)
    with pytest.raises(LLMProviderError):
        await provider.chat([{"role": "root", "content": "hello"}])


async def test_chat_empty_content_raises(make_provider):
    provider = make_provider(GemmaProvider)
    with pytest.raises(LLMProviderError):
        await provider.chat([{"role": "user", "content": "   "}])


# ---------------------------------------------------------------------------
# Error mapping — a missing weight file surfaces as a domain error,
# never a raw OSError / ImportError.
# ---------------------------------------------------------------------------


async def test_generate_missing_model_raises_provider_error(make_provider):
    provider = make_provider(GemmaProvider)
    with pytest.raises(LLMProviderError):
        await provider.generate("Write a haiku about the sea.")
