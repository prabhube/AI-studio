"""
ORM Mixin Unit Tests.

WHY: Verifies that UUIDMixin, TimestampMixin, and SoftDeleteMixin
     work correctly — these underpin every model in the application.

Tests to implement:
    - UUIDMixin generates valid UUID4 on creation
    - TimestampMixin sets created_at and updated_at on creation
    - SoftDeleteMixin.soft_delete() sets deleted_at to now
    - SoftDeleteMixin.is_deleted returns True after soft_delete()
    - Hard deletion via BaseRepository.delete_by_id() removes the row

Implementation: Phase 1 tests (existing test suite).
"""

import pytest


class TestUUIDMixin:
    def test_id_is_uuid4(self):
        pytest.skip("Add to test_core in Phase 1 tests")


class TestSoftDeleteMixin:
    def test_is_deleted_false_by_default(self):
        pytest.skip("Add in Phase 2")

    def test_soft_delete_sets_deleted_at(self):
        pytest.skip("Add in Phase 2")
