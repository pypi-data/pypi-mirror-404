"""
Main client for Shiftai Agentic Infra SDK.
Provides fluent API access to all platform operations.
"""

from typing import Optional
from .http import HttpClient
from .api import (
    PlatformApi,
    MessagesApi,
    UsersApi,
    AgentsApi,
    AnalyticsApi,
    ConversationsApi,
    PlatformSessionApi,
)
from .api.internal.trulens_api import EvalApi


class InternalApi:
    """Internal API wrapper for admin/observability operations."""
    
    def __init__(self, http_client: HttpClient):
        self.eval = EvalApi(http_client)


class ShiftaiagenticinfraClient:
    """
    Main client for Shiftai Agentic Infra SDK.
    
    Thread-safe: All API instances are stateless.
    
    Usage:
        # For public operations (platform registration)
        client = CommunicationInfrastructureClient(
            base_url="http://localhost:8081"
        )
        registration = await client.platform.registerPlatform(...)

        # For authenticated operations
        client = CommunicationInfrastructureClient(
            base_url="http://localhost:8081",
            api_key="pk_your_api_key"
        )
        response = await client.messages.send_human_message(
            username="john",
            message="Hello",
            agent_name="Bot",
            agent_platform="OpenAI"
        )
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the SDK client.
        
        Args:
            base_url: Base URL of the API (e.g., "http://localhost:8081")
            api_key: Optional API key for authentication (required for most operations)
        """
        if not base_url:
            raise ValueError("baseUrl is required")
        
        self.api_key = api_key
        self._http_client = HttpClient(base_url, api_key)
        self.platform = PlatformApi(self._http_client)
        self.messages = MessagesApi(self._http_client)
        self.users = UsersApi(self._http_client)
        self.agents = AgentsApi(self._http_client)
        self.analytics = AnalyticsApi(self._http_client)
        self.conversations = ConversationsApi(self._http_client)
        self.platform_session = PlatformSessionApi(self._http_client)
        self.internal = InternalApi(self._http_client)

    def _ensure_api_key(self) -> None:
        """
        Ensure that an API key is available for authenticated operations.

        Raises:
            ValueError: If no API key is configured
        """
        if not self.api_key:
            raise ValueError(
                "This operation requires an API key. "
                "Please initialize the client with an api_key parameter, "
                "or obtain one by registering a platform first."
            )
    
    async def close(self):
        """Close the HTTP client."""
        await self._http_client.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

