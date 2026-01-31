"""
HTTP client for making async API calls.
Thread-safe and stateless - can be shared across multiple threads.
"""

import json
import dataclasses
from typing import TypeVar, Type, List, Dict, Any, Optional
from datetime import datetime

import httpx

from .exceptions import (
    ApiException,
    UnauthorizedException,
    BadRequestException,
    NotFoundException,
    ServerException,
)

T = TypeVar('T')


class HttpClient:
    """HTTP client wrapper for making async API calls."""
    
    def __init__(self, base_url: str, api_key: Optional[str]):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL of the API (e.g., "http://localhost:8081")
            api_key: Optional API key for authentication
        """
        # Normalize baseUrl - remove trailing slash
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        
        # Create httpx client with timeouts
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=30.0),
            headers={
                "Content-Type": "application/json",
            }
        )

    def ensure_authenticated(self) -> None:
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
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Map HTTP status codes to custom exceptions."""
        status_code = response.status_code
        try:
            response_body = response.text
        except Exception:
            response_body = None
        
        if status_code == 401:
            raise UnauthorizedException("Unauthorized", response_body)
        elif status_code == 400:
            raise BadRequestException("Bad Request", response_body)
        elif status_code == 404:
            raise NotFoundException("Not Found", response_body)
        elif 500 <= status_code < 600:
            raise ServerException(status_code, "Server Error", response_body)
        else:
            raise ApiException(status_code, f"API request failed with status {status_code}", response_body)
    
    def _deserialize_datetime(self, value: Any) -> Any:
        """Deserialize datetime strings to datetime objects."""
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except Exception:
                pass
        elif isinstance(value, dict):
            return {k: self._deserialize_datetime(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._deserialize_datetime(item) for item in value]
        return value

    def _filter_known_fields(self, data: Dict[str, Any], response_type: Type) -> Dict[str, Any]:
        """
        Filter dictionary to only include fields that exist in the response_type.

        This provides similar functionality to Jackson's @JsonIgnoreProperties(ignoreUnknown = true)
        for Python dataclasses.
        """
        if not hasattr(response_type, '__dataclass_fields__'):
            return data

        known_fields = set(response_type.__dataclass_fields__.keys())
        return {k: v for k, v in data.items() if k in known_fields}

    async def get(self, path: str, response_type: Type[T]) -> T:
        """
        Execute GET request with API key authentication.

        Args:
            path: API path (e.g., "/api/platform/messages")
            response_type: Expected response type class

        Returns:
            Deserialized response object
        """
        url = f"{self.base_url}{path}"
        headers = {
            "Api-Key": self.api_key,
        }

        try:
            response = await self.client.get(url, headers=headers)

            if not response.is_success:
                self._handle_error(response)

            data = response.json()
            # Handle datetime deserialization
            data = self._deserialize_datetime(data)

            # Convert dict to response_type object
            if isinstance(data, dict):
                # Filter to known fields to prevent TypeError on unknown fields
                filtered_data = self._filter_known_fields(data, response_type)
                return response_type(**filtered_data)
            return data
            
        except (UnauthorizedException, BadRequestException, NotFoundException, ServerException, ApiException):
            raise
        except Exception as e:
            print(f"Error executing GET request to {path}: {e}")
            raise ApiException(0, f"IO error: {str(e)}")
    
    async def get_list(self, path: str, element_type: Type[T]) -> List[T]:
        """
        Execute GET request for List responses.

        Args:
            path: API path
            element_type: Expected element type class

        Returns:
            List of deserialized response objects
        """
        url = f"{self.base_url}{path}"
        headers = {
            "Api-Key": self.api_key,
        }

        try:
            response = await self.client.get(url, headers=headers)

            if not response.is_success:
                self._handle_error(response)

            data = response.json()
            # Handle datetime deserialization
            data = self._deserialize_datetime(data)

            if not isinstance(data, list):
                raise ApiException(0, f"Expected list, got {type(data)}")

            # Convert list of dicts to list of objects
            result = []
            for item in data:
                if isinstance(item, dict):
                    # Filter to known fields to prevent TypeError on unknown fields
                    filtered_item = self._filter_known_fields(item, element_type)
                    result.append(element_type(**filtered_item))
                else:
                    result.append(item)
            return result
            
        except (UnauthorizedException, BadRequestException, NotFoundException, ServerException, ApiException):
            raise
        except Exception as e:
            print(f"Error executing GET request to {path}: {e}")
            raise ApiException(0, f"IO error: {str(e)}")
    
    async def post(self, path: str, request_body: Any, response_type: Type[T]) -> T:
        """
        Execute POST request with API key authentication.
        
        Args:
            path: API path
            request_body: Request body object (will be serialized to JSON)
            response_type: Expected response type class
            
        Returns:
            Deserialized response object
        """
        url = f"{self.base_url}{path}"
        headers = {
            "Api-Key": self.api_key,
        }
        
        # Serialize request body
        if request_body is not None:
            if dataclasses.is_dataclass(request_body):
                # Use dataclasses.asdict() for proper nested serialization
                json_body = json.dumps(dataclasses.asdict(request_body), default=str)
            elif isinstance(request_body, dict):
                json_body = json.dumps(request_body, default=str)
            else:
                json_body = json.dumps(request_body, default=str)
        else:
            json_body = None
        
        try:
            response = await self.client.post(url, headers=headers, content=json_body)
            
            if not response.is_success:
                self._handle_error(response)
            
            data = response.json()
            # Handle datetime deserialization
            data = self._deserialize_datetime(data)
            
            # Convert dict to response_type object
            if isinstance(data, dict):
                # Filter to known fields to prevent TypeError on unknown fields
                filtered_data = self._filter_known_fields(data, response_type)
                return response_type(**filtered_data)
            return data
            
        except (UnauthorizedException, BadRequestException, NotFoundException, ServerException, ApiException):
            raise
        except Exception as e:
            print(f"Error executing POST request to {path}: {e}")
            raise ApiException(0, f"IO error: {str(e)}")
    
    async def post_list(self, path: str, request_body: Any, element_type: Type[T]) -> List[T]:
        """
        Execute POST request for List responses with API key authentication.
        
        Args:
            path: API path
            request_body: Request body object (will be serialized to JSON)
            element_type: Expected element type class
            
        Returns:
            List of deserialized response objects
        """
        url = f"{self.base_url}{path}"
        headers = {
            "Api-Key": self.api_key,
        }
        
        # Serialize request body
        if request_body is not None:
            if dataclasses.is_dataclass(request_body):
                # Use dataclasses.asdict() for proper nested serialization
                json_body = json.dumps(dataclasses.asdict(request_body), default=str)
            elif isinstance(request_body, dict):
                json_body = json.dumps(request_body, default=str)
            else:
                json_body = json.dumps(request_body, default=str)
        else:
            json_body = None
        
        try:
            response = await self.client.post(url, headers=headers, content=json_body)
            
            if not response.is_success:
                self._handle_error(response)
            
            data = response.json()
            # Handle datetime deserialization
            data = self._deserialize_datetime(data)
            
            if not isinstance(data, list):
                raise ApiException(0, f"Expected list, got {type(data)}")
            
            # Convert list of dicts to list of objects
            result: List[T] = []
            for item in data:
                if isinstance(item, dict):
                    # Filter to known fields to prevent TypeError on unknown fields
                    filtered_item = self._filter_known_fields(item, element_type)
                    result.append(element_type(**filtered_item))
                else:
                    result.append(item)
            return result
            
        except (UnauthorizedException, BadRequestException, NotFoundException, ServerException, ApiException):
            raise
        except Exception as e:
            print(f"Error executing POST request to {path}: {e}")
            raise ApiException(0, f"IO error: {str(e)}")
    
    async def post_without_auth(self, path: str, request_body: Any, response_type: Type[T]) -> T:
        """
        Execute POST request without API key authentication.
        
        Args:
            path: API path
            request_body: Request body object
            response_type: Expected response type class
            
        Returns:
            Deserialized response object
        """
        url = f"{self.base_url}{path}"
        headers = {}
        
        # Serialize request body
        if request_body is not None:
            if dataclasses.is_dataclass(request_body):
                # Use dataclasses.asdict() for proper nested serialization
                json_body = json.dumps(dataclasses.asdict(request_body), default=str)
            elif isinstance(request_body, dict):
                json_body = json.dumps(request_body, default=str)
            else:
                json_body = json.dumps(request_body, default=str)
        else:
            json_body = None
        
        try:
            response = await self.client.post(url, headers=headers, content=json_body)
            
            if not response.is_success:
                self._handle_error(response)
            
            data = response.json()
            # Handle datetime deserialization
            data = self._deserialize_datetime(data)
            
            # Convert dict to response_type object
            if isinstance(data, dict):
                # Filter to known fields to prevent TypeError on unknown fields
                filtered_data = self._filter_known_fields(data, response_type)
                return response_type(**filtered_data)
            return data
            
        except (UnauthorizedException, BadRequestException, NotFoundException, ServerException, ApiException):
            raise
        except Exception as e:
            print(f"Error executing POST request to {path}: {e}")
            raise ApiException(0, f"IO error: {str(e)}")
    
    async def get_map_without_auth(self, path: str) -> Dict[str, Any]:
        """
        Execute GET request without auth, returning raw map.
        
        Args:
            path: API path
            
        Returns:
            Dictionary response
        """
        url = f"{self.base_url}{path}"
        
        try:
            response = await self.client.get(url)
            
            if not response.is_success:
                self._handle_error(response)
            
            return response.json()
            
        except (UnauthorizedException, BadRequestException, NotFoundException, ServerException, ApiException):
            raise
        except Exception as e:
            print(f"Error executing GET request to {path}: {e}")
            raise ApiException(0, f"IO error: {str(e)}")
    
    async def post_map_without_auth(self, path: str, request_body: Any = None) -> Dict[str, Any]:
        """
        Execute POST request without auth, returning raw map.
        
        Args:
            path: API path
            request_body: Optional request body
            
        Returns:
            Dictionary response
        """
        url = f"{self.base_url}{path}"
        
        # Serialize request body
        if request_body is not None:
            if dataclasses.is_dataclass(request_body):
                # Use dataclasses.asdict() for proper nested serialization
                json_body = json.dumps(dataclasses.asdict(request_body), default=str)
            elif isinstance(request_body, dict):
                json_body = json.dumps(request_body, default=str)
            else:
                json_body = json.dumps(request_body, default=str)
        else:
            json_body = None
        
        try:
            response = await self.client.post(url, content=json_body)
            
            if not response.is_success:
                self._handle_error(response)
            
            return response.json()
            
        except (UnauthorizedException, BadRequestException, NotFoundException, ServerException, ApiException):
            raise
        except Exception as e:
            print(f"Error executing POST request to {path}: {e}")
            raise ApiException(0, f"IO error: {str(e)}")
    
    async def post_map(self, path: str, request_body: Any = None) -> Dict[str, Any]:
        """
        Execute POST request with auth, returning raw map.
        
        Args:
            path: API path
            request_body: Optional request body
            
        Returns:
            Dictionary response
        """
        url = f"{self.base_url}{path}"
        headers = {
            "Api-Key": self.api_key,
        }
        
        # Serialize request body
        if request_body is not None:
            if dataclasses.is_dataclass(request_body):
                # Use dataclasses.asdict() for proper nested serialization
                json_body = json.dumps(dataclasses.asdict(request_body), default=str)
            elif isinstance(request_body, dict):
                json_body = json.dumps(request_body, default=str)
            else:
                json_body = json.dumps(request_body, default=str)
        else:
            json_body = None
        
        try:
            response = await self.client.post(url, headers=headers, content=json_body)
            
            if not response.is_success:
                self._handle_error(response)
            
            return response.json()
            
        except (UnauthorizedException, BadRequestException, NotFoundException, ServerException, ApiException):
            raise
        except Exception as e:
            print(f"Error executing POST request to {path}: {e}")
            raise ApiException(0, f"IO error: {str(e)}")

