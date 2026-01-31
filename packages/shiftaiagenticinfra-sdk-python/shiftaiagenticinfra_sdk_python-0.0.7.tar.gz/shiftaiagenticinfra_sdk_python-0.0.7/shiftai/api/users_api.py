"""
API for user operations.
Provides methods for creating and managing users.
"""

from typing import Optional, Dict, Any
from ..http import HttpClient
from ..models import CreateUserRequest, User


class UsersApi:
    """API for user operations."""
    
    def __init__(self, http_client: HttpClient):
        self._http_client = http_client
    
    async def create(
        self,
        username: str,
        email: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> User:
        """
        Create a new user.
        
        POST /api/users
        
        Args:
            username: Unique username for the user (required)
            email: User's email address (required)
            metadata: Optional metadata object for storing custom user attributes
            
        Returns:
            Created user object
            
        Raises:
            ValueError: If username or email is missing or empty, or API key is not configured
            ApiException: If the API request fails
        """
        self._http_client.ensure_authenticated()

        if not username or not username.strip():
            raise ValueError("username is required")
        if not email or not email.strip():
            raise ValueError("email is required")
        
        request = CreateUserRequest(
            username=username,
            email=email,
            metadata=metadata
        )
        
        return await self._http_client.post(
            "/api/users",
            request,
            User
        )

