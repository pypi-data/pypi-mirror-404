"""
Provides the base class for all exceptions semantically specific to the EUVD.
"""


class EUVDException(Exception):
    """
    Base class for all exceptions specific to the EUVD.
    """

    def __init__(self, message: str):
        """
        Initialize the EUVDException with a message.

        Args:
            message (str): The error message.
        """
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return f"EUVDException: {self.message}"


__all__ = [
    "EUVDException",
]
