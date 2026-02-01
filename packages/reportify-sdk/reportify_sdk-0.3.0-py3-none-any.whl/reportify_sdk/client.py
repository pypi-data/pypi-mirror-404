"""
Reportify Client

Main client class for interacting with the Reportify API.
"""

from typing import Any

import httpx

from reportify_sdk.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)


class Reportify:
    """
    Reportify API Client

    A user-friendly client for accessing financial data, document search,
    and knowledge base through the Reportify API.

    Args:
        api_key: Your Reportify API key
        base_url: Base URL for the API (default: https://api.reportify.cn)
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> from reportify_sdk import Reportify
        >>> client = Reportify(api_key="your-api-key")
        >>> docs = client.search("Tesla earnings", num=10)
    """

    DEFAULT_BASE_URL = "https://api.reportify.cn"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        if not api_key:
            raise AuthenticationError("API key is required")

        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=timeout,
        )

        # Initialize sub-modules (lazy loading)
        self._stock = None
        self._timeline = None
        self._kb = None
        self._docs = None
        self._tools = None
        self._quant = None
        self._concepts = None
        self._channels = None
        self._chat = None
        self._agent = None
        self._user = None
        self._search = None

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "reportify-sdk-python/0.3.0",
        }

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the API

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            params: Query parameters
            json: JSON body data

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            NotFoundError: If resource is not found
            APIError: For other API errors
        """
        try:
            response = self._client.request(
                method=method,
                url=path,
                params=params,
                json=json,
            )

            # Handle error responses
            if response.status_code == 401:
                raise AuthenticationError()
            elif response.status_code == 429:
                raise RateLimitError()
            elif response.status_code == 404:
                raise NotFoundError()
            elif response.status_code >= 400:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", error_data.get("message", error_msg))
                except Exception:
                    pass
                raise APIError(error_msg, status_code=response.status_code)

            return response.json()

        except httpx.TimeoutException:
            raise APIError("Request timeout", status_code=408)
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request"""
        return self._request("GET", path, params=params)

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a POST request"""
        return self._request("POST", path, json=json)

    def _get_bytes(self, path: str) -> bytes:
        """Make a GET request and return raw bytes (for file downloads)"""
        try:
            response = self._client.get(path)
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif status_code == 404:
                raise NotFoundError(f"Resource not found: {path}")
            elif status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            else:
                raise APIError(f"API error: {status_code}")


    # -------------------------------------------------------------------------
    # Sub-modules (lazy loading)
    # -------------------------------------------------------------------------

    @property
    def search(self):
        """Search module for document search across all categories"""
        if self._search is None:
            from reportify_sdk.search import SearchModule
            self._search = SearchModule(self)
        return self._search

    @property
    def stock(self):
        """Stock data module for financial statements, prices, etc."""
        if self._stock is None:
            from reportify_sdk.stock import StockModule
            self._stock = StockModule(self)
        return self._stock

    @property
    def timeline(self):
        """Timeline module for following companies, topics, etc."""
        if self._timeline is None:
            from reportify_sdk.timeline import TimelineModule
            self._timeline = TimelineModule(self)
        return self._timeline

    @property
    def kb(self):
        """Knowledge base module for searching user uploaded documents"""
        if self._kb is None:
            from reportify_sdk.kb import KBModule
            self._kb = KBModule(self)
        return self._kb

    @property
    def docs(self):
        """Documents module for accessing document content and metadata"""
        if self._docs is None:
            from reportify_sdk.docs import DocsModule
            self._docs = DocsModule(self)
        return self._docs

    @property
    def quant(self):
        """Quant module for indicators, factors, quotes, and backtesting"""
        if self._quant is None:
            from reportify_sdk.quant import QuantModule
            self._quant = QuantModule(self)
        return self._quant

    @property
    def concepts(self):
        """Concepts module for accessing concept data and feeds"""
        if self._concepts is None:
            from reportify_sdk.concepts import ConceptsModule
            self._concepts = ConceptsModule(self)
        return self._concepts

    @property
    def channels(self):
        """Channels module for searching and following channels"""
        if self._channels is None:
            from reportify_sdk.channels import ChannelsModule
            self._channels = ChannelsModule(self)
        return self._channels

    @property
    def chat(self):
        """Chat module for document-based Q&A"""
        if self._chat is None:
            from reportify_sdk.chat import ChatModule
            self._chat = ChatModule(self)
        return self._chat

    @property
    def agent(self):
        """Agent module for AI-powered conversations and workflows"""
        if self._agent is None:
            from reportify_sdk.agent import AgentModule
            self._agent = AgentModule(self)
        return self._agent

    @property
    def user(self):
        """User module for user-related tools and data"""
        if self._user is None:
            from reportify_sdk.user import UserModule
            self._user = UserModule(self)
        return self._user

    def close(self):
        """Close the HTTP client"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
