"""
API for platform registration.
Provides methods for registering new projects and obtaining API keys.
"""

from typing import Optional, Dict, Any
from ..http import HttpClient
from ..models import PlatformRegistrationRequest, PlatformRegistrationResponse


class PlatformApi:
    """API for platform registration operations."""
    
    def __init__(self, http_client: HttpClient):
        self._http_client = http_client
    
    async def register(
        self,
        project_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PlatformRegistrationResponse:
        """
        Register a new project/platform and get API key.
        
        POST /api/platform/register
        
        Args:
            project_name: Unique name for the project/platform (required)
            metadata: Optional metadata object containing project details
            
        Returns:
            PlatformRegistrationResponse containing API key
            
        Raises:
            ValueError: If project_name is missing or empty
            ApiException: If the API request fails
        """
        if not project_name or not project_name.strip():
            raise ValueError("project_name is required")
        
        request = PlatformRegistrationRequest(
            projectName=project_name,
            metadata=metadata
        )
        
        return await self._http_client.post_without_auth(
            "/api/platform/register",
            request,
            PlatformRegistrationResponse
        )

