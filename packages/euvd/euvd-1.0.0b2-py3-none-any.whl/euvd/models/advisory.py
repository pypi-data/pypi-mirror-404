"""
This module defines the Advisory class.
"""

import datetime
from typing import Any

from pydantic import Field

from euvd.models._baserecord import _BaseRecord
from euvd.models.basescore import BaseScore
from euvd.models.enisaidenisavulnerabilityref import EnisaIdEnisaVulnerabilityRef
from euvd.models.enisaidproductref import EnisaIdProductRef
from euvd.models.source import Source


class Advisory(_BaseRecord):
    """
    Encapsulates an advisory.
    """

    id: str
    summary: str | None = None
    source: Source | None = None
    products: set[EnisaIdProductRef] = Field(default_factory=set)
    enisa_vulnerabilities: set[EnisaIdEnisaVulnerabilityRef] = Field(default_factory=set)

    def __hash__(self) -> int:
        return hash((self.id,))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Advisory":
        """
        Parses a dictionary into an Advisory instance.

        Args:
            data (dict[str, Any]): The advisory data to parse.

        Returns:
            Advisory: An instance of the Advisory class.

        Raises:
            ValueError: If parsing fails due to invalid data.
        """
        try:
            return Advisory(
                id=data["id"],
                description=data["description"],
                summary=data.get("summary"),
                date_published=datetime.datetime.strptime(
                    data["datePublished"],
                    "%b %d, %Y, %I:%M:%S %p",
                ),
                date_updated=datetime.datetime.strptime(
                    data["dateUpdated"],
                    "%b %d, %Y, %I:%M:%S %p",
                ),
                base_score=BaseScore(
                    score=data.get("baseScore", 0.0),
                    version=data.get("baseScoreVersion", "2"),
                    vector=data.get("baseScoreVector"),
                )
                if data.get("baseScore", -1.0) >= 0
                else None,
                references=set(data.get("references", "").strip().split("\n")),
                aliases=set(data.get("aliases", "").strip().split("\n")),
                products=set(
                    map(
                        EnisaIdProductRef.from_dict,
                        data.get("advisoryProduct", []),
                    )
                ),
                enisa_vulnerabilities=set(
                    map(
                        EnisaIdEnisaVulnerabilityRef.from_dict,
                        data.get("enisaIdAdvisories", []),
                    )
                ),
            )
        except Exception as e:
            raise ValueError(f"Failed to parse advisory: {data}") from e


__all__ = [
    "Advisory",
]
