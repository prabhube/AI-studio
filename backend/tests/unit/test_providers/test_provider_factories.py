"""
Provider Factory Unit Tests.

WHY: Tests that factories correctly resolve providers from settings
     and raise ProviderNotConfiguredError when set to "none".

The LLM factory tests are implemented (Phase 3). They prove the core promise
of the abstraction layer: the concrete provider is chosen purely from
configuration, and every provider satisfies the LLMProvider protocol, so
business logic can depend on the protocol alone.

Image / TTS / STT / video factories remain skipped until their phases.
"""

from types import SimpleNamespace

import pytest

from app.core.exceptions import ProviderNotConfiguredError
from app.providers.base.llm_provider import LLMProvider
from app.providers.llm import factory
from app.providers.llm.gemma_provider import GemmaProvider
from app.providers.llm.llama_provider import LlamaProvider


def _settings(provider: str) -> SimpleNamespace:
    """
    Build a minimal settings stub shaped like the real Settings object.

    Only ``.llm`` is needed by the factory. The nested attributes are the ones
    a provider reads at construction time (model loading is lazy, so no real
    weight file or llama-cpp-python install is required for these tests).
    """
    llm = SimpleNamespace(
        provider=provider,
        model_path="/tmp/nonexistent-model.gguf",
        context_length=2048,
        n_threads=2,
    )
    return SimpleNamespace(llm=llm)


@pytest.fixture(autouse=True)
def _reset_singleton() -> None:
    """Ensure a clean factory singleton before and after every test."""
    factory.reset_llm_provider()
    yield
    factory.reset_llm_provider()


@pytest.mark.asyncio
class TestLLMProviderFactory:
    async def test_gemma_provider_selected_when_configured(self, monkeypatch):
        monkeypatch.setattr(factory, "get_settings", lambda: _settings("gemma"))

        provider = await factory.get_llm_provider()

        assert isinstance(provider, GemmaProvider)
        # Structural protocol conformance — the whole point of the abstraction.
        assert isinstance(provider, LLMProvider)
        assert provider.model_info()["name"] == "gemma"

    async def test_llama_provider_selected_when_configured(self, monkeypatch):
        monkeypatch.setattr(factory, "get_settings", lambda: _settings("llama"))

        provider = await factory.get_llm_provider()

        assert isinstance(provider, LlamaProvider)
        assert isinstance(provider, LLMProvider)
        assert provider.model_info()["name"] == "llama"

    async def test_none_raises_provider_not_configured_error(self, monkeypatch):
        monkeypatch.setattr(factory, "get_settings", lambda: _settings("none"))

        with pytest.raises(ProviderNotConfiguredError):
            await factory.get_llm_provider()

    async def test_unknown_provider_raises(self, monkeypatch):
        monkeypatch.setattr(factory, "get_settings", lambda: _settings("mistral"))

        with pytest.raises(ProviderNotConfiguredError):
            await factory.get_llm_provider()

    async def test_singleton_returns_same_instance(self, monkeypatch):
        monkeypatch.setattr(factory, "get_settings", lambda: _settings("gemma"))

        first = await factory.get_llm_provider()
        second = await factory.get_llm_provider()

        assert first is second

    async def test_reset_clears_singleton(self, monkeypatch):
        monkeypatch.setattr(factory, "get_settings", lambda: _settings("gemma"))

        first = await factory.get_llm_provider()
        factory.reset_llm_provider()
        second = await factory.get_llm_provider()

        assert first is not second

    async def test_switching_provider_via_config_only(self, monkeypatch):
        """Swapping LLM_PROVIDER changes the implementation, nothing else."""
        monkeypatch.setattr(factory, "get_settings", lambda: _settings("gemma"))
        assert isinstance(await factory.get_llm_provider(), GemmaProvider)

        factory.reset_llm_provider()

        monkeypatch.setattr(factory, "get_settings", lambda: _settings("llama"))
        assert isinstance(await factory.get_llm_provider(), LlamaProvider)


@pytest.mark.asyncio
class TestImageProviderFactory:
    async def test_stable_diffusion_provider_selected(self):
        pytest.skip("Implementation: Phase 4")


@pytest.mark.asyncio
class TestTTSProviderFactory:
    async def test_piper_provider_selected(self):
        pytest.skip("Implementation: Phase 5")
