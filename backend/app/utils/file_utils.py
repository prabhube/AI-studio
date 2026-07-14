"""
File System Utilities.

WHY this file exists:
    Centralizes all file I/O operations so that:
    1. Business logic never touches os.path or pathlib directly.
    2. File operations can be mocked in tests.
    3. Path validation is consistent across the application.

All functions will be implemented in Phase 4 (image generation introduces file I/O).
"""

import uuid
from pathlib import Path
from typing import Literal


def build_output_path(
    base_dir: str | Path,
    media_type: Literal["image", "audio", "video"],
    extension: str,
) -> Path:
    """
    Build a unique output file path for a generated media asset.

    Args:
        base_dir:   Root media directory from settings.
        media_type: Subdirectory to place the file in.
        extension:  File extension (e.g. "png", "wav", "mp4").

    Returns:
        A unique Path object like: /app/media/images/a1b2c3d4.png
    """
    ...


def ensure_directory(path: Path) -> Path:
    """
    Create a directory and all parents if they don't exist.

    Args:
        path: Directory path to ensure exists.

    Returns:
        The same path (for chaining).
    """
    ...


def safe_delete(path: Path) -> bool:
    """
    Delete a file safely — logs a warning instead of raising on failure.

    Args:
        path: File path to delete.

    Returns:
        True if deleted, False if file did not exist or deletion failed.
    """
    ...


def get_file_size_bytes(path: Path) -> int:
    """
    Return the size of a file in bytes.

    Raises:
        StorageError: If the file does not exist.
    """
    ...
