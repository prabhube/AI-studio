"""
V1 API Router — Aggregates all v1 endpoint routers.

WHY this file exists:
    Single point of router registration for API version 1.
    Adding a new feature module = one include_router() call here.
    main.py only sees one router: api_router.

Versioning strategy:
    /api/v1/...  — current version
    /api/v2/...  — future version (new router.py in api/v2/)
    Both versions can run simultaneously during migration periods.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import audio, auth, health, images, projects, users, videos

api_router = APIRouter()

# ---- Public (no auth required) ----
api_router.include_router(health.router)
api_router.include_router(auth.router)

# ---- Authenticated ----
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(videos.router)
api_router.include_router(images.router)
api_router.include_router(audio.router)
