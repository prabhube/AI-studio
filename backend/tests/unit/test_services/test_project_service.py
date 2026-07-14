"""
ProjectService Unit Tests — Placeholders.

WHY: Verifies project business rules without a real database.

Tests to implement:
    - create() creates a project with correct owner
    - get_by_id() raises ResourceNotFoundError for missing project
    - get_by_id() raises AuthorizationError when user doesn't own project
    - list_for_user() returns only the requesting user's projects
    - update() raises AuthorizationError for non-owner
    - delete() soft-deletes project (deleted_at is set)

Implementation: Phase 2.
"""

import pytest


@pytest.mark.asyncio
class TestProjectServiceCreate:
    async def test_create_sets_correct_owner(self):
        pytest.skip("Implementation: Phase 2")


@pytest.mark.asyncio
class TestProjectServiceAuthorization:
    async def test_get_raises_error_for_wrong_user(self):
        pytest.skip("Implementation: Phase 2")

    async def test_update_raises_error_for_wrong_user(self):
        pytest.skip("Implementation: Phase 2")

    async def test_delete_raises_error_for_wrong_user(self):
        pytest.skip("Implementation: Phase 2")
