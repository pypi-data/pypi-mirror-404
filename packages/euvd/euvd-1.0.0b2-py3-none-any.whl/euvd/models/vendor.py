"""
This module defines the Vendor class, which represents a generic vendor.
"""

from pydantic.dataclasses import dataclass


@dataclass
class Vendor:
    """
    Represents a generic vendor.
    """

    name: str

    def __hash__(self) -> int:
        return hash(self.name)


__all__ = [
    "Vendor",
]
