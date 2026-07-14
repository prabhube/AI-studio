# Prabhu AI Studio — Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│                    Next.js 15 (React 19)                        │
│            http://localhost:3000                                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP / WebSocket
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                       NGINX (Phase 8)                           │
│         Routes /api → Backend │ /* → Frontend                  │
│         Serves /media files directly from disk                  │
└──────────────┬──────────────────────────────────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────┐    ┌─────────────────────────────────────┐
│   FastAPI Backend    │    │         Next.js Frontend             │
│   Port 8000          │    │         Port 3000                    │
│                      │    │                                      │
│  API Layer           │    │  App Router Pages                    │
│  Service Layer       │    │  Feature Components                  │
│  Repository Layer    │    │  TanStack Query (server state)       │
│  Provider Layer      │    │  Zustand (UI state)                  │
│  Task Layer (Celery) │    │  Axios API Client                    │
└──────┬───────────────┘    └─────────────────────────────────────┘
       │
       ├──────────────────────────────────┐
       │                                  │
       ▼                                  ▼
┌──────────────┐                 ┌────────────────┐
│  PostgreSQL  │                 │     Redis       │
│  Port 5432   │                 │  Port 6379      │
│              │                 │                 │
│  Users       │                 │  Celery Broker  │
│  Projects    │                 │  Celery Backend │
│  Videos      │                 │  Rate Limiting  │
│  Images      │                 └────────────────┘
│  AudioClips  │
│  Jobs        │                 ┌────────────────┐
└──────────────┘                 │  Celery Worker │
                                 │                │
                                 │  video queue   │
                                 │  image queue   │
                                 │  audio queue   │
                                 └──────┬─────────┘
                                        │ calls
                                        ▼
                          ┌─────────────────────────┐
                          │    AI Provider Layer     │
                          │                          │
                          │  LLMProvider             │
                          │   └─ GemmaProvider       │
                          │   └─ LlamaProvider       │
                          │                          │
                          │  ImageProvider           │
                          │   └─ StableDiffusion     │
                          │                          │
                          │  TTSProvider             │
                          │   └─ PiperProvider       │
                          │                          │
                          │  STTProvider             │
                          │   └─ WhisperProvider     │
                          │                          │
                          │  VideoProvider           │
                          │   └─ FFmpegProvider      │
                          └─────────────────────────┘
```

---

## Backend Layer Responsibilities

| Layer | Responsibility | Never Does |
|---|---|---|
| **Controller** (endpoints/) | Parse HTTP requests, validate input, return HTTP responses | Business logic, SQL |
| **Service** (services/) | Business rules, orchestration, authorization checks | Direct SQL, HTTP concerns |
| **Repository** (repositories/) | SQL queries, data access | Business logic, HTTP concerns |
| **Provider** (providers/) | AI model inference | Database access, HTTP concerns |
| **Task** (tasks/) | Background job execution | Direct HTTP responses |

---

## AI Provider Architecture

Every AI capability follows the same pattern:

```
Protocol (base/)         Concrete (llm/, image/, ...)    Factory (factory.py)
    │                           │                              │
LLMProvider ──────── implemented by ──► GemmaProvider ◄── get_llm_provider()
                                        LlamaProvider
                                        [FutureProvider]
```

To add a new AI model:
1. Create `new_provider.py` implementing the Protocol
2. Add one `elif` branch in `factory.py`
3. Add the option to `LLMSettings` in `config.py`
**Zero other changes required in services or controllers.**

---

## Request Lifecycle

```
POST /api/v1/videos/generate
         │
         ▼
    RequestIDMiddleware  ← assigns X-Request-ID
         │
    AccessLoggingMiddleware  ← logs method + path
         │
    SlowAPIMiddleware  ← rate limit check (100 req/min/IP)
         │
    CORSMiddleware  ← origin check
         │
    FastAPI routing  ← match to generate_video() endpoint
         │
    Depends(get_current_user)  ← validate JWT token
         │
    VideoService.request_generation()  ← create Video record (pending)
         │
    generate_video.delay()  ← dispatch Celery task
         │
    return 202 Accepted  ← Video with status="pending"
         │
         ▼
    [Background] Celery Worker
         │
    PipelineService.run_video_pipeline()
         │
    LLM → Images → Audio → FFmpeg
         │
    Video.status = "completed"
```

---

## Database Schema

```
users ──────────────────────────────────────────────┐
  id (UUID PK)                                      │
  email (unique)                                    │
  username (unique)                                 │
  hashed_password                                   │
  is_active, is_superuser                           │
  created_at, updated_at, deleted_at                │
                                                    │
projects (FK → users.id)  ──────────────────────   │
  id (UUID PK)                                  │   │
  user_id (FK)  ◄───────────────────────────────┘   │
  name, description, status                         │
  created_at, updated_at, deleted_at                │
                                                    │
videos (FK → projects.id)  ─────────────────────   │
images (FK → projects.id)  ─────────────────────   │
audio_clips (FK → projects.id)  ─────────────────  │
                                                    │
generation_jobs (FK → users.id, projects.id)  ──── │
  Tracks every Celery task. Separate from model     │
  records so job history persists after cleanup.    │
```

---

## Frontend Architecture

```
Page (app/*)
  ├── Fetches data via useXxx() hook
  ├── Renders layout + feature components
  └── Handles navigation/routing

Hook (hooks/useXxx.ts)
  ├── Calls API service
  ├── Manages TanStack Query cache
  └── Returns { data, isLoading, error, mutation }

API Service (lib/xxx-api.ts)
  ├── Calls apiClient (Axios instance)
  └── Returns typed domain objects

apiClient (lib/api-client.ts)
  ├── Injects Bearer token on every request
  └── Auto-refreshes token on 401

Zustand Store (store/ui-store.ts)
  └── Sidebar state, active modal, active project
```

---

## Development Phases

| Phase | Focus | Key Deliverable |
|---|---|---|
| 1 | Foundation | Auth, Docker, DB, Health API |
| 2 | Domain Layer | Projects, Jobs, all CRUD APIs |
| 3 | LLM | Gemma/Llama script generation |
| 4 | Image Generation | Stable Diffusion frames |
| 5 | TTS | Piper voice narration |
| 6 | STT | Whisper transcription |
| 7 | Video Assembly | FFmpeg pipeline |
| 8 | Full Pipeline | End-to-end video from prompt |
| 9 | Frontend UI | Complete React studio interface |
| 10 | Polish | Performance, monitoring, docs |
