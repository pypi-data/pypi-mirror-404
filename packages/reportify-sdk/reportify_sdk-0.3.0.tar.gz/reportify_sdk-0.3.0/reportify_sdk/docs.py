"""
Documents Module

Provides access to document content, metadata, and summaries.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reportify_sdk.client import Reportify


class DocsModule:
    """
    Documents module for accessing document content and metadata

    Access through the main client:
        >>> client = Reportify(api_key="xxx")
        >>> doc = client.docs.get("doc_id")
    """

    def __init__(self, client: "Reportify"):
        self._client = client

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._get(path, params=params)

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._post(path, json=json)

    def get(self, doc_id: str) -> dict[str, Any]:
        """
        Get document content and metadata

        Retrieves the full content of a document including chunks.

        Args:
            doc_id: Document ID

        Returns:
            Document dictionary with content and metadata

        Example:
            >>> doc = client.docs.get("abc123")
            >>> print(doc["title"])
            >>> print(doc["content"][:500])
        """
        return self._get(f"/v1/docs/{doc_id}")

    def summary(self, doc_id: str) -> dict[str, Any]:
        """
        Get document summary

        Retrieves the AI-generated summary of a document.

        Args:
            doc_id: Document ID

        Returns:
            Summary dictionary with title, summary text, and key points

        Example:
            >>> summary = client.docs.summary("abc123")
            >>> print(summary["summary"])
            >>> for point in summary.get("key_points", []):
            ...     print(f"- {point}")
        """
        return self._get(f"/v1/docs/{doc_id}/summary")

    def raw_content(self, doc_id: str) -> dict[str, Any]:
        """
        Get raw document content

        Retrieves the original content of a document without processing.

        Args:
            doc_id: Document ID

        Returns:
            Raw content dictionary
        """
        return self._get(f"/v1/docs/{doc_id}/raw-content")

    def list(
        self,
        *,
        symbols: list[str] | None = None,
        categories: list[str] | None = None,
        markets: list[str] | None = None,
        institutions: list[str] | None = None,
        tags: dict[str, list] | None = None,
        folder_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        min_score: float | None = None,
        extended_filters: list[dict] | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """
        List documents with filters

        Args:
            symbols: Stock symbols in market:ticker format (e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            categories: Filter by document categories (financials, transcripts, reports, news, files, filings, socials)
            markets: Filter by markets (cn, hk, us)
            institutions: Filter by institutions
            tags: Filter by tags (dict with key-value pairs)
            folder_ids: Filter by folder IDs
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            min_score: Minimum relevance score
            extended_filters: Extended filter conditions
            page_num: Page number (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            Dictionary with documents list and pagination info

        Example:
            >>> result = client.docs.list(symbols=["US:AAPL"], page_size=10)
            >>> for doc in result["docs"]:
            ...     print(doc["title"])
        """
        data: dict[str, Any] = {
            "page_num": page_num,
            "page_size": page_size,
        }
        if symbols:
            data["symbols"] = symbols
        if categories:
            data["categories"] = categories
        if markets:
            data["markets"] = markets
        if institutions:
            data["institutions"] = institutions
        if tags:
            data["tags"] = tags
        if folder_ids:
            data["folder_ids"] = folder_ids
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if min_score is not None:
            data["min_score"] = min_score
        if extended_filters:
            data["extended_filters"] = extended_filters

        return self._post("/v1/docs", json=data)

    def search_chunks(
        self,
        query: str,
        *,
        symbols: list[str] | None = None,
        categories: list[str] | None = None,
        markets: list[str] | None = None,
        institutions: list[str] | None = None,
        tags: dict[str, list] | None = None,
        folder_ids: list[str] | None = None,
        doc_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        min_score: float | None = None,
        extended_filters: list[dict] | None = None,
        num: int = 10,
        include_doc_extra_details: bool = False,
        refine_question: bool = False,
        date_range: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search document chunks semantically

        Performs semantic search across document chunks.

        Args:
            query: Search query string
            symbols: Stock symbols in market:ticker format (e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            categories: Filter by document categories (financials, transcripts, reports, news, filings, socials)
            markets: Filter by markets (cn, hk, us)
            institutions: Filter by institutions
            tags: Filter by tags (dict with key-value pairs)
            folder_ids: Filter by folder IDs
            doc_ids: Filter by document IDs
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            min_score: Minimum relevance score
            extended_filters: Extended filter conditions
            num: Number of results to return (default: 10)
            include_doc_extra_details: Include extra document details
            refine_question: Refine the search question
            date_range: Date range filter (h, d, w, m, y)

        Returns:
            List of matching chunks with document info

        Example:
            >>> chunks = client.docs.search_chunks("revenue guidance", num=5)
            >>> for chunk in chunks:
            ...     print(chunk["content"])
        """
        data: dict[str, Any] = {
            "query": query,
            "num": num,
        }
        if symbols:
            data["symbols"] = symbols
        if categories:
            data["categories"] = categories
        if markets:
            data["markets"] = markets
        if institutions:
            data["institutions"] = institutions
        if tags:
            data["tags"] = tags
        if folder_ids:
            data["folder_ids"] = folder_ids
        if doc_ids:
            data["doc_ids"] = doc_ids
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if min_score is not None:
            data["min_score"] = min_score
        if extended_filters:
            data["extended_filters"] = extended_filters
        if include_doc_extra_details:
            data["include_doc_extra_details"] = include_doc_extra_details
        if refine_question:
            data["refine_question"] = refine_question
        if date_range:
            data["date_range"] = date_range

        response = self._post("/v1/search/chunks", json=data)
        return response.get("chunks", [])

    def query_by_symbols(
        self,
        symbols: list[str],
        *,
        categories: list[str] | None = None,
        markets: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """
        Query documents by stock symbols

        Args:
            symbols: Stock symbols in market:ticker format (required, e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            categories: Filter by document categories
            markets: Filter by markets (cn, hk, us)
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            page_num: Page number (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            Dictionary with documents list and pagination info
        """
        data: dict[str, Any] = {
            "symbols": symbols,
            "page_num": page_num,
            "page_size": page_size,
        }
        if categories:
            data["categories"] = categories
        if markets:
            data["markets"] = markets
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        return self._post("/v1/docs/symbols", json=data)

    def query_by_tags(
        self,
        tags: dict[str, list],
        *,
        categories: list[str] | None = None,
        markets: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page_num: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """
        Query documents by tags

        Args:
            tags: Tags to filter by (required, dict with key-value pairs)
            categories: Filter by document categories
            markets: Filter by markets (cn, hk, us)
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            page_num: Page number (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            Dictionary with documents list and pagination info
        """
        data: dict[str, Any] = {
            "tags": tags,
            "page_num": page_num,
            "page_size": page_size,
        }
        if categories:
            data["categories"] = categories
        if markets:
            data["markets"] = markets
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        return self._post("/v1/docs/tags", json=data)

    def search(
        self,
        *,
        query: str | None = None,
        symbols: list[str] | None = None,
        categories: list[str] | None = None,
        markets: list[str] | None = None,
        institutions: list[str] | None = None,
        tags: dict[str, list] | None = None,
        folder_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        min_score: float | None = None,
        extended_filters: list[dict] | None = None,
        page_num: int = 1,
        page_size: int = 10,
        mode: str = "smart",
        sort: str = "smart",
        should_highlight: bool = False,
    ) -> dict[str, Any]:
        """
        Search documents (v1 API)

        Args:
            query: Search query string
            symbols: Stock symbols in market:ticker format (e.g., US:AAPL, HK:00700, SH:600519, SZ:000001)
            categories: Filter by document categories
            markets: Filter by markets (cn, hk, us)
            institutions: Filter by institutions
            tags: Filter by tags
            folder_ids: Filter by folder IDs
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            min_score: Minimum relevance score
            extended_filters: Extended filter conditions
            page_num: Page number (default: 1)
            page_size: Number of items per page (default: 10)
            mode: Search mode ("smart", "semantic", "keywords")
            sort: Sort order ("smart", "latest")
            should_highlight: Whether to highlight matches

        Returns:
            Dictionary with documents list and pagination info
        """
        data: dict[str, Any] = {
            "page_num": page_num,
            "page_size": page_size,
            "mode": mode,
            "sort": sort,
            "should_highlight": should_highlight,
        }
        if query:
            data["query"] = query
        if symbols:
            data["symbols"] = symbols
        if categories:
            data["categories"] = categories
        if markets:
            data["markets"] = markets
        if institutions:
            data["institutions"] = institutions
        if tags:
            data["tags"] = tags
        if folder_ids:
            data["folder_ids"] = folder_ids
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if min_score is not None:
            data["min_score"] = min_score
        if extended_filters:
            data["extended_filters"] = extended_filters

        return self._post("/v1/search", json=data)

    # -------------------------------------------------------------------------
    # Folder Management
    # -------------------------------------------------------------------------

    def create_folder(self, name: str) -> dict[str, Any]:
        """
        Create a new folder

        Args:
            name: Folder name

        Returns:
            Dictionary with folder_id
        """
        return self._post("/v1/docs/folder/create", json={"name": name})

    def delete_folder(self, folder_id: str) -> dict[str, Any]:
        """
        Delete a folder and all files in it

        Args:
            folder_id: Folder ID to delete

        Returns:
            Dictionary with deleted doc_ids and folder_id
        """
        return self._client._request(
            "DELETE", "/v1/docs/folder/delete", json={"folder_id": folder_id}
        )

    # -------------------------------------------------------------------------
    # Document Upload
    # -------------------------------------------------------------------------

    def upload(
        self,
        docs: list[dict[str, Any]],
        *,
        folder_id: str | None = None,
        pdf_parsing_mode: int = 1,
    ) -> dict[str, Any]:
        """
        Upload documents by URL

        Args:
            docs: List of document objects with url, name, metadatas, published_at, tags
            folder_id: Folder ID to upload to (optional, uses default folder if not provided)
            pdf_parsing_mode: PDF parsing mode (1: by page, 3: by logic)

        Returns:
            Dictionary with uploaded document IDs

        Example:
            >>> result = client.docs.upload([
            ...     {"url": "https://example.com/doc.pdf", "name": "My Doc"}
            ... ])
        """
        data: dict[str, Any] = {
            "docs": docs,
            "pdf_parsing_mode": pdf_parsing_mode,
        }
        if folder_id:
            data["folder_id"] = folder_id

        return self._post("/v1/docs/upload", json=data)

    def upload_async(
        self,
        docs: list[dict[str, Any]],
        *,
        folder_id: str | None = None,
        pdf_parsing_mode: int = 1,
    ) -> dict[str, Any]:
        """
        Upload documents asynchronously by URL

        Args:
            docs: List of document objects with url, name, metadatas, published_at, tags
            folder_id: Folder ID to upload to (optional)
            pdf_parsing_mode: PDF parsing mode (1: by page, 3: by logic)

        Returns:
            Dictionary with uploaded document IDs
        """
        data: dict[str, Any] = {
            "docs": docs,
            "pdf_parsing_mode": pdf_parsing_mode,
        }
        if folder_id:
            data["folder_id"] = folder_id

        return self._post("/v1/docs/upload/async", json=data)

    def get_upload_status(self, doc_id: str) -> dict[str, Any]:
        """
        Get document upload status

        Args:
            doc_id: Document ID

        Returns:
            Dictionary with id and status (pending, processing, completed)
        """
        return self._get(f"/v1/docs/{doc_id}/upload/status")

    def delete(self, doc_ids: list[str]) -> dict[str, Any]:
        """
        Delete documents

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            Dictionary with deleted doc_ids
        """
        return self._client._request(
            "DELETE", "/v1/docs/delete", json={"doc_ids": doc_ids}
        )
