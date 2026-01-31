"""
Asynchronous client for the EUVD API.
"""

import datetime
from types import TracebackType
from typing import Any

import httpx

from euvd.clients._baseclient import _BaseClient
from euvd.models import Advisory, EnisaVulnerability, Pagination


class EUVDAsyncClient(_BaseClient):
    """
    Asynchronous client for the EUVD API.
    """

    def __init__(self) -> None:
        """
        Initialize the EUVDAsyncClient.
        """
        self.__client: httpx.AsyncClient = httpx.AsyncClient(base_url="https://euvdservices.enisa.europa.eu/api")

    async def __aenter__(self) -> "EUVDAsyncClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.__client.aclose()

    async def get_latest_vulnerabilities(self) -> list[EnisaVulnerability]:
        """
        Retrieves the latest vulnerabilities.

        Returns:
            list[EnisaVulnerability]: A list of EnisaVulnerability objects representing the latest vulnerabilities.
        """
        request_args: dict[str, Any] = self._prepare_get_latest_vulnerabilities_request()
        request: httpx.Request = self.__client.build_request(**request_args)
        response: httpx.Response = await self.__client.send(
            request,
            follow_redirects=True,
        )
        self._handle_get_latest_vulnerabilities_request_errors(response)
        vulnerabilities: list[dict[str, Any]] = response.json()
        parsed_vulnerabilities: list[EnisaVulnerability] = self._parse_vulnerabilities(vulnerabilities)
        return parsed_vulnerabilities

    async def get_latest_exploited_vulnerabilities(self) -> list[EnisaVulnerability]:
        """
        Retrieves the latest exploited vulnerabilities.

        Returns:
            list[EnisaVulnerability]: A list of EnisaVulnerability objects representing the latest exploited vulnerabilities.
        """
        request_args: dict[str, Any] = self._prepare_get_latest_exploited_vulnerabilities_request()
        request: httpx.Request = self.__client.build_request(**request_args)
        response: httpx.Response = await self.__client.send(
            request,
            follow_redirects=True,
        )
        self._handle_get_latest_exploited_vulnerabilities_request_errors(response)
        vulnerabilities: list[dict[str, Any]] = response.json()
        parsed_vulnerabilities: list[EnisaVulnerability] = self._parse_vulnerabilities(vulnerabilities)
        return parsed_vulnerabilities

    async def get_latest_critical_vulnerabilities(self) -> list[EnisaVulnerability]:
        """
        Retrieves the latest critical vulnerabilities.

        Returns:
            list[EnisaVulnerability]: A list of EnisaVulnerability objects representing the latest critical vulnerabilities.
        """
        request_args: dict[str, Any] = self._prepare_get_latest_critical_vulnerabilities_request()
        request: httpx.Request = self.__client.build_request(**request_args)
        response: httpx.Response = await self.__client.send(
            request,
            follow_redirects=True,
        )
        self._handle_get_latest_critical_vulnerabilities_response_errors(response)
        vulnerabilities: list[dict[str, Any]] = response.json()
        parsed_vulnerabilities: list[EnisaVulnerability] = self._parse_vulnerabilities(vulnerabilities)
        return parsed_vulnerabilities

    async def search_vulnerabilities(
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
    ) -> tuple[list[EnisaVulnerability], Pagination]:
        """
        Searches for vulnerabilities using various filters.

        Args:
            from_score (float, optional): Minimum CVSS score.
            to_score (float, optional): Maximum CVSS score.
            from_epss (float, optional): Minimum EPSS score.
            to_epss (float, optional): Maximum EPSS score.
            from_date (datetime.date, optional): Start date for the search.
            to_date (datetime.date, optional): End date for the search.
            product (str, optional): Product name to filter vulnerabilities.
            vendor (str, optional): Vendor name to filter vulnerabilities.
            assigner (str, optional): Assigner name to filter vulnerabilities.
            exploited (bool, optional): Whether the vulnerability is exploited.
            text (str, optional): Text to search within vulnerabilities.
            page (int): Page number for pagination.
            page_size (int): Number of items per page.

        Returns:
            tuple[list[EnisaVulnerability], Pagination]: A tuple containing a list of
                EnisaVulnerability objects and a Pagination object.
        """
        request_args = self._prepare_search_vulnerabilities_request(
            from_score,
            to_score,
            from_epss,
            to_epss,
            from_date,
            to_date,
            product,
            vendor,
            assigner,
            exploited,
            text,
            page,
            page_size,
        )
        request: httpx.Request = self.__client.build_request(**request_args)
        response: httpx.Response = await self.__client.send(
            request,
            follow_redirects=True,
        )
        self._handle_search_vulnerabilities_response_errors(response)
        results: dict[str, Any] = response.json()
        vulnerabilities: list[dict[str, Any]] = results.get("items", [])
        parsed_vulnerabilities: list[EnisaVulnerability] = self._parse_vulnerabilities(vulnerabilities)
        pagination: Pagination = Pagination(
            page=page,
            page_size=page_size,
            total_items=results.get("total", 0),
        )
        return (parsed_vulnerabilities, pagination)

    async def get_vulnerability(
        self,
        vulnerability_id: str,
    ) -> EnisaVulnerability:
        """
        Retrieves a vulnerability by its ID.

        Args:
            vulnerability_id (str): The ID of the vulnerability to retrieve.

        Returns:
            EnisaVulnerability: An EnisaVulnerability object representing the vulnerability.
        """
        request_args: dict[str, Any] = self._prepare_get_vulnerability_request(vulnerability_id)
        request: httpx.Request = self.__client.build_request(**request_args)
        response: httpx.Response = await self.__client.send(
            request,
            follow_redirects=True,
        )
        self._handle_get_vulnerability_response_errors(vulnerability_id, response)
        vulnerability_data: dict[str, Any] = response.json()
        return EnisaVulnerability.from_dict(vulnerability_data)

    async def get_advisory(
        self,
        advisory_id: str,
    ) -> Advisory:
        """
        Retrieves an advisory by its ID.

        Args:
            advisory_id (str): The ID of the advisory to retrieve.

        Returns:
            Advisory: An Advisory object representing the advisory.
        """
        request_args: dict[str, Any] = self._prepare_get_advisory_request(advisory_id)
        request: httpx.Request = self.__client.build_request(**request_args)
        response: httpx.Response = await self.__client.send(
            request,
            follow_redirects=True,
        )
        self._handle_get_advisory_response_errors(advisory_id, response)
        advisory_data: dict[str, Any] = response.json()
        return Advisory.from_dict(advisory_data)


__all__ = [
    "EUVDAsyncClient",
]
