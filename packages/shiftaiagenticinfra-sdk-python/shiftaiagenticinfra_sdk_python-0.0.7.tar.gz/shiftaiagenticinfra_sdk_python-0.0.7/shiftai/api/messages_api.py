"""
API for platform message operations.
Provides methods for submitting messages and retrieving message history.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from ..http import HttpClient
from ..models import (
    PlatformMessageSubmissionRequest,
    PlatformMessageSubmissionResponse,
    PlatformMessage,
    AgentData,
)


class MessagesApi:
    """API for platform message operations."""
    
    def __init__(self, http_client: HttpClient):
        self._http_client = http_client
    
    async def send_human_message(
        self,
        username: str,
        message: str,
        agent_name: str,
        agent_platform: str,
        user_email: str,
        user_metadata: Optional[Dict[str, Any]] = None,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        annotations: Optional[Dict[str, Any]] = None,
        source_event: Optional[Dict[str, Any]] = None,
        agent_version: Optional[str] = None,
        agent_metadata: Optional[Dict[str, Any]] = None,
        mode: Optional[str] = None,
        conversation_id: Optional[UUID] = None,
    ) -> PlatformMessageSubmissionResponse:
        """
        Send a human message.
        Automatically sets senderType=HUMAN and messageType=TEXT.
        
        POST /api/platform/messages/submit
        
        Args:
            username: Username of the individual sending the message (required)
            message: The actual message content (required)
            agent_name: Agent name identifier (required)
            agent_platform: Agent platform or provider (required)
            user_email: Email address for user identification (required)
            user_metadata: Optional user-specific metadata
            intent: Optional detected intent or purpose of the message
            entities: Optional named entities extracted from the message
            annotations: Optional additional annotations or tags
            source_event: Optional original source event data
            agent_version: Optional agent version or model identifier
            agent_metadata: Optional additional agent configuration metadata
            mode: Optional mode identifier for the message
            conversation_id: Optional conversation ID for HUMAN messages. If not provided, backend creates a new conversation.
            
        Returns:
            PlatformMessageSubmissionResponse with message ID and contextual prompt
            
        Raises:
            ValueError: If required fields are missing or API key is not configured
            ApiException: If the API request fails
        """
        self._http_client.ensure_authenticated()

        # Validate required fields
        if not username or not username.strip():
            raise ValueError("username is required")
        if not message or not message.strip():
            raise ValueError("message is required")
        if not agent_name or not agent_name.strip():
            raise ValueError("agent_name is required")
        if not agent_platform or not agent_platform.strip():
            raise ValueError("agent_platform is required")
        if not agent_version or not agent_version.strip():
            raise ValueError("agent_version is required")
        if not user_email or not user_email.strip():
            raise ValueError("user_email is required")

        # Build agent data
        agent_data = AgentData(
            name=agent_name,
            platform=agent_platform,
            version=agent_version,
            metadata=agent_metadata
        )
        
        # Build request
        request = PlatformMessageSubmissionRequest(
            username=username,
            email=user_email,
            metadata=user_metadata,
            message=message,
            intent=intent,
            entities=entities,
            annotations=annotations,
            sourceEvent=source_event,
            agentData=agent_data,
            senderType="HUMAN",  # Auto-set
            messageType="TEXT",  # Auto-set
            conversationId=conversation_id,
            mode=mode
        )
        
        return await self._http_client.post(
            "/api/platform/messages/submit",
            request,
            PlatformMessageSubmissionResponse
        )
    
    async def send_bot_message(
        self,
        username: str,
        message: str,
        agent_name: str,
        agent_platform: str,
        reply_message_id: UUID,
        rag_context: str,
        user_email: str,
        user_metadata: Optional[Dict[str, Any]] = None,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        annotations: Optional[Dict[str, Any]] = None,
        source_event: Optional[Dict[str, Any]] = None,
        agent_version: Optional[str] = None,
        agent_metadata: Optional[Dict[str, Any]] = None,
        mode: Optional[str] = None,
    ) -> PlatformMessageSubmissionResponse:
        """
        Send a bot message.
        Automatically sets senderType=BOT and messageType=TEXT.
        Requires replyMessageId and ragContext.
        
        POST /api/platform/messages/submit
        
        Args:
            username: Username of the individual (required)
            message: The actual message content (required)
            agent_name: Agent name identifier (required)
            agent_platform: Agent platform or provider (required)
            reply_message_id: ID of the message this is replying to (required)
            rag_context: Retrieved context from RAG (required)
            user_email: Email address for user identification (required)
            user_metadata: Optional user-specific metadata
            intent: Optional detected intent
            entities: Optional named entities
            annotations: Optional additional annotations
            source_event: Optional original source event data
            agent_version: Optional agent version
            agent_metadata: Optional additional agent configuration metadata
            mode: Optional mode identifier for the message
            
        Returns:
            PlatformMessageSubmissionResponse with message ID
            
        Raises:
            ValueError: If required fields are missing or API key is not configured
            ApiException: If the API request fails
        """
        self._http_client.ensure_authenticated()

        # Validate required fields
        if not username or not username.strip():
            raise ValueError("username is required")
        if not message or not message.strip():
            raise ValueError("message is required")
        if not agent_name or not agent_name.strip():
            raise ValueError("agent_name is required")
        if not agent_platform or not agent_platform.strip():
            raise ValueError("agent_platform is required")
        if reply_message_id is None:
            raise ValueError("reply_message_id is required for bot messages")
        if not rag_context or not rag_context.strip():
            raise ValueError("rag_context is required for bot messages")
        if not agent_version or not agent_version.strip():
            raise ValueError("agent_version is required")
        if not user_email or not user_email.strip():
            raise ValueError("user_email is required")

        # Build agent data
        agent_data = AgentData(
            name=agent_name,
            platform=agent_platform,
            version=agent_version,
            metadata=agent_metadata
        )
        
        # Build request
        request = PlatformMessageSubmissionRequest(
            username=username,
            email=user_email,
            metadata=user_metadata,
            message=message,
            intent=intent,
            entities=entities,
            annotations=annotations,
            sourceEvent=source_event,
            agentData=agent_data,
            replyMessageId=reply_message_id,
            ragContext=rag_context,
            senderType="BOT",   # Auto-set
            messageType="TEXT", # Auto-set
            mode=mode
        )
        
        return await self._http_client.post(
            "/api/platform/messages/submit",
            request,
            PlatformMessageSubmissionResponse
        )
    
    async def submit(
        self,
        request: PlatformMessageSubmissionRequest
    ) -> PlatformMessageSubmissionResponse:
        """
        Submit a single platform message (legacy method - kept for backward compatibility).
        
        POST /api/platform/messages/submit
        
        Args:
            request: Message submission request object
            
        Returns:
            PlatformMessageSubmissionResponse with message ID and contextual prompt
        """
        self._http_client.ensure_authenticated()

        return await self._http_client.post(
            "/api/platform/messages/submit",
            request,
            PlatformMessageSubmissionResponse
        )
    
    async def get_all(self) -> List[PlatformMessage]:
        """
        Get all platform messages for the authenticated project.
        
        GET /api/platform/messages
        
        Returns:
            List of all messages
        """
        self._http_client.ensure_authenticated()

        return await self._http_client.get_list(
            "/api/platform/messages",
            PlatformMessage
        )
    
    async def get_by_id(self, message_id: UUID) -> PlatformMessage:
        """
        Get platform message by ID.
        
        GET /api/platform/messages/{messageId}
        
        Args:
            message_id: UUID of the message
            
        Returns:
            The message object
        """
        self._http_client.ensure_authenticated()

        return await self._http_client.get(
            f"/api/platform/messages/{message_id}",
            PlatformMessage
        )
    
    async def get_by_agent(self, agent_id: UUID) -> List[PlatformMessage]:
        """
        Get platform messages by agent.
        
        GET /api/platform/messages/agent/{agentId}
        
        Args:
            agent_id: UUID of the agent
            
        Returns:
            List of messages from the agent
        """
        self._http_client.ensure_authenticated()

        return await self._http_client.get_list(
            f"/api/platform/messages/agent/{agent_id}",
            PlatformMessage
        )

