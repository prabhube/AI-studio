# Development Roadmap

## Phase Status

| Phase | Name | Status | Key Deliverables |
|---|---|---|---|
| **1** | Foundation | ✅ Complete | Docker, PostgreSQL, Redis, FastAPI core, JWT auth, Next.js shell |
| **2** | Domain Layer | 🔜 Next | Projects CRUD, Jobs API, all repositories implemented |
| **3** | LLM Integration | ⏳ Pending | Gemma/Llama script generation, scene planning |
| **4** | Image Generation | ⏳ Pending | Stable Diffusion frames, upscaling |
| **5** | TTS | ⏳ Pending | Piper voice synthesis, voice selection |
| **6** | STT | ⏳ Pending | Whisper transcription, subtitle generation |
| **7** | Video Assembly | ⏳ Pending | FFmpeg pipeline, transitions, subtitles |
| **8** | Full Pipeline | ⏳ Pending | Prompt → complete video, job monitoring |
| **9** | Frontend UI | ⏳ Pending | Complete React studio, video player, gallery |
| **10** | Polish | ⏳ Pending | Performance, monitoring, final documentation |

---

## Phase 2 — Domain Layer

**Goal:** Implement all repositories, services, and endpoints for Projects and Jobs.
**No AI required** — pure CRUD with authorization.

Deliverables:
- `ProjectRepository` — get_by_user_id, count queries
- `ProjectService` — create, list, get, update, soft-delete with auth checks
- `JobRepository` — mark_completed, mark_failed, update_progress
- All project endpoints fully implemented (POST, GET, PATCH, DELETE)
- React `useProjects()` hook connected to real API
- `ProjectCard` and `ProjectList` components
- Seed script with sample data

---

## Phase 3 — LLM Integration

**Goal:** Generate video scripts from text prompts using Gemma or Llama.

Deliverables:
- `GemmaProvider` and `LlamaProvider` fully implemented
- `PipelineService.generate_script()` — structured JSON output
- `PipelineService.generate_image_prompts()` — one prompt per scene
- LLM health check in `/health` endpoint
- Unit tests with mocked LLM responses
- Model download guide in README

---

## Phase 4 — Image Generation

**Goal:** Generate images for each video frame using Stable Diffusion.

Deliverables:
- `StableDiffusionProvider` fully implemented via diffusers
- `ImageService.request_generation()` dispatches Celery task
- `generate_image` Celery task fully implemented
- Image gallery on frontend
- Progress polling via useVideoStatus hook
- Tests with mocked SD pipeline

---

## Phase 5 — TTS

**Goal:** Synthesize voice narration using Piper TTS.

Deliverables:
- `PiperProvider` fully implemented
- `AudioService.request_tts()` dispatches Celery task
- `synthesize_speech` Celery task fully implemented
- Voice Studio page on frontend
- Voice selection dropdown populated from `/audio/voices`

---

## Phase 6 — STT

**Goal:** Transcribe audio using Whisper, generate subtitles.

Deliverables:
- `WhisperProvider` fully implemented
- SRT subtitle file generation
- `transcribe_audio` Celery task implemented
- Language auto-detection

---

## Phase 7 — Video Assembly

**Goal:** Combine frames + audio into a complete video using FFmpeg.

Deliverables:
- `FFmpegProvider` fully implemented
- Transitions: fade, slide, zoom
- Subtitle burning (SRT → video)
- Thumbnail extraction
- Video duration / metadata extraction

---

## Phase 8 — Full Pipeline

**Goal:** One prompt → complete video, fully automated.

Deliverables:
- `PipelineService.run_video_pipeline()` complete
- `generate_video` Celery task chaining all steps
- Real-time progress reporting (0% → 100%)
- Video detail page with player + frame gallery
- Error handling and partial failure recovery

---

## Phase 9 — Frontend UI

**Goal:** Complete, polished React studio interface.

Deliverables:
- Video generator multi-step form
- Real-time generation progress UI
- Video player with download/share
- Image gallery with lightbox
- Voice studio with waveform preview
- Settings page with provider config
- Mobile-responsive layout

---

## Phase 10 — Polish & Documentation

**Goal:** Production-ready local application.

Deliverables:
- Nginx reverse proxy configuration
- Performance profiling and optimization
- Complete API documentation (OpenAPI)
- User guide with screenshots
- Developer onboarding guide
- Model download automation scripts
