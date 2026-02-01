"""
Timeline Module

Provides access to timeline feeds based on user's followed entities
(companies, topics, institutes, media).

NOTE: This module uses internal APIs that are not documented in the public OpenAPI spec.
These endpoints may change without notice.
"""

import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reportify_sdk.client import Reportify


def _timeline_deprecation_warning(method_name: str) -> None:
    """Emit deprecation warning for timeline methods."""
    warnings.warn(
        f"timeline.{method_name}() uses an internal API not documented in the public OpenAPI spec. "
        "This endpoint may change without notice.",
        DeprecationWarning,
        stacklevel=3,
    )


class TimelineModule:
    """
    Timeline module for following-based content feeds

    Access through the main client:
        >>> client = Reportify(api_key="xxx")
        >>> timeline = client.timeline.companies(num=20)
    """

    def __init__(self, client: "Reportify"):
        self._client = client

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._post(path, json=json)

    def companies(self, *, num: int = 10) -> list[dict[str, Any]]:
        """
        Get timeline for followed companies

        .. deprecated::
            This method uses an internal API not documented in the public OpenAPI spec.

        Returns recent content related to companies the user is following,
        including financial reports, news, research reports, and announcements.

        Args:
            num: Number of items to return (default: 10, max: 100)

        Returns:
            List of timeline items (documents) from followed companies

        Example:
            >>> timeline = client.timeline.companies(num=20)
            >>> for item in timeline:
            ...     print(item["title"], item["published_at"])
        """
        _timeline_deprecation_warning("companies")
        response = self._post("/v1/tools/timeline/companies", json={"num": num})
        return response.get("docs", [])

    def topics(self, *, num: int = 10) -> list[dict[str, Any]]:
        """
        Get timeline for followed topics

        .. deprecated::
            This method uses an internal API not documented in the public OpenAPI spec.

        Returns recent content related to custom topics the user is following.

        Args:
            num: Number of items to return (default: 10, max: 100)

        Returns:
            List of timeline items related to followed topics

        Example:
            >>> timeline = client.timeline.topics(num=20)
            >>> for item in timeline:
            ...     print(item["title"])
        """
        _timeline_deprecation_warning("topics")
        response = self._post("/v1/tools/timeline/topics", json={"num": num})
        return response.get("docs", [])

    def institutes(self, *, num: int = 10) -> list[dict[str, Any]]:
        """
        Get timeline for followed professional institutes

        .. deprecated::
            This method uses an internal API not documented in the public OpenAPI spec.

        Returns recent content from research institutions, banks,
        and other professional organizations the user is following.

        Args:
            num: Number of items to return (default: 10, max: 100)

        Returns:
            List of timeline items from followed institutes

        Example:
            >>> timeline = client.timeline.institutes(num=20)
            >>> for item in timeline:
            ...     print(item["channel_name"], item["title"])
        """
        _timeline_deprecation_warning("institutes")
        response = self._post("/v1/tools/timeline/institutes", json={"num": num})
        return response.get("docs", [])

    def public_media(self, *, num: int = 10) -> list[dict[str, Any]]:
        """
        Get timeline for followed public media

        .. deprecated::
            This method uses an internal API not documented in the public OpenAPI spec.

        Returns recent content from public media accounts (WeChat, etc.)
        the user is following.

        Args:
            num: Number of items to return (default: 10, max: 100)

        Returns:
            List of timeline items from followed public media

        Example:
            >>> timeline = client.timeline.public_media(num=20)
        """
        _timeline_deprecation_warning("public_media")
        response = self._post("/v1/tools/timeline/public-media", json={"num": num})
        return response.get("docs", [])

    def social_media(self, *, num: int = 10) -> list[dict[str, Any]]:
        """
        Get timeline for followed social media

        .. deprecated::
            This method uses an internal API not documented in the public OpenAPI spec.

        Returns recent content from social media accounts (Twitter, etc.)
        the user is following.

        Args:
            num: Number of items to return (default: 10, max: 100)

        Returns:
            List of timeline items from followed social media

        Example:
            >>> timeline = client.timeline.social_media(num=20)
        """
        _timeline_deprecation_warning("social_media")
        response = self._post("/v1/tools/timeline/social-media", json={"num": num})
        return response.get("docs", [])
