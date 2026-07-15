"""
Unit tests for PromptAnalyzerService.

The LLM provider is mocked so these tests are fast, deterministic, and do not
require a real model. They verify the two things the service is responsible
for: driving the provider correctly, and turning its (often messy) output into
a stable, valid PromptAnalysis.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import InvalidInputError, LLMProviderError
from app.schemas.prompt import PromptAnalysis
from app.services.prompt_analyzer_service import PromptAnalyzerService


@pytest.fixture
def provider(monkeypatch):
    """Patch get_llm_provider to return a mock provider; return it for setup."""
    prov = MagicMock()
    prov.model_info.return_value = {"name": "gemma"}
    prov.chat = AsyncMock()
    monkeypatch.setattr(
        "app.services.prompt_analyzer_service.get_llm_provider",
        AsyncMock(return_value=prov),
    )
    return prov


async def test_returns_fully_structured_analysis(provider):
    provider.chat.return_value = json.dumps(
        {
            "topic": "Ocean life",
            "audience": "children",
            "mood": "cheerful",
            "style": "animated",
            "camera": "wide-shot",
            "characters": [
                {"name": "Dory", "description": "a forgetful fish", "role": "protagonist"}
            ],
            "duration_seconds": 60,
            "language": "English",
            "voice": "warm female narrator",
        }
    )

    result = await PromptAnalyzerService().analyze("A fun cartoon about ocean life")

    assert isinstance(result, PromptAnalysis)
    assert result.topic == "Ocean life"
    assert result.audience == "children"
    assert result.mood == "cheerful"
    assert result.style == "animated"
    assert result.camera == "wide-shot"
    assert result.duration_seconds == 60
    assert result.language == "English"
    assert result.voice == "warm female narrator"
    assert len(result.characters) == 1
    assert result.characters[0].name == "Dory"
    assert result.characters[0].role == "protagonist"


async def test_fills_defaults_for_missing_keys(provider):
    provider.chat.return_value = '{"topic": "Space"}'

    result = await PromptAnalyzerService().analyze("space documentary")

    assert result.topic == "Space"
    assert result.audience == "general audience"
    assert result.mood == "neutral"
    assert result.style == "realistic"
    assert result.camera == "static"
    assert result.duration_seconds == 30
    assert result.language == "English"
    assert result.voice == "neutral narrator"
    assert result.characters == []


async def test_strips_markdown_fences(provider):
    provider.chat.return_value = '```json\n{"topic": "Cooking"}\n```'
    result = await PromptAnalyzerService().analyze("a cooking show")
    assert result.topic == "Cooking"


async def test_falls_back_to_prompt_for_topic(provider):
    provider.chat.return_value = '{"audience": "developers"}'
    result = await PromptAnalyzerService().analyze("A tutorial on Kubernetes")
    assert result.topic == "A tutorial on Kubernetes"


async def test_coerces_string_duration(provider):
    provider.chat.return_value = '{"topic": "x", "duration_seconds": "about 45 seconds"}'
    result = await PromptAnalyzerService().analyze("some prompt")
    assert result.duration_seconds == 45


async def test_clamps_out_of_range_duration(provider):
    provider.chat.return_value = '{"topic": "x", "duration_seconds": 999999}'
    result = await PromptAnalyzerService().analyze("some prompt")
    assert result.duration_seconds == 3600


async def test_unknown_mood_is_kept_lowercased(provider):
    provider.chat.return_value = '{"topic": "x", "mood": "EPIC"}'
    result = await PromptAnalyzerService().analyze("some prompt")
    assert result.mood == "epic"


async def test_empty_mood_falls_back_to_default(provider):
    provider.chat.return_value = '{"topic": "x", "mood": ""}'
    result = await PromptAnalyzerService().analyze("some prompt")
    assert result.mood == "neutral"


async def test_characters_from_plain_strings(provider):
    provider.chat.return_value = '{"topic": "x", "characters": ["Alice", "Bob"]}'
    result = await PromptAnalyzerService().analyze("some prompt")
    assert [c.name for c in result.characters] == ["Alice", "Bob"]


async def test_nameless_characters_are_skipped(provider):
    provider.chat.return_value = (
        '{"topic": "x", "characters": [{"description": "no name"}, {"name": "Zoe"}]}'
    )
    result = await PromptAnalyzerService().analyze("some prompt")
    assert [c.name for c in result.characters] == ["Zoe"]


async def test_character_count_is_capped(provider):
    characters = [{"name": f"C{i}"} for i in range(50)]
    provider.chat.return_value = json.dumps({"topic": "x", "characters": characters})
    result = await PromptAnalyzerService().analyze("some prompt")
    assert len(result.characters) == 12


async def test_long_character_name_is_truncated(provider):
    provider.chat.return_value = json.dumps(
        {"topic": "x", "characters": [{"name": "N" * 300}]}
    )
    result = await PromptAnalyzerService().analyze("some prompt")
    assert len(result.characters[0].name) == 120


async def test_empty_prompt_raises_and_skips_llm(provider):
    with pytest.raises(InvalidInputError):
        await PromptAnalyzerService().analyze("  ")
    provider.chat.assert_not_called()


async def test_unparseable_output_raises_llm_error(provider):
    provider.chat.return_value = "Sorry, I can't help with that."
    with pytest.raises(LLMProviderError):
        await PromptAnalyzerService().analyze("some prompt")


async def test_uses_analyzer_generation_settings(provider):
    provider.chat.return_value = '{"topic": "x"}'
    await PromptAnalyzerService().analyze("some prompt")

    # System + user messages sent, with near-deterministic sampling.
    assert provider.chat.await_count == 1
    _, kwargs = provider.chat.await_args
    assert kwargs["temperature"] == 0.2
    messages = provider.chat.await_args.args[0]
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "some prompt"
