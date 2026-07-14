"""
Pagination Utilities.

WHY this file exists:
    Keeps pagination math consistent across all list endpoints.
    Instead of computing offset/total_pages inline in every service,
    call these helpers.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PaginationParams:
    """Validated pagination parameters extracted from query params."""

    page: int
    page_size: int

    @property
    def offset(self) -> int:
        """Calculate the SQL OFFSET value."""
        return (self.page - 1) * self.page_size


def calculate_total_pages(total: int, page_size: int) -> int:
    """
    Return the total number of pages for a given total record count.

    Args:
        total:     Total number of records.
        page_size: Records per page.

    Returns:
        Total page count (minimum 1).
    """
    if page_size <= 0:
        return 1
    return max(1, (total + page_size - 1) // page_size)
