"""
Search Module

Provides document search functionality across various categories.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reportify_sdk.client import Reportify


class SearchModule:
    """
    Search module for document search functionality.

    Access via client.search:
        >>> results = client.search.all("Tesla earnings")
        >>> news = client.search.news("Apple iPhone")
    """

    def __init__(self, client: "Reportify"):
        self._client = client

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._post(path, json=json)

    def all(
        self,
        query: str,
        *,
        num: int = 10,
        categories: list[str] | None = None,
        symbols: list[str] | None = None,
        industries: list[str] | None = None,
        channel_ids: list[str] | None = None,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search documents across all categories

        Args:
            query: Search query string
            num: Number of results to return (default: 10, max: 100)
            categories: Filter by categories (news, reports, filings, transcripts, socials)
            symbols: Stock symbols in market:ticker format (e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            industries: Filter by industries
            channel_ids: Filter by channel IDs
            start_datetime: Start datetime filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            end_datetime: End datetime filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)

        Returns:
            List of matching documents
        """
        data: dict[str, Any] = {"query": query, "num": num}
        if categories:
            data["categories"] = categories
        if symbols:
            data["symbols"] = symbols
        if industries:
            data["industries"] = industries
        if channel_ids:
            data["channel_ids"] = channel_ids
        if start_datetime:
            data["start_datetime"] = start_datetime
        if end_datetime:
            data["end_datetime"] = end_datetime

        response = self._post("/v2/search", json=data)
        return response.get("docs", [])

    def news(
        self,
        query: str,
        *,
        num: int = 10,
        symbols: list[str] | None = None,
        channel_ids: list[str] | None = None,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search news articles

        Args:
            query: Search query string
            num: Number of results to return
            symbols: Stock symbols in market:ticker format (e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            channel_ids: Filter by channel IDs
            start_datetime: Start datetime filter
            end_datetime: End datetime filter

        Returns:
            List of news documents
        """
        data: dict[str, Any] = {"query": query, "num": num}
        if symbols:
            data["symbols"] = symbols
        if channel_ids:
            data["channel_ids"] = channel_ids
        if start_datetime:
            data["start_datetime"] = start_datetime
        if end_datetime:
            data["end_datetime"] = end_datetime

        response = self._post("/v2/search/news", json=data)
        return response.get("docs", [])

    def reports(
        self,
        query: str,
        *,
        num: int = 10,
        symbols: list[str] | None = None,
        industries: list[str] | None = None,
        channel_ids: list[str] | None = None,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search research reports

        Args:
            query: Search query string
            num: Number of results to return
            symbols: Stock symbols in market:ticker format (e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            industries: Filter by industries
            channel_ids: Filter by channel IDs
            start_datetime: Start datetime filter
            end_datetime: End datetime filter

        Returns:
            List of research reports
        """
        data: dict[str, Any] = {"query": query, "num": num}
        if symbols:
            data["symbols"] = symbols
        if industries:
            data["industries"] = industries
        if channel_ids:
            data["channel_ids"] = channel_ids
        if start_datetime:
            data["start_datetime"] = start_datetime
        if end_datetime:
            data["end_datetime"] = end_datetime

        response = self._post("/v2/search/reports", json=data)
        return response.get("docs", [])

    def filings(
        self,
        query: str,
        symbols: list[str],
        *,
        num: int = 10,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search company filings

        Args:
            query: Search query string
            symbols: Stock symbols in market:ticker format (required, e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            num: Number of results to return
            start_datetime: Start datetime filter
            end_datetime: End datetime filter

        Returns:
            List of filing documents
        """
        data: dict[str, Any] = {"query": query, "symbols": symbols, "num": num}
        if start_datetime:
            data["start_datetime"] = start_datetime
        if end_datetime:
            data["end_datetime"] = end_datetime

        response = self._post("/v2/search/filings", json=data)
        return response.get("docs", [])

    def conference_calls(
        self,
        query: str,
        symbols: list[str],
        *,
        num: int = 10,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
        fiscal_year: str | None = None,
        fiscal_quarter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search earnings call transcripts and slides

        Args:
            query: Search query string
            symbols: Stock symbols in market:ticker format (required, e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            num: Number of results to return
            start_datetime: Start datetime filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            end_datetime: End datetime filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            fiscal_year: Fiscal year filter (e.g., '2025', '2026')
            fiscal_quarter: Fiscal quarter filter (e.g., 'Q1', 'Q2', 'Q3', 'Q4')

        Returns:
            List of conference call documents
        """
        data: dict[str, Any] = {"query": query, "symbols": symbols, "num": num}
        if start_datetime:
            data["start_datetime"] = start_datetime
        if end_datetime:
            data["end_datetime"] = end_datetime
        if fiscal_year:
            data["fiscal_year"] = fiscal_year
        if fiscal_quarter:
            data["fiscal_quarter"] = fiscal_quarter

        response = self._post("/v2/search/conference-calls", json=data)
        return response.get("docs", [])

    def earnings_pack(
        self,
        query: str,
        symbols: list[str],
        *,
        num: int = 10,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
        fiscal_year: str | None = None,
        fiscal_quarter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search earnings financial reports

        Args:
            query: Search query string
            symbols: Stock symbols in market:ticker format (required, e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            num: Number of results to return
            start_datetime: Start datetime filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            end_datetime: End datetime filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            fiscal_year: Fiscal year filter (e.g., '2025', '2026')
            fiscal_quarter: Fiscal quarter filter (e.g., 'Q1', 'Q2', 'Q3', 'Q4')

        Returns:
            List of earnings pack documents
        """
        data: dict[str, Any] = {"query": query, "symbols": symbols, "num": num}
        if start_datetime:
            data["start_datetime"] = start_datetime
        if end_datetime:
            data["end_datetime"] = end_datetime
        if fiscal_year:
            data["fiscal_year"] = fiscal_year
        if fiscal_quarter:
            data["fiscal_quarter"] = fiscal_quarter

        response = self._post("/v2/search/earnings-pack", json=data)
        return response.get("docs", [])

    def minutes(
        self,
        query: str,
        *,
        num: int = 10,
        symbols: list[str] | None = None,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search conference calls and IR (Investor Relations) meetings

        Args:
            query: Search query string
            num: Number of results to return
            symbols: Stock symbols in market:ticker format (e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            start_datetime: Start datetime filter
            end_datetime: End datetime filter

        Returns:
            List of minutes documents
        """
        data: dict[str, Any] = {"query": query, "num": num}
        if symbols:
            data["symbols"] = symbols
        if start_datetime:
            data["start_datetime"] = start_datetime
        if end_datetime:
            data["end_datetime"] = end_datetime

        response = self._post("/v2/search/minutes", json=data)
        return response.get("docs", [])

    def socials(
        self,
        query: str,
        *,
        num: int = 10,
        symbols: list[str] | None = None,
        channel_ids: list[str] | None = None,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search social media content

        Args:
            query: Search query string
            num: Number of results to return
            symbols: Stock symbols in market:ticker format (e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            channel_ids: Filter by channel IDs
            start_datetime: Start datetime filter
            end_datetime: End datetime filter

        Returns:
            List of social media documents
        """
        data: dict[str, Any] = {"query": query, "num": num}
        if symbols:
            data["symbols"] = symbols
        if channel_ids:
            data["channel_ids"] = channel_ids
        if start_datetime:
            data["start_datetime"] = start_datetime
        if end_datetime:
            data["end_datetime"] = end_datetime

        response = self._post("/v2/search/socials", json=data)
        return response.get("docs", [])

    def webpages(
        self,
        query: str,
        *,
        num: int = 10,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search webpage content

        Args:
            query: Search query string
            num: Number of results to return
            start_datetime: Start datetime filter
            end_datetime: End datetime filter

        Returns:
            List of webpage content
        """
        data: dict[str, Any] = {"query": query, "num": num}
        if start_datetime:
            data["start_datetime"] = start_datetime
        if end_datetime:
            data["end_datetime"] = end_datetime

        response = self._post("/v2/search/webpages", json=data)
        return response.get("docs", [])
