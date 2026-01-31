"""
This module defines the Product class, which represents a generic product.
"""

from pydantic.dataclasses import dataclass


@dataclass
class Product:
    """
    Represents a generic product.
    """

    name: str

    def __hash__(self) -> int:
        return hash(self.name)


__all__ = [
    "Product",
]
