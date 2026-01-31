"""
This module defines the base class for ENISA ID references, providing a UUID-based identifier.
"""

import uuid

from pydantic import BaseModel, ConfigDict


class _BaseEnisaIdReference(BaseModel):
    """
    Base class for ENISA references.
    """

    model_config = ConfigDict(json_encoders={uuid.UUID: str})

    id: uuid.UUID


__all__ = [
    "_BaseEnisaIdReference",
]
