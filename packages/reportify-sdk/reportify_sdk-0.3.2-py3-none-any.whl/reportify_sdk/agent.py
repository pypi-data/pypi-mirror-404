"""
Agent Module

Provides access to AI agent conversations and workflow execution.
"""

from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from reportify_sdk.client import Reportify


class AgentModule:
    """
    Agent module for AI-powered conversations and workflows

    Access through the main client:
        >>> client = Reportify(api_key="xxx")
        >>> conv = client.agent.create_conversation(agent_id=11887655289749510)
    """

    def __init__(self, client: "Reportify"):
        self._client = client

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._get(path, params=params)

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._post(path, json=json)

    def create_conversation(
        self,
        agent_id: int,
        *,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new agent conversation

        Args:
            agent_id: Agent ID
            title: Conversation title (optional)

        Returns:
            Conversation details including id, user_id, agent_id, type, status, etc.

        Example:
            >>> conv = client.agent.create_conversation(
            ...     agent_id=11887655289749510,
            ...     title="NVIDIA analysis"
            ... )
            >>> print(conv["id"])
        """
        data: dict[str, Any] = {"agent_id": agent_id}
        if title:
            data["title"] = title

        return self._post("/v1/agent/conversations", json=data)

    def get_conversation(self, conversation_id: int) -> dict[str, Any]:
        """
        Get agent conversation details

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation details including messages, status, etc.
        """
        return self._get(f"/v1/agent/conversations/{conversation_id}")

    def chat(
        self,
        conversation_id: int,
        message: str,
        *,
        documents: list[dict[str, Any]] | None = None,
        stream: bool = True,
    ) -> dict[str, Any] | Iterator[dict[str, Any]]:
        """
        Chat with agent (streaming or non-streaming)

        Args:
            conversation_id: Conversation ID
            message: User message content
            documents: List of related documents (optional)
                Each document should have: doc_id, doc_title, file_type (optional)
            stream: Whether to use streaming response (default: True)

        Returns:
            For streaming: Iterator of WorkflowStreamEvent objects
            For non-streaming: Response with message content

        Example:
            >>> # Non-streaming
            >>> response = client.agent.chat(
            ...     conversation_id=123456,
            ...     message="Analyze NVIDIA's latest earnings",
            ...     stream=False
            ... )
            
            >>> # Streaming
            >>> for event in client.agent.chat(conv_id, "Hello", stream=True):
            ...     print(event)
        """
        data: dict[str, Any] = {
            "message": message,
            "stream": stream,
        }
        if documents:
            data["documents"] = documents

        return self._post(
            f"/v1/agent/conversations/{conversation_id}/chat",
            json=data,
        )

    def list_messages(
        self,
        conversation_id: int,
        *,
        limit: int = 10,
        before_message_id: int | None = None,
    ) -> dict[str, Any]:
        """
        List agent conversation messages

        Args:
            conversation_id: Conversation ID
            limit: Number of messages to return (default: 10, max: 100)
            before_message_id: Fetch messages created before this message ID

        Returns:
            Dictionary with messages list
        """
        params: dict[str, Any] = {"limit": limit}
        if before_message_id is not None:
            params["before_message_id"] = before_message_id

        return self._get(
            f"/v1/agent/conversations/{conversation_id}/messages",
            params=params,
        )

    def get_message_events(
        self,
        conversation_id: int,
        assistant_message_id: str,
        *,
        stream: bool = True,
        timeout: int = 1800,
        from_offset: int = 0,
    ) -> dict[str, Any] | Iterator[dict[str, Any]]:
        """
        Get assistant message events from a specific offset

        Args:
            conversation_id: Conversation ID
            assistant_message_id: Assistant message ID (from chat response header)
            stream: Whether to stream events via SSE (default: True)
            timeout: Timeout in seconds for streaming mode (default: 1800)
            from_offset: Start streaming from specific offset (default: 0)

        Returns:
            For streaming: Iterator of WorkflowStreamEvent objects
            For non-streaming: Dictionary with assistant_events list
        """
        params: dict[str, Any] = {
            "stream": stream,
            "timeout": timeout,
            "from_offset": from_offset,
        }

        return self._get(
            f"/v1/agent/conversations/{conversation_id}/messages/{assistant_message_id}",
            params=params,
        )

    def cancel_execution(
        self,
        conversation_id: int,
        assistant_message_id: str,
    ) -> dict[str, Any]:
        """
        Cancel agent execution

        Args:
            conversation_id: Conversation ID
            assistant_message_id: Assistant message ID to cancel

        Returns:
            Dictionary with response_id and status
        """
        return self._post(
            f"/v1/agent/conversations/{conversation_id}/messages/{assistant_message_id}/cancel"
        )

    def get_file(self, file_id: str) -> bytes:
        """
        Get agent generated file

        Args:
            file_id: Agent generated file ID

        Returns:
            File content as bytes

        Example:
            >>> file_content = client.agent.get_file("file_abc123")
            >>> with open("output.xlsx", "wb") as f:
            ...     f.write(file_content)
        """
        return self._client._get_bytes(f"/v1/agent/files/{file_id}")
