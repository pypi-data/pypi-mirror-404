"""
Concepts Module

Provides access to concept-related data and feeds.
"""

from typing import Any

from reportify_sdk.client import Reportify


class ConceptsModule:
    """
    Concepts module for accessing concept data and feeds

    This module provides methods to:
    - Get latest concepts
    - Get today's concept feeds
    """

    def __init__(self, client: Reportify):
        self.client = client

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Helper method for GET requests"""
        return self.client._get(path, params)

    def latest(self, include_docs: bool = True) -> list[dict[str, Any]]:
        """
        Get latest concepts

        Args:
            include_docs: Whether to include related documents (default: True)

        Returns:
            List of latest concepts with stocks, keywords, and events

        Example:
            >>> # Get latest concepts
            >>> concepts = client.concepts.latest()
            >>> for concept in concepts:
            ...     print(concept['concept_name'])
            
            >>> # Get concepts without documents
            >>> concepts = client.concepts.latest(include_docs=False)
        """
        params = {"include_docs": include_docs}
        return self._get("/v1/concepts/latest", params)

    def today(self) -> list[dict[str, Any]]:
        """
        Get today's concept feeds

        Returns:
            List of today's concept feeds with events, stocks, and docs

        Example:
            >>> # Get today's concept feeds
            >>> feeds = client.concepts.today()
            >>> for feed in feeds:
            ...     print(f"{feed['concept_name']}: {feed['gen_count']} generations")
            ...     print(f"Time range: {feed['earliest_at']} - {feed['latest_at']}")
        """
        return self._get("/v1/concepts/today")
