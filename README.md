# Prabhu AI Studio

A local-first AI video generation application. Transform text prompts into complete videos using open-source AI models — everything runs on your own machine. No cloud required.

---

## Architecture Overview

```
prabhu-ai-studio/
├── backend/              FastAPI Python backend
│   ├── app/
│   │   ├── api/          Controllers (endpoint routers)
│   │   ├── core/         Config, security, logging, exceptions
│   │   ├── db/           SQLAlchemy session, Redis client, Base
│   │   ├── middleware/   Request ID middleware
│   │   ├── models/       SQLAlchemy ORM models
│   │   ├── providers/    AI provider abstractions (LLM, Image, TTS, STT, Video)
│   │   ├── repositories/ Data access layer
│   │   ├── schemas/      Pydantic request/response schemas
│   │   ├── services/     Business logic layer
│   │   └── utils/        Shared helpers, exception handlers
│   ├── alembic/          Database migrations
│   └── tests/            Unit, integration, API tests
│
├── frontend/             Next.js 15 + TypeScript frontend
│   └── src/
│       ├── app/          Next.js App Router pages
│       ├── components/   Reusable UI components
│       ├── hooks/        Custom React hooks
│       ├── lib/          API client, utilities
│       ├── styles/       Tailwind + global CSS
│       └── types/        TypeScript type definitions
│
├── infrastructure/
│   ├── docker/           Docker init scripts
│   └── nginx/            Reverse proxy config (Phase 8)
│
├── docs/                 Architecture & API documentation
├── scripts/              Developer helper scripts
└── docker-compose.yml    Full stack orchestration
```

---

## Technology Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Backend    | Python 3.12, FastAPI, SQLAlchemy 2, Alembic     |
| Database   | PostgreSQL 16                                   |
| Cache      | Redis 7                                         |
| Frontend   | Next.js 15, React 19, TypeScript, Tailwind CSS  |
| AI — LLM   | Llama / Gemma (via llama.cpp)                   |
| AI — Image | Stable Diffusion                                |
| AI — TTS   | Piper TTS                                       |
| AI — STT   | OpenAI Whisper                                  |
| AI — Video | FFmpeg                                          |
| Container  | Docker + Docker Compose                         |

---

## Quick Start

### Prerequisites

- Docker Desktop (Windows/macOS) or Docker + Docker Compose (Linux)
- Git

### 1. Clone and configure

```bash
git clone <repo-url>
cd prabhu-ai-studio

# Copy and edit environment variables
cp .env.example .env
# Edit .env — at minimum change APP_SECRET_KEY and JWT_SECRET_KEY
```

### 2. Start all services

```bash
docker compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- FastAPI backend on port 8000
- Next.js frontend on port 3000

### 3. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Open the application

| Service        | URL                              |
|----------------|----------------------------------|
| Frontend       | http://localhost:3000            |
| Backend API    | http://localhost:8000/api/v1     |
| API Docs       | http://localhost:8000/api/docs   |
| Health Check   | http://localhost:8000/api/v1/health |

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
.venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy env and configure
cp ../.env.example ../.env

# Start PostgreSQL and Redis manually or via Docker:
docker compose up postgres redis -d

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

npm install
npm run dev
# Frontend available at http://localhost:3000
```

---

## Running Tests

```bash
cd backend

# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests with coverage
pytest

# Run specific test modules
pytest tests/unit/test_core/test_security.py -v
pytest tests/api/ -v
```

---

## Development Roadmap

| Phase | Description                                    | Status      |
|-------|------------------------------------------------|-------------|
| 1     | Project Foundation & Architecture              | ✅ Complete |
| 2     | AI Provider Abstraction Layer                  | Pending     |
| 3     | LLM Integration (Gemma / Llama)                | Pending     |
| 4     | Image Generation (Stable Diffusion)            | Pending     |
| 5     | Text-to-Speech (Piper TTS)                     | Pending     |
| 6     | Speech-to-Text (Whisper)                       | Pending     |
| 7     | Video Assembly (FFmpeg)                        | Pending     |
| 8     | End-to-End Video Pipeline                      | Pending     |
| 9     | Frontend — Full Video Studio UI                | Pending     |
| 10    | Performance, Polish & Documentation            | Pending     |

---

## API Reference

Interactive API docs are available at `http://localhost:8000/api/docs` in development mode.

### Authentication Endpoints

| Method | Path                    | Description              |
|--------|-------------------------|--------------------------|
| POST   | /api/v1/auth/register   | Create a new account     |
| POST   | /api/v1/auth/login      | Login and get JWT tokens |
| POST   | /api/v1/auth/refresh    | Refresh access token     |

### User Endpoints

| Method | Path               | Auth Required | Description              |
|--------|--------------------|---------------|--------------------------|
| GET    | /api/v1/users/me   | User          | Get current user profile |
| PATCH  | /api/v1/users/me   | User          | Update current user      |
| GET    | /api/v1/users/     | Superuser     | List all users           |
| GET    | /api/v1/users/{id} | Superuser     | Get user by ID           |

### Health

| Method | Path              | Description       |
|--------|-------------------|-------------------|
| GET    | /api/v1/health    | Service health    |

---

## Security Notes

- Passwords are hashed with bcrypt (cost factor 12).
- JWTs use HS256 with configurable expiry.
- All secrets must be set via environment variables — never hardcoded.
- CORS is restricted to configured origins.
- Rate limiting is applied per IP via SlowAPI.
- Soft-delete is implemented for audit trail preservation.

---

## Contributing

This is a personal-use v1 project. Code follows:
- SOLID principles
- Clean Architecture (Controllers → Services → Repositories → Models)
- Repository Pattern
- Async-first design (asyncpg, async SQLAlchemy, async Redis)
- Type hints throughout
- Structured logging with structlog
