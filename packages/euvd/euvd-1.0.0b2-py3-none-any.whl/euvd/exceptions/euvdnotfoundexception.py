"""
Provides the class for the exception when a resource was not found in the EUVD.
"""

from euvd.exceptions.euvdexception import EUVDException


class EUVDNotFoundException(EUVDException):
    """
    Encapsulates a "not found" exception.
    """

    def __init__(self, message: str):
        super().__init__(message)

    def __str__(self) -> str:
        return f"EUVDNotFoundException: {self.message}"


__all__ = [
    "EUVDNotFoundException",
]
