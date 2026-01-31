"""
This module defines the BaseScore class, which represents the base score of a vulnerability.
"""

from cvss import CVSS2, CVSS3, CVSS4
from pydantic import BaseModel

from euvd.models.customfieldtypes import BaseScoreValueType


class BaseScore(BaseModel):
    """
    Represents the base score of a vulnerability.
    """

    version: str | None = None
    score: BaseScoreValueType
    vector: str | None = None

    @property
    def cvss(self) -> CVSS2 | CVSS3 | CVSS4:
        """
        Converts the base score to a CVSS object based on the version.

        Returns:
            CVSS2 | CVSS3 | CVSS4: The CVSS object corresponding to the version.

        Raises:
            ValueError: If the CVSS vector is not defined or the version is unsupported.
        """
        if self.vector is None or not self.vector:
            raise ValueError("No CVSS vector defined.")
        if self.version is None:
            raise ValueError("No CVSS version defined.")
        if self.version.startswith("3"):
            return CVSS3(self.vector)
        if self.version.startswith("4"):
            return CVSS4(self.vector)
        if self.version.startswith("2"):
            return CVSS2(self.vector)
        raise ValueError(f"Unsupported CVSS version: {self.version}")


__all__ = [
    "BaseScore",
]
