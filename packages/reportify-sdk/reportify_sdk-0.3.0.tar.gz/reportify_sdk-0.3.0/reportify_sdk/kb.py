"""
Knowledge Base Module

Provides access to user's personal knowledge base for searching
uploaded documents and folders.

NOTE: This module uses internal APIs that are not documented in the public OpenAPI spec.
These endpoints may change without notice. For production use, consider using
the documented docs.search_chunks() method instead.
"""

import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reportify_sdk.client import Reportify


class KBModule:
    """
    Knowledge base module for searching user uploaded documents

    Access through the main client:
        >>> client = Reportify(api_key="xxx")
        >>> results = client.kb.search("revenue breakdown")
    """

    def __init__(self, client: "Reportify"):
        self._client = client

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._post(path, json=json)

    def search(
        self,
        query: str,
        *,
        folder_ids: list[str] | None = None,
        doc_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        num: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search user's knowledge base

        .. deprecated::
            This method uses an internal API not documented in the public OpenAPI spec.
            Consider using client.docs.search_chunks() instead.

        Performs semantic search across documents the user has uploaded
        to their personal knowledge base.

        Args:
            query: Search query string
            folder_ids: Filter by specific folder IDs
            doc_ids: Filter by specific document IDs
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            num: Number of results to return (default: 10)

        Returns:
            List of matching chunks with document information

        Example:
            >>> results = client.kb.search("quarterly revenue", num=5)
            >>> for chunk in results:
            ...     print(chunk["content"][:100])
            ...     print(f"From: {chunk['doc']['title']}")
        """
        warnings.warn(
            "kb.search() uses an internal API not documented in the public OpenAPI spec. "
            "Consider using docs.search_chunks() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        data: dict[str, Any] = {
            "query": query,
            "num": num,
        }
        if folder_ids:
            data["folder_ids"] = folder_ids
        if doc_ids:
            data["doc_ids"] = doc_ids
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        response = self._post("/v1/tools/kb/search", json=data)
        return response.get("chunks", [])
