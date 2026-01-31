"""
Provides the class that references a vendor as an ENISA vendor ID.
"""

import uuid
from typing import Any

from euvd.models._baseenisaidreference import _BaseEnisaIdReference
from euvd.models.vendor import Vendor


class EnisaIdVendorRef(_BaseEnisaIdReference):
    """
    Represents a vendor as an ENISA vendor ID.
    """

    vendor: Vendor

    def __hash__(self) -> int:
        return hash((self.id, self.vendor))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnisaIdVendorRef":
        """
        Parses a vendor dictionary into an EnisaIdVendor model.

        Args:
            data (dict[str, Any]): The vendor data to parse.

        Returns:
            EnisaIdVendorRef: An instance of the EnisaIdVendorRef class.
        """
        return EnisaIdVendorRef(
            id=uuid.UUID(data["id"]),
            vendor=Vendor(**data["vendor"]),
        )


__all__ = [
    "EnisaIdVendorRef",
]
