# AI Provider Architecture

## Design Principle: Plug-in Providers

All AI capabilities are hidden behind **Protocol interfaces**.
The application's services interact only with the interface, never the concrete provider.

This means: swap Gemma for Llama by changing **one environment variable**.

---

## Provider Contract (base/)

Each provider type defines a Python `Protocol`:

```python
# base/llm_provider.py
class LLMProvider(Protocol):
    async def generate(self, prompt: str, ...) -> str: ...
    async def chat(self, messages: list[dict], ...) -> str: ...
    async def is_available(self) -> bool: ...
    def model_info(self) -> dict[str, str]: ...
```

`@runtime_checkable` means `isinstance(obj, LLMProvider)` works via duck typing.
No inheritance required — just implement the methods.

---

## Provider Registry

| Capability | Protocol | Current Provider | Future Options |
|---|---|---|---|
| Text Generation | `LLMProvider` | Gemma, Llama | Mistral, Phi, Qwen |
| Image Generation | `ImageProvider` | Stable Diffusion 1.5 | FLUX, SDXL, ControlNet |
| Text-to-Speech | `TTSProvider` | Piper TTS | Coqui, Bark, Kokoro |
| Speech-to-Text | `STTProvider` | Whisper | faster-whisper |
| Video Assembly | `VideoProvider` | FFmpeg | MoviePy, RunwayML local |

---

## Factory Pattern

Each provider type has a factory function:

```python
async def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm.provider == "gemma":
        return GemmaProvider(settings.llm)
    elif settings.llm.provider == "llama":
        return LlamaProvider(settings.llm)
    else:
        raise ProviderNotConfiguredError("llm")
```

- **Singleton**: Factory caches the instance after first call.
- **Lazy loading**: Model files are loaded on first provider access, not at startup.
- **Test reset**: `reset_llm_provider()` clears the singleton for testing.

---

## Adding a New Provider (Step-by-Step)

Example: Adding Mistral as a third LLM option.

**Step 1:** Create `backend/app/providers/llm/mistral_provider.py`
```python
class MistralProvider:
    def __init__(self, settings) -> None: ...
    async def generate(self, prompt: str, **kwargs) -> str: ...
    async def chat(self, messages: list[dict], **kwargs) -> str: ...
    async def is_available(self) -> bool: ...
    def model_info(self) -> dict[str, str]: ...
```

**Step 2:** Add to `factory.py`
```python
elif provider_name == "mistral":
    from app.providers.llm.mistral_provider import MistralProvider
    _provider_instance = MistralProvider(settings.llm)
```

**Step 3:** Extend `LLMSettings` in `config.py`
```python
provider: Literal["gemma", "llama", "mistral", "none"] = ...
```

**Step 4:** Update `.env`
```
LLM_PROVIDER=mistral
LLM_MODEL_PATH=/models/llm/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

**Zero other changes.** No service changes. No controller changes. No test changes.

---

## Value Objects for Provider Requests

Each provider uses immutable `dataclass(frozen=True)` value objects:

```python
@dataclass(frozen=True)
class ImageGenerationRequest:
    prompt: str
    width: int = 512
    height: int = 512
    # ...
```

**WHY frozen dataclasses?**
- Immutable: can't accidentally mutate parameters mid-pipeline
- Hashable: can be cached and used as dict keys
- Type-safe: validated at construction time
- Self-documenting: all parameters visible in one place

---

## Provider Health Checks

Every provider implements `is_available() -> bool`.
The `/api/v1/health` endpoint calls all configured providers:

```json
{
  "status": "degraded",
  "services": {
    "postgres": "ok",
    "redis": "ok",
    "llm": "error: model file not found",
    "image": "ok",
    "tts": "ok"
  }
}
```

This lets you see immediately which models are loaded without running inference.
