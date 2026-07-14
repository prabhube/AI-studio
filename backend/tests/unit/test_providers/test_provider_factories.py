"""
Provider Factory Unit Tests.

WHY: Tests that factories correctly resolve providers from settings
     and raise ProviderNotConfiguredError when set to "none".

Tests to implement:
    - get_llm_provider() returns GemmaProvider when LLM_PROVIDER=gemma
    - get_llm_provider() returns LlamaProvider when LLM_PROVIDER=llama
    - get_llm_provider() raises ProviderNotConfiguredError when none
    - get_image_provider() returns StableDiffusionProvider correctly
    - get_tts_provider() returns PiperProvider correctly
    - get_stt_provider() returns WhisperProvider correctly
    - get_video_provider() returns FFmpegProvider correctly
    - All factories return singleton (same object on second call)
    - reset_*_provider() functions clear the singleton for next test

Implementation: Phase 2 (provider abstraction phase).
"""

import pytest


@pytest.mark.asyncio
class TestLLMProviderFactory:
    async def test_gemma_provider_selected_when_configured(self):
        pytest.skip("Implementation: Phase 2")

    async def test_none_raises_provider_not_configured_error(self):
        pytest.skip("Implementation: Phase 2")

    async def test_singleton_returns_same_instance(self):
        pytest.skip("Implementation: Phase 2")


@pytest.mark.asyncio
class TestImageProviderFactory:
    async def test_stable_diffusion_provider_selected(self):
        pytest.skip("Implementation: Phase 4")


@pytest.mark.asyncio
class TestTTSProviderFactory:
    async def test_piper_provider_selected(self):
        pytest.skip("Implementation: Phase 5")
