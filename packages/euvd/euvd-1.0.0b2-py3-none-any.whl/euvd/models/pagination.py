"""
This module defines the Pagination class, which provides functionality for paginated responses.
"""

import math
from dataclasses import dataclass


@dataclass
class Pagination:
    """
    Pagination model for paginated responses.
    """

    page: int
    page_size: int
    total_items: int

    def __post_init__(self) -> None:
        """
        Validates the initialization parameters.

        Raises:
            ValueError: If page, page_size, or total_items are invalid.
        """
        if self.page < 1:
            raise ValueError("Page number must be at least 1.")
        if self.page_size < 1:
            raise ValueError("Page size must be at least 1.")
        if self.page_size > 100:
            raise ValueError("Page size must be at most 100.")
        if self.total_items < 0:
            raise ValueError("Total items cannot be negative.")

    @property
    def total_pages(self) -> int:
        """
        Calculate the total number of pages.

        Returns:
            int: The total number of pages.
        """
        return int(math.ceil(self.total_items / self.page_size))

    @property
    def has_next(self) -> bool:
        """
        Check if there is a next page.

        Returns:
            bool: True if there is a next page, False otherwise.
        """
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """
        Check if there is a previous page.

        Returns:
            bool: True if there is a previous page, False otherwise.
        """
        return self.page > 1

    @property
    def next_page(self) -> int | None:
        """
        Get the next page number if it exists.

        Returns:
            int | None: The next page number, or None if there is no next page.
        """
        return self.page + 1 if self.has_next else None

    @property
    def previous_page(self) -> int | None:
        """
        Get the previous page number if it exists.

        Returns:
            int | None: The previous page number, or None if there is no previous page.
        """
        return self.page - 1 if self.has_previous else None


__all__ = [
    "Pagination",
]
