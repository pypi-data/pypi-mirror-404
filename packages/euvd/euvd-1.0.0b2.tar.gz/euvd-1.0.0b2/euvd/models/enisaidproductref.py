"""
This module defines the EnisaIdProductRef class, which represents a product as an ENISA product ID.
"""

import uuid
from typing import Any

from euvd.models._baseenisaidreference import _BaseEnisaIdReference
from euvd.models.product import Product


class EnisaIdProductRef(_BaseEnisaIdReference):
    """
    Represents a product as an ENISA product ID.
    """

    product: Product
    product_version: str | None = None

    def __hash__(self) -> int:
        return hash((self.id, self.product, self.product_version))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnisaIdProductRef":
        """
        Parses a product dictionary into an EnisaIdProductRef instance.

        Args:
            data (dict[str, Any]): The product data to parse.

        Returns:
            EnisaIdProductRef: An instance of the EnisaIdProductRef class.
        """
        return EnisaIdProductRef(
            id=uuid.UUID(data["id"]),
            product=Product(**data["product"]),
            product_version=data.get("productVersion"),
        )


__all__ = [
    "EnisaIdProductRef",
]
