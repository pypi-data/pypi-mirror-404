"""
This module defines the Source class, which represents the source of an advisory or vulnerability.
"""

from pydantic import BaseModel


class Source(BaseModel):
    """
    Represents the source of an advisory or vulnerability.
    """

    id: int
    name: str


__all__ = [
    "Source",
]
