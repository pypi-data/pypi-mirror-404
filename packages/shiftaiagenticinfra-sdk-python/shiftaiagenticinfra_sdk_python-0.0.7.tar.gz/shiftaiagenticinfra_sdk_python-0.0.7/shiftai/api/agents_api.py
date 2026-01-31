"""
API for agent operations.
Provides methods for creating and managing AI agents.
"""

from typing import Optional, Dict, Any
from ..http import HttpClient
from ..models import CreateAgentRequest, Agent


class AgentsApi:
    """API for agent operations."""
    
    def __init__(self, http_client: HttpClient):
        self._http_client = http_client
    
    async def create(
        self,
        name: str,
        platform: str,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """
        Create a new agent.
        
        POST /api/agents
        
        Args:
            name: Display name for the AI agent (required)
            platform: Platform or provider of the AI agent (required)
            version: Optional version number or model identifier
            metadata: Optional additional agent configuration or metadata
            
        Returns:
            Created agent object
            
        Raises:
            ValueError: If name or platform is missing or empty, or API key is not configured
            ApiException: If the API request fails
        """
        self._http_client.ensure_authenticated()

        if not name or not name.strip():
            raise ValueError("name is required")
        if not platform or not platform.strip():
            raise ValueError("platform is required")
        
        request = CreateAgentRequest(
            name=name,
            platform=platform,
            version=version,
            metadata=metadata
        )
        
        return await self._http_client.post(
            "/api/agents",
            request,
            Agent
        )

