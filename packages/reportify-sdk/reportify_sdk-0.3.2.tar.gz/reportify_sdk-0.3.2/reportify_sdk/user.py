"""
User Module

Provides access to user-related tools and data.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reportify_sdk.client import Reportify


class UserModule:
    """
    User module for accessing user-related tools

    Access through the main client:
        >>> client = Reportify(api_key="xxx")
        >>> companies = client.user.followed_companies()
    """

    def __init__(self, client: "Reportify"):
        self._client = client

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._get(path, params=params)

    def followed_companies(self) -> list[dict[str, Any]]:
        """
        Get all companies followed by the user

        Returns a list of companies that the user is following,
        including company details like symbol, name, logo, and follow timestamp.

        Returns:
            List of followed company information

        Example:
            >>> companies = client.user.followed_companies()
            >>> for company in companies:
            ...     print(f"{company['symbol']}: {company['name']}")
        """
        response = self._get("/v1/tools/user/followed-companies")
        return response.get("companies", [])
