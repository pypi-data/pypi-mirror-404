"""
Reportify SDK - Python client for Reportify API

A user-friendly SDK for accessing financial data, document search,
and knowledge base through the Reportify API.

Usage:
    from reportify_sdk import Reportify

    client = Reportify(api_key="your-api-key")
    docs = client.search("Tesla earnings", num=10)
"""

from reportify_sdk.client import Reportify
from reportify_sdk.exceptions import (
    ReportifyError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    APIError,
)

__version__ = "0.3.0"
__all__ = [
    "Reportify",
    "ReportifyError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "APIError",
]
