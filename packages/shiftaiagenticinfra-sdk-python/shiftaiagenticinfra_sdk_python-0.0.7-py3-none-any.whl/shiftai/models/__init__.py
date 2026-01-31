"""Model classes for request/response DTOs."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


@dataclass
class PlatformRegistrationRequest:
    """Request for platform registration."""
    projectName: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PlatformRegistrationResponse:
    """Response from platform registration."""
    id: Optional[int] = None
    tenantId: Optional[str] = None
    projectName: Optional[str] = None
    apiKey: Optional[str] = None
    createdAt: Optional[datetime] = None
    message: Optional[str] = None


@dataclass
class AgentData:
    """Agent information for message submission."""
    name: str
    platform: str
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PlatformMessageSubmissionRequest:
    """Request for submitting platform messages."""
    username: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    agentData: Optional[AgentData] = None
    senderType: Optional[str] = None  # "HUMAN" or "BOT"
    message: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None
    messageType: Optional[str] = None  # "TEXT"
    sourceEvent: Optional[Dict[str, Any]] = None
    ragContext: Optional[str] = None
    replyMessageId: Optional[UUID] = None
    # Optional conversation ID for HUMAN messages. If omitted, backend creates a new conversation.
    # For BOT messages, backend determines conversation from replyMessageId and ignores this field.
    conversationId: Optional[UUID] = None
    mode: Optional[str] = None


@dataclass
class ConversationMessage:
    """Simple DTO representing a conversation message with sender and message content."""
    sender: Optional[str] = None  # "HUMAN" or "BOT"
    message: Optional[str] = None


@dataclass
class WeaviateVector:
    """DTO representing a vector entry in Weaviate."""
    text: Optional[str] = None
    humanMessageId: Optional[str] = None
    botMessageId: Optional[str] = None
    conversationId: Optional[str] = None
    userId: Optional[str] = None
    agentId: Optional[str] = None
    timestamp: Optional[str] = None
    messageType: Optional[str] = None
    generatedContext: Optional[str] = None
    confidence: Optional[float] = None
    certainty: Optional[float] = None


@dataclass
class PlatformMessageSubmissionResponse:
    """Response from platform message submission."""
    success: Optional[bool] = None
    messageId: Optional[UUID] = None
    conversationId: Optional[UUID] = None
    message: Optional[str] = None
    contextualPrompt: Optional[Dict[str, Any]] = None  # Changed from str to Dict to match server
    humanQuery: Optional[str] = None  # Current HUMAN message query (senderType=HUMAN only)
    previousKConversations: Optional[List[List[ConversationMessage]]] = None  # Previous conversation turns
    similarConversations: Optional[List[WeaviateVector]] = None  # Similar conversations (senderType=HUMAN only)
    operationStatus: Optional[Dict[str, bool]] = None  # Operation status flags (senderType=BOT only)
    conversationTitle: Optional[str] = None  # LLM-generated conversation title
    # Cache metadata (only present when cache was checked)
    cacheResponse: Optional[str] = None
    cacheHit: Optional[bool] = None


@dataclass
class EndConversationRequest:
    """Request DTO for ending a conversation session."""
    conversationId: UUID


@dataclass
class EndConversationResponse:
    """Response DTO for ending a conversation session."""
    success: Optional[bool] = None
    message: Optional[str] = None
    conversationId: Optional[UUID] = None
    conversationExternalId: Optional[str] = None
    endedAt: Optional[str] = None  # ISO 8601 datetime string


@dataclass
class CreateUserRequest:
    """Request for creating a user."""
    username: str
    email: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class User:
    """User model."""
    userId: Optional[UUID] = None
    username: Optional[str] = None
    email: Optional[str] = None
    projectName: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CreateAgentRequest:
    """Request for creating an agent."""
    name: str
    platform: str
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Agent:
    """Agent model."""
    id: Optional[UUID] = None
    name: Optional[str] = None
    platform: Optional[str] = None
    version: Optional[str] = None
    projectName: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class FeedbackSubmissionRequest:
    """Request for submitting feedback (multiple feedback per BOT message)."""
    messageId: UUID  # required - BOT message ID
    feedbackTitle: str  # required - Feedback title
    feedback: str  # required - Feedback content
    liked: Optional[bool] = None  # optional - Like rating (renamed from like)
    disliked: Optional[bool] = None  # optional - Dislike rating (renamed from dislike)
    regeneration: Optional[bool] = None  # optional - Regeneration request


@dataclass
class FeedbackSubmissionResponse:
    """Response from feedback submission."""
    success: Optional[bool] = None
    feedbackId: Optional[UUID] = None  # Feedback entry ID (was botMessageId)
    message: Optional[str] = None
    submittedAt: Optional[str] = None  # ISO 8601 datetime string


@dataclass
class FeedbackDTO:
    """Single feedback entry for a BOT message (GET feedback list)."""
    id: Optional[UUID] = None  # Feedback entry ID
    feedbackTitle: Optional[str] = None
    feedback: Optional[str] = None
    liked: Optional[bool] = None
    disliked: Optional[bool] = None
    regeneration: Optional[bool] = None
    submittedAt: Optional[str] = None  # ISO 8601 datetime string


@dataclass(init=False)
class PlatformMessage:
    """Platform message model - matches backend JPA entity."""

    # Core fields
    id: Optional[UUID] = None
    message: Optional[str] = None
    sender: Optional[str] = None  # Backend uses "sender", not "senderType"
    messageType: Optional[str] = None

    # Backend relationship fields (nested objects)
    platformUser: Optional[Dict[str, Any]] = None
    agent: Optional[Dict[str, Any]] = None
    user: Optional[Dict[str, Any]] = None
    conversation: Optional[Dict[str, Any]] = None
    replyToMessage: Optional[Dict[str, Any]] = None

    # Backend primitive fields
    projectName: Optional[str] = None
    agentName: Optional[str] = None
    mode: Optional[str] = None
    timestamp: Optional[str] = None  # ISO datetime string
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None
    sourceEvent: Optional[Dict[str, Any]] = None
    messageEmbedding: Optional[str] = None
    generatedContext: Optional[str] = None
    ragContext: Optional[str] = None
    cacheHit: Optional[bool] = None
    cacheResponse: Optional[str] = None
    evalRecordId: Optional[str] = None
    evalSyncStatus: Optional[str] = None
    evalSyncError: Optional[str] = None
    evalSyncTimestamp: Optional[str] = None
    evalTotalTokens: Optional[int] = None
    evalTotalCost: Optional[float] = None
    likeFeedback: Optional[bool] = None
    dislikeFeedback: Optional[bool] = None
    feedbackText: Optional[str] = None
    regeneration: Optional[bool] = None
    feedbackUpdatedAt: Optional[str] = None

    def __init__(self, **kwargs):
        """Custom init to handle extra backend fields gracefully."""
        # Map backend field names to SDK field names
        field_mapping = {
            'sender': 'sender',  # Backend uses "sender"
            'senderType': 'sender',  # Fallback for consistency
        }

        for field_name, value in kwargs.items():
            # Apply field mapping if needed
            sdk_field = field_mapping.get(field_name, field_name)

            # Only set if field exists in dataclass
            if hasattr(self, sdk_field):
                setattr(self, sdk_field, value)


@dataclass
class DashboardMetricsDTO:
    """Dashboard metrics DTO."""
    totalUsers: Optional[int] = None
    totalAgents: Optional[int] = None
    totalQueries: Optional[int] = None
    totalResponses: Optional[int] = None
    avgResponseTimeSeconds: Optional[float] = None
    totalFeedback: Optional[int] = None
    likes: Optional[int] = None
    dislikes: Optional[int] = None
    regenerates: Optional[int] = None


@dataclass
class TopAgentDTO:
    """Top agent DTO."""
    rank: Optional[int] = None
    agentName: Optional[str] = None
    agentId: Optional[UUID] = None
    queryCount: Optional[int] = None
    satisfactionPercentage: Optional[float] = None


@dataclass
class TopUserDTO:
    """Top user DTO."""
    rank: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    userId: Optional[UUID] = None
    queryCount: Optional[int] = None
    avgResponseTimeSeconds: Optional[float] = None


@dataclass
class UserAnalyticsDTO:
    """User analytics DTO."""
    username: Optional[str] = None
    email: Optional[str] = None
    userId: Optional[UUID] = None
    queries: Optional[int] = None
    responses: Optional[int] = None
    avgResponseTimeSeconds: Optional[float] = None
    likes: Optional[int] = None
    dislikes: Optional[int] = None
    regenerates: Optional[int] = None


@dataclass
class ProjectAnalyticsResponseDTO:
    """Project analytics response DTO."""
    totalUsers: Optional[int] = None
    totalAgents: Optional[int] = None
    totalQueries: Optional[int] = None
    totalResponses: Optional[int] = None
    avgResponseTimeSeconds: Optional[float] = None
    totalFeedback: Optional[int] = None
    likes: Optional[int] = None
    dislikes: Optional[int] = None
    regenerates: Optional[int] = None
    topUserActivity: Optional[List[Any]] = None
    topDevicesByUsage: Optional[List[Any]] = None


@dataclass
class ConversationSummaryResponse:
    """Response object containing conversation summary information."""
    conversationId: Optional[UUID] = None
    startedAt: Optional[str] = None  # ISO 8601 datetime string
    endedAt: Optional[str] = None  # ISO 8601 datetime string, null if conversation is active
    userId: Optional[UUID] = None
    username: Optional[str] = None
    agentId: Optional[UUID] = None
    agentName: Optional[str] = None
    conversationTitle: Optional[str] = None  # LLM-generated conversation title


@dataclass
class ConversationMessageResponse:
    """Simplified message response for conversation messages.

    Provides a clean, readable format without deeply nested objects.
    Includes generatedContext for ALL messages (both HUMAN and BOT).
    Includes ragContext only for BOT messages (null for HUMAN messages).
    """
    id: Optional[UUID] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None  # ISO 8601 datetime string
    sender: Optional[str] = None  # "HUMAN" or "BOT"
    messageType: Optional[str] = None  # "TEXT", "IMAGE", "VIDEO", "FILE"
    userId: Optional[UUID] = None
    username: Optional[str] = None
    agentId: Optional[UUID] = None
    agentName: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None
    sourceEvent: Optional[Dict[str, Any]] = None
    replyToMessageId: Optional[UUID] = None
    generatedContext: Optional[str] = None  # Generated for ALL messages (HUMAN and BOT)
    ragContext: Optional[str] = None  # Only for BOT messages
    likeFeedback: Optional[bool] = None
    dislikeFeedback: Optional[bool] = None
    feedbackText: Optional[str] = None
    regeneration: Optional[bool] = None
    feedbackUpdatedAt: Optional[str] = None  # ISO 8601 datetime string
    trulensSyncStatus: Optional[str] = None  # "PENDING", "SUCCESS", "FAILED"
    trulensTotalTokens: Optional[int] = None
    trulensTotalCost: Optional[float] = None
    evalRecordId: Optional[str] = None
    evalSyncStatus: Optional[str] = None
    evalSyncError: Optional[str] = None
    evalSyncTimestamp: Optional[str] = None
    evalTotalTokens: Optional[int] = None
    evalTotalCost: Optional[float] = None
    conversationTitle: Optional[str] = None  # LLM-generated conversation title