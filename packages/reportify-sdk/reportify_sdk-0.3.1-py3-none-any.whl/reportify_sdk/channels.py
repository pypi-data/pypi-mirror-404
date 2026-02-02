"""
Channels Module

Provides access to channel management and following functionality.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reportify_sdk.client import Reportify


class ChannelsModule:
    """
    Channels module for searching and following channels

    Access through the main client:
        >>> client = Reportify(api_key="xxx")
        >>> channels = client.channels.search("Goldman Sachs")
    """

    def __init__(self, client: "Reportify"):
        self._client = client

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._get(path, params=params)

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._post(path, json=json)

    def search(
        self,
        query: str,
        *,
        page_num: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """
        Search for channels by query string

        Args:
            query: Search query string or URL
            page_num: Page number (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            Dictionary with channels list and pagination info

        Example:
            >>> result = client.channels.search("Goldman Sachs")
            >>> for channel in result["channels"]:
            ...     print(channel["name"])
        """
        return self._post(
            "/v1/channels/search",
            json={"query": query, "page_num": page_num, "page_size": page_size},
        )

    def followings(
        self,
        *,
        page_num: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """
        Get list of channels user is following

        Args:
            page_num: Page number (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            Dictionary with channels list and pagination info
        """
        return self._get(
            "/v1/channels/followings",
            params={"page_num": page_num, "page_size": page_size},
        )

    def follow(self, channel_id: str) -> dict[str, Any]:
        """
        Follow a specific channel

        Args:
            channel_id: Channel ID to follow

        Returns:
            Channel information with following status
        """
        return self._post(f"/v1/channels/{channel_id}/follow")

    def unfollow(self, channel_id: str) -> dict[str, Any]:
        """
        Unfollow a specific channel

        Args:
            channel_id: Channel ID to unfollow

        Returns:
            Status message
        """
        return self._client._request("DELETE", f"/v1/channels/{channel_id}/unfollow")

    def get_docs(
        self,
        *,
        channel_ids: str | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """
        Get documents from followed channels

        Args:
            channel_ids: Comma-separated channel IDs (optional, uses all followed if not provided)
            page_num: Page number (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            Dictionary with documents list and pagination info
        """
        params: dict[str, Any] = {"page_num": page_num, "page_size": page_size}
        if channel_ids:
            params["channel_ids"] = channel_ids

        return self._get("/v1/channels/followings/docs", params=params)
