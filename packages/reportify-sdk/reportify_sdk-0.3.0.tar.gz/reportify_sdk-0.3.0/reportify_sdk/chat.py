"""
Chat Module

Provides chat completion functionality based on document content.
"""

from typing import TYPE_CHECKING, Any, Iterator, Literal

if TYPE_CHECKING:
    from reportify_sdk.client import Reportify


class ChatModule:
    """
    Chat module for document-based Q&A

    Access through the main client:
        >>> client = Reportify(api_key="xxx")
        >>> response = client.chat.completion("What are Tesla's revenue?")
    """

    def __init__(self, client: "Reportify"):
        self._client = client

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._post(path, json=json)

    def completion(
        self,
        query: str,
        *,
        folder_ids: list[str] | None = None,
        doc_ids: list[str] | None = None,
        categories: list[str] | None = None,
        markets: list[str] | None = None,
        institutions: list[str] | None = None,
        symbols: list[str] | None = None,
        tags: dict[str, list] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        min_score: float | None = None,
        extended_filters: list[dict] | None = None,
        mode: Literal["concise", "comprehensive", "deepresearch"] = "concise",
        session_id: str = "",
        stream: bool = False,
    ) -> dict[str, Any] | Iterator[dict[str, Any]]:
        """
        Chat completion based on document content

        Args:
            query: User question
            folder_ids: Filter by folder IDs
            doc_ids: Filter by document IDs
            categories: Filter by document categories
            markets: Filter by markets (cn, hk, us)
            institutions: Filter by institutions
            symbols: Stock symbols in market:ticker format (e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            tags: Filter by tags
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            min_score: Minimum relevance score
            extended_filters: Extended filter conditions
            mode: Response mode ("concise", "comprehensive", "deepresearch")
            session_id: Session ID for conversation continuity
            stream: Whether to stream the response

        Returns:
            Chat completion response with type, message_id, message, and extra

        Example:
            >>> response = client.chat.completion(
            ...     "What are Tesla's revenue projections?",
            ...     symbols=["US:TSLA"],
            ...     mode="comprehensive"
            ... )
            >>> print(response["message"])
        """
        data: dict[str, Any] = {
            "query": query,
            "mode": mode,
            "session_id": session_id,
            "stream": stream,
        }
        if folder_ids:
            data["folder_ids"] = folder_ids
        if doc_ids:
            data["doc_ids"] = doc_ids
        if categories:
            data["categories"] = categories
        if markets:
            data["markets"] = markets
        if institutions:
            data["institutions"] = institutions
        if symbols:
            data["symbols"] = symbols
        if tags:
            data["tags"] = tags
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if min_score is not None:
            data["min_score"] = min_score
        if extended_filters:
            data["extended_filters"] = extended_filters

        return self._post("/v1/chat/completion", json=data)
