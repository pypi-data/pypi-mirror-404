"""
Base HTTP client for the EUVD API.
"""

import datetime
import math
from typing import Any

import httpx

from euvd.exceptions import (
    EUVDException,
    EUVDNotFoundException,
)
from euvd.models import EnisaVulnerability


class _BaseClient:
    def _parse_vulnerabilities(self, vulnerabilities: list[dict[str, Any]]) -> list[EnisaVulnerability]:
        """
        Parse a list of vulnerability dictionaries into EnisaVulnerability instances.

        :param vulnerabilities: List of vulnerability data dictionaries
        :return: List of parsed EnisaVulnerability objects
        """
        parsed_vulnerabilities: list[EnisaVulnerability] = list(
            map(
                EnisaVulnerability.from_dict,
                vulnerabilities,
            )
        )

        return parsed_vulnerabilities

    def _prepare_get_latest_vulnerabilities_request(self) -> dict[str, Any]:
        """
        Prepare HTTP request arguments for retrieving latest vulnerabilities.

        :return: Dictionary with HTTP request method and URL
        """
        request_args: dict[str, Any] = {
            "method": "GET",
            "url": "/lastvulnerabilities",
        }

        return request_args

    def _handle_get_latest_vulnerabilities_request_errors(self, response: httpx.Response) -> None:
        """
        Handle errors from the get latest vulnerabilities request.

        :param response: HTTP response object
        :raises EUVDException: If the response indicates an error
        """
        if not response.is_success:
            raise EUVDException(
                f"Failed to retrieve latest vulnerabilities: {response.status_code} {response.reason_phrase}",
            )

    def _prepare_get_latest_exploited_vulnerabilities_request(self) -> dict[str, Any]:
        """
        Prepare HTTP request arguments for retrieving latest exploited vulnerabilities.

        :return: Dictionary with HTTP request method and URL
        """
        request_args: dict[str, Any] = {
            "method": "GET",
            "url": "/exploitedvulnerabilities",
        }

        return request_args

    def _handle_get_latest_exploited_vulnerabilities_request_errors(self, response: httpx.Response) -> None:
        """
        Handle errors from the get latest exploited vulnerabilities request.

        :param response: HTTP response object
        :raises EUVDException: If the response indicates an error
        """
        if not response.is_success:
            raise EUVDException(
                f"Failed to retrieve latest exploited vulnerabilities: {response.status_code} {response.reason_phrase}",
            )

    def _prepare_get_latest_critical_vulnerabilities_request(self) -> dict[str, Any]:
        """
        Prepare HTTP request arguments for retrieving latest critical vulnerabilities.

        :return: Dictionary with HTTP request method and URL
        """
        request_args: dict[str, Any] = {
            "method": "GET",
            "url": "/criticalvulnerabilities",
        }

        return request_args

    def _handle_get_latest_critical_vulnerabilities_response_errors(self, response: httpx.Response) -> None:
        """
        Handle errors from the get latest critical vulnerabilities request.

        :param response: HTTP response object
        :raises EUVDException: If the response indicates an error
        """
        if not response.is_success:
            raise EUVDException(
                f"Failed to retrieve latest critical vulnerabilities: {response.status_code} {response.reason_phrase}",
            )

    def _prepare_search_vulnerabilities_request(
        self,
        from_score: float | None = None,
        to_score: float | None = None,
        from_epss: float | None = None,
        to_epss: float | None = None,
        from_date: datetime.date | None = None,
        to_date: datetime.date | None = None,
        product: str | None = None,
        vendor: str | None = None,
        assigner: str | None = None,
        exploited: bool | None = None,
        text: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """
        Prepare HTTP request arguments for searching vulnerabilities with filters.

        :param from_score: Minimum CVSS score filter
        :param to_score: Maximum CVSS score filter
        :param from_epss: Minimum EPSS score filter
        :param to_epss: Maximum EPSS score filter
        :param from_date: Start date filter
        :param to_date: End date filter
        :param product: Product name filter
        :param vendor: Vendor name filter
        :param assigner: Assigner name filter
        :param exploited: Exploited status filter
        :param text: Text search filter
        :param page: Page number for pagination
        :param page_size: Number of items per page
        :return: Dictionary with HTTP request method, URL, and parameters
        :raises ValueError: If any validation constraint is violated
        """
        if from_score is not None and to_score is not None and from_score > to_score:
            raise ValueError("from_score cannot be greater than to_score")
        if from_epss is not None and to_epss is not None and from_epss > to_epss:
            raise ValueError("from_epss cannot be greater than to_epss")
        if from_date is not None and to_date is not None and from_date > to_date:
            raise ValueError("from_date cannot be greater than to_date")
        if page < 1:
            raise ValueError("page must be greater than or equal to 1")
        if page_size < 1:
            raise ValueError("page_size must be greater than or equal to 1")
        if page_size > 100:
            raise ValueError("page_size must be lower than or equal to 100")
        request_params: dict[str, Any] = {}
        if from_score is not None:
            if from_score < 0 or from_score > 10:
                raise ValueError("from_score must be between 0 and 10")
            request_params["fromScore"] = from_score
        if to_score is not None:
            if to_score < 0 or to_score > 10:
                raise ValueError("to_score must be between 0 and 10")
            request_params["toScore"] = to_score
        if from_epss is not None:
            if from_epss < 0.0 or from_epss > 100.0:
                raise ValueError("from_epss must be between 0.0 and 100.0")
            request_params["fromEpss"] = int(math.floor(from_epss))
        if to_epss is not None:
            if to_epss < 0.0 or to_epss > 100.0:
                raise ValueError("to_epss must be between 0.0 and 100.0")
            request_params["toEpss"] = int(math.ceil(to_epss))
        if from_date is not None:
            request_params["fromDate"] = from_date.isoformat()
        if to_date is not None:
            request_params["toDate"] = to_date.isoformat()
        if product is not None:
            request_params["product"] = product
        if vendor is not None:
            request_params["vendor"] = vendor
        if assigner is not None:
            request_params["assigner"] = assigner
        if exploited is not None:
            request_params["exploited"] = str(exploited).lower()
        if text is not None:
            request_params["text"] = text
        request_params["page"] = page - 1  # Convert to zero-based index
        request_params["size"] = page_size
        request_args: dict[str, Any] = {
            "method": "GET",
            "url": "/search",
            "params": request_params,
        }

        return request_args

    def _handle_search_vulnerabilities_response_errors(self, response: httpx.Response) -> None:
        """
        Handle errors from the search vulnerabilities request.

        :param response: HTTP response object
        :raises EUVDException: If the response indicates an error
        """
        if not response.is_success:
            raise EUVDException(
                f"Failed to find vulnerabilities: {response.status_code} {response.reason_phrase}",
            )

    def _prepare_get_vulnerability_request(self, vulnerability_id: str) -> dict[str, Any]:
        """
        Prepare HTTP request arguments for retrieving a specific vulnerability.

        :param vulnerability_id: ID of the vulnerability to retrieve
        :return: Dictionary with HTTP request method, URL, and parameters
        """
        request_args: dict[str, Any] = {
            "method": "GET",
            "url": "/enisaid",
            "params": {
                "id": vulnerability_id,
            },
        }

        return request_args

    def _handle_get_vulnerability_response_errors(self, vulnerability_id: str, response: httpx.Response) -> None:
        """
        Handle errors from the get vulnerability request.

        :param vulnerability_id: ID of the requested vulnerability
        :param response: HTTP response object
        :raises EUVDException: If the response indicates an error
        :raises EUVDNotFoundException: If the vulnerability is not found
        """
        if response.status_code in (404, 204):
            raise EUVDNotFoundException(
                f"Vulnerability with ID {vulnerability_id} not found.",
            )
        if not response.is_success:
            raise EUVDException(
                f"Failed to retrieve vulnerability: {response.status_code} {response.reason_phrase}",
            )

    def _prepare_get_advisory_request(self, advisory_id: str) -> dict[str, Any]:
        """
        Prepare HTTP request arguments for retrieving a specific advisory.

        :param advisory_id: ID of the advisory to retrieve
        :return: Dictionary with HTTP request method, URL, and parameters
        """
        request_args: dict[str, Any] = {
            "method": "GET",
            "url": "/advisory",
            "params": {
                "id": advisory_id,
            },
        }

        return request_args

    def _handle_get_advisory_response_errors(self, advisory_id: str, response: httpx.Response) -> None:
        """
        Handle errors from the get advisory request.

        :param advisory_id: ID of the requested advisory
        :param response: HTTP response object
        :raises EUVDException: If the response indicates an error
        :raises EUVDNotFoundException: If the advisory is not found
        """
        if response.status_code in (404, 204):
            raise EUVDNotFoundException(
                f"Advisory with ID {advisory_id} not found.",
            )
        if not response.is_success:
            raise EUVDException(
                f"Failed to retrieve advisory: {response.status_code} {response.reason_phrase}",
            )


__all__ = [
    "_BaseClient",
]
