"""
Data models used by the EUVD service.
"""

from .advisory import Advisory
from .basescore import BaseScore
from .customfieldtypes import (
    BaseScoreValueType,
    EPSSScoreValueType,
    EUVDIdType,
)
from .enisaidenisavulnerabilityref import EnisaIdEnisaVulnerabilityRef
from .enisaidproductref import EnisaIdProductRef
from .enisaidvendorref import EnisaIdVendorRef
from .enisaidvulnerabilityref import EnisaIdVulnerabilityRef
from .enisavulnerability import EnisaVulnerability
from .pagination import Pagination
from .product import Product
from .source import Source
from .vendor import Vendor
from .vulnerability import Vulnerability

__all__ = [
    "Advisory",
    "BaseScore",
    "BaseScoreValueType",
    "EPSSScoreValueType",
    "EUVDIdType",
    "EnisaIdEnisaVulnerabilityRef",
    "EnisaIdProductRef",
    "EnisaIdVendorRef",
    "EnisaIdVulnerabilityRef",
    "EnisaVulnerability",
    "Pagination",
    "Product",
    "Source",
    "Vendor",
    "Vulnerability",
]
