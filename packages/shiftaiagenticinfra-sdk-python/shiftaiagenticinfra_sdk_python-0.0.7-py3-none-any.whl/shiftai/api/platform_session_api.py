"""
API for platform session (conversation session) operations.

Provides methods for initiating new conversation sessions and explicitly ending them.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from ..http import HttpClient
from ..models import EndConversationRequest, EndConversationResponse


class PlatformSessionApi:
    """API for platform session operations."""

    def __init__(self, http_client: HttpClient):
        self._http_client = http_client

    async def initiate_session(
        self,
        request: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initiate a new conversation session.

        POST /api/platformsession/initiate

        Notes:
            - Requires API key authentication.
            - This SDK method returns the response body "as-is" (raw map) because
              the exact response DTO may evolve server-side.

        Args:
            request: Optional raw request body to pass through (dict). If omitted, sends an empty body.

        Returns:
            Dict[str, Any]: Raw response map returned by the endpoint.
        """
        self._http_client.ensure_authenticated()
        return await self._http_client.post_map("/api/platformsession/initiate", request or {})

    async def end_conversation(self, conversation_id: UUID) -> EndConversationResponse:
        """
        End an active conversation session.

        POST /api/platformsession/endconversation

        Args:
            conversation_id: UUID of the conversation to end (required)

        Returns:
            EndConversationResponse containing success, message and timestamps.
        """
        self._http_client.ensure_authenticated()

        if conversation_id is None:
            raise ValueError("conversation_id is required")

        request = EndConversationRequest(conversationId=conversation_id)
        return await self._http_client.post(
            "/api/platformsession/endconversation",
            request,
            EndConversationResponse,
        )

