"""
This module defines several globally-used basic data types.
"""

from typing import Annotated

from pydantic import Field

EUVDIdType = Annotated[str, Field(pattern=r"EUVD-\d+-\d+")]
BaseScoreValueType = Annotated[float | None, Field(ge=0.0, le=10.0)]
EPSSScoreValueType = Annotated[float | None, Field(ge=0.0, le=100.0)]


__all__ = [
    "BaseScoreValueType",
    "EPSSScoreValueType",
    "EUVDIdType",
]
