"""
Database Seed Script.

WHY this file exists:
    Seeds the database with initial data for development:
      - One default superuser account
      - One sample project
      - Placeholder records to test the UI

    Run: make seed
    Or:  docker compose exec backend python scripts/seed.py

    IMPORTANT: This script is for development only.
               It checks if data already exists before inserting.
               It is safe to run multiple times (idempotent).

Implementation: Phase 2 (after project model is implemented).
"""

import asyncio
import sys
from pathlib import Path

# Add the backend app to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def seed() -> None:
    """
    Seed the database with development data.

    Steps:
      1. Create admin user (if not exists)
      2. Create a sample project (if not exists)

    Implementation: Phase 2.
    """
    print("Database seed — Implementation: Phase 2")
    print("Skipping seed. Run after Phase 2 is complete.")


if __name__ == "__main__":
    asyncio.run(seed())
