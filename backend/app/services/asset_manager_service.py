"""
Asset Manager Service.

Manages the file-system session for one pipeline run.

Each pipeline run gets a UUID session ID. All generated files live under:
  {media_root}/pipeline/{session_id}/
    images/    — scene images (scene_0.png, scene_1.png, …)
    audio/     — narration.mp3, music.mp3
    subtitles/ — subtitles.srt
    video/     — assembled.mp4, final.mp4
    state.json — session metadata

The service is stateless: every call receives the session_id and derives the
paths from it. No database records — this keeps the pipeline independent of
the DB migration state.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Session dataclass
# ---------------------------------------------------------------------------

@dataclass
class SessionAssets:
    session_id: str
    root_dir: str
    images_dir: str
    audio_dir: str
    subtitles_dir: str
    video_dir: str
    image_paths: list[str] = field(default_factory=list)
    narration_path: str = ""
    music_path: str = ""
    subtitle_path: str = ""
    assembled_video_path: str = ""
    final_video_path: str = ""
    status: str = "created"
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AssetManagerService:
    """Creates and manages pipeline session directories and asset tracking."""

    def get_media_root(self) -> Path:
        settings = get_settings()
        media = Path(settings.media_root)
        # On Windows the default Linux-style path won't work; fall back to a
        # local 'media' directory beside the backend folder.
        if not media.is_absolute() or (str(media).startswith("/") and not media.exists()):
            import sys
            if sys.platform == "win32":
                # Place outputs in backend/media/ so the path always works
                backend_dir = Path(__file__).resolve().parents[3]
                media = backend_dir / "media"
        media.mkdir(parents=True, exist_ok=True)
        return media

    def get_session_root(self, session_id: str) -> Path:
        return self.get_media_root() / "pipeline" / session_id

    def create_session(self) -> SessionAssets:
        """
        Create a new pipeline session with a fresh UUID.
        Returns a SessionAssets with all paths pre-computed.
        """
        session_id = str(uuid.uuid4())
        root = self.get_session_root(session_id)

        dirs = {
            "images": root / "images",
            "audio": root / "audio",
            "subtitles": root / "subtitles",
            "video": root / "video",
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        session = SessionAssets(
            session_id=session_id,
            root_dir=str(root),
            images_dir=str(dirs["images"]),
            audio_dir=str(dirs["audio"]),
            subtitles_dir=str(dirs["subtitles"]),
            video_dir=str(dirs["video"]),
        )
        self._save_state(session)

        logger.info("pipeline_session_created", session_id=session_id)
        return session

    def get_session(self, session_id: str) -> SessionAssets | None:
        """Load an existing session from its state.json."""
        state_path = self.get_session_root(session_id) / "state.json"
        if not state_path.exists():
            return None
        try:
            with open(state_path) as f:
                data = json.load(f)
            return SessionAssets(**data)
        except Exception:
            return None

    def update_session(self, session: SessionAssets) -> None:
        """Persist updated session state to disk."""
        self._save_state(session)

    def image_path(self, session_id: str, scene_index: int) -> Path:
        return self.get_session_root(session_id) / "images" / f"scene_{scene_index:03d}.png"

    def narration_path(self, session_id: str) -> Path:
        return self.get_session_root(session_id) / "audio" / "narration.mp3"

    def music_path(self, session_id: str) -> Path:
        return self.get_session_root(session_id) / "audio" / "music.mp3"

    def subtitle_path(self, session_id: str) -> Path:
        return self.get_session_root(session_id) / "subtitles" / "subtitles.srt"

    def assembled_video_path(self, session_id: str) -> Path:
        return self.get_session_root(session_id) / "video" / "assembled.mp4"

    def final_video_path(self, session_id: str) -> Path:
        return self.get_session_root(session_id) / "video" / "final.mp4"

    def _save_state(self, session: SessionAssets) -> None:
        state_path = Path(session.root_dir) / "state.json"
        with open(state_path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
