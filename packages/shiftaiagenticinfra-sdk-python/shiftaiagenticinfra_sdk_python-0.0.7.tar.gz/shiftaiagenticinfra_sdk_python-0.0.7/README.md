# Shiftai Agentic Infra Python SDK

This SDK is the official gateway to the Shift AI Agentic Infra services, enabling developers to directly integrate and use agentic capabilities in their applications.

## About ShiftAI

<p align="center">
  <a href="https://theshiftai.in">
    <img src="https://img.shields.io/badge/Website-theshiftai.in-blue?style=for-the-badge">
  </a>
  <a href="https://github.com/shiftaitop">
    <img src="https://img.shields.io/badge/GitHub-shiftaitop-black?style=for-the-badge">
  </a>
  <a href="https://www.linkedin.com/company/theshiftai-in/">
    <img src="https://img.shields.io/badge/LinkedIn-ShiftAI-blue?style=for-the-badge&logo=linkedin">
  </a>
  <a href="https://x.com/shift_ai_first">
    <img src="https://img.shields.io/badge/X(Twitter)-@shift__ai__first-black?style=for-the-badge&logo=x">
  </a>
  <a href="https://www.reddit.com/user/TheShiftAI/">
    <img src="https://img.shields.io/badge/Reddit-TheShiftAI-FF4500?style=for-the-badge&logo=reddit">
  </a>
  <a href="https://substack.com/@shiftaifirst">
    <img src="https://img.shields.io/badge/Substack-ShiftAI-orange?style=for-the-badge&logo=substack">
  </a>
</p>

**ShiftAI** is an AI infrastructure and consulting company focused on building
**production-ready AI systems** that help organizations transform business
operations using AI.

ShiftAI works with enterprises and product teams to design, integrate, and deploy
AI-driven systems that move beyond experimentation into real-world production.

---

## Official ShiftAI Links

- 🌐 Website: https://theshiftai.in  
- 🐙 GitHub Organization: https://github.com/shiftaitop  
- 💼 LinkedIn (Company): https://www.linkedin.com/company/theshiftai-in/  
- 🐦 Twitter (X): https://x.com/shift_ai_first  
- 🔗 Reddit: https://www.reddit.com/user/TheShiftAI/  
- ✍️ Substack: https://substack.com/@shiftaifirst  
  

### Founder
- **Suresh Gokarakonda**
- LinkedIn: https://www.linkedin.com/in/gokarakonda/

---

## About ShiftAI Agentic Infrastructure

**ShiftAI Agentic Infrastructure** is a **multi-tenant platform** for managing
AI-powered conversations, agents, and workflows.

Organizations register as isolated tenants and receive secure API keys for access.
The platform automatically manages conversation sessions, threads messages between
humans and agents, and maintains complete conversation history.

It supports multiple LLM providers through a **pluggable architecture**, enabling
provider switching without application-level changes.

On every interaction, the platform generates AI-enhanced contextual prompts derived
from conversation history, summarizing conversation flow, key facts, and resolved
ambiguities. This context is returned to clients and stored for future interactions.

The platform also includes built-in **evaluation and analytics** capabilities that
assess response quality, relevance, and reasoning across user–agent interactions,
providing visibility into conversation performance over time.

---

## Platform Usage Overview

Using ShiftAI Agentic Infrastructure through this SDK, applications typically:

1. Initialize the SDK client using project credentials  
2. Submit human messages to start or continue conversations  
3. Receive contextual intelligence generated from conversation history  
4. Generate agent responses using the provided context  
5. Submit agent responses linked to prior human messages  
6. Monitor conversations and performance using built-in analytics  

All operations are automatically scoped to the authenticated project, ensuring
secure isolation between organizations using the platform.

---






## Dependencies

### Allowed Dependencies (Only These)

- ✅ `httpx` - Async HTTP client (required for API calls)
- ✅ `dataclasses` - Standard library (for data models)
- ✅ `typing` - Standard library (for type hints)
- ✅ Standard library only: `json`, `datetime`, `uuid`, `asyncio`
- ✅ SDK internal modules - All models and utilities owned by SDK



## Installation & Usage Modes



### Package Usage 

```bash
pip install shiftaiagenticinfra-sdk-python
```

## Quick Start

```python
import asyncio
from shiftai import ShiftaiagenticinfraClient

async def main():
    # 1. Initialize client
    client = ShiftaiagenticinfraClient(
        base_url="api.theshiftai.in",
        api_key="pk_your_api_key"
    )

    # 2. Send a human message
    human_response = await client.messages.send_human_message(
        username="john_doe",
        message="Hello, how can I help you?",
        agent_name="SupportBot",
        agent_platform="OpenAI",
        user_email="john@example.com",
        agent_version="1.0.0"  # Required: Agent version 
    )

    print(f"Message sent! ID: {human_response.messageId}")

    # 3. Send a bot response
    bot_response = await client.messages.send_bot_message(
        username="john_doe",
        message="I can help you with your questions!",
        agent_name="SupportBot",
        agent_platform="OpenAI",
        agent_version="1.0.0",  # Required: Agent version 
        reply_message_id=human_response.messageId,
        rag_context="Retrieved context from knowledge base...",
        user_email="john@example.com"
    )

    # 4. Get analytics
    dashboard = await client.analytics.get_dashboard()
    print(f"Total users: {dashboard.totalUsers}")

    # 5. Close client
    await client.close()

asyncio.run(main())
```

This example imports and runs immediately when the SDK source is copied into any Python project with httpx installed.

## API Reference

### Platform API

#### `await platform.register(project_name, metadata=None)`
Register a new project and get API key.

**Parameters:**
- `project_name` (str, **required**): Unique name for the project/platform (e.g., "my-chatbot", "customer-support-app")
- `metadata` (dict, **optional**): Additional project metadata (e.g., `{"environment": "production", "version": "1.0"}`)

**Return Type:** `PlatformRegistrationResponse`

**Example:**
```python
response = await client.platform.register(
    project_name="MyProject",
    metadata={"environment": "production"}
)
print(f"API Key: {response.apiKey}")
```

### Messages API

#### `await messages.send_human_message(...)`
Send a human message with automatic user/agent creation.

**Parameters:**
- `username` (str, **required**): User identifier (e.g., "john_doe", "user123")
- `message` (str, **required**): The actual message content (e.g., "Hello, how can I help you?")
- `agent_name` (str, **required**): Target agent name (e.g., "SupportBot", "GPT-4")
- `agent_platform` (str, **required**): Agent platform/provider (e.g., "OpenAI", "Azure", "Anthropic")
- `user_email` (str, **required**): User's email address for identification (e.g., "john@example.com")
- `user_metadata` (dict, **optional**): Custom user attributes (e.g., `{"role": "premium", "subscription": "gold"}`)
- `intent` (str, **optional**): Message intent classification (e.g., "question", "complaint", "request")
- `entities` (dict, **optional**): Extracted named entities (e.g., `{"person": "John", "location": "New York"}`)
- `annotations` (dict, **optional**): Additional message annotations (e.g., `{"priority": "high", "tags": ["urgent"]}`)
- `source_event` (dict, **optional**): Original event data from source system
- `agent_version` (str, **optional**): Agent version/model (e.g., "gpt-4", "claude-2") - **Required in database**
- `agent_metadata` (dict, **optional**): Agent configuration data (e.g., `{"temperature": 0.7, "max_tokens": 1000}`)
- `mode` (str, **optional**): Mode identifier for the message. Allowed values: `"SIMPLE"` or `"EXPAND"`
- `conversation_id` (UUID, **optional**): Conversation ID to store the HUMAN message in. If omitted, backend creates a new conversation automatically.

**Return Type:** `PlatformMessageSubmissionResponse`

#### `await messages.send_bot_message(...)`
Send a bot response to a human message.

**Parameters:**
- `username` (str, **required**): User identifier (must match the human message sender)
- `message` (str, **required**): Bot response content (e.g., "I can help you with that!")
- `agent_name` (str, **required**): Agent name (must match the human message agent)
- `agent_platform` (str, **required**): Agent platform (must match the human message platform)
- `reply_message_id` (UUID, **required**): ID of the human message being replied to
- `rag_context` (str, **required**): RAG context used for generating the response
- `user_email` (str, **required**): User's email address for identification
- `user_metadata` (dict, **optional**): User metadata
- `intent` (str, **optional**): Response intent
- `entities` (dict, **optional**): Extracted entities from response
- `annotations` (dict, **optional**): Response annotations
- `source_event` (dict, **optional**): Source event data
- `agent_version` (str, **optional**): Agent version/model - **Required in database**
- `agent_metadata` (dict, **optional**): Agent configuration
- `mode` (str, **optional**): Mode identifier for the message. Allowed values: `"SIMPLE"` or `"EXPAND"`

**Return Type:** `PlatformMessageSubmissionResponse`

**Response Notes (Cache):**
- `cacheHit` / `cacheResponse` may be present when the backend cache API was checked (typically for HUMAN messages).

### Platform Session API

#### `await platform_session.initiate_session(request=None)`
Initiate a new conversation session.

POST `/api/platformsession/initiate`

**Return Type:** `Dict[str, Any]` (raw response body as returned by the server)

#### `await platform_session.end_conversation(conversation_id)`
End an active conversation session explicitly.

POST `/api/platformsession/endconversation`

**Parameters:**
- `conversation_id` (UUID, **required**): Conversation identifier to end

**Return Type:** `EndConversationResponse`

#### `await messages.submit(request)`
Low-level message submission with full control.

**Parameters:**
- `request` (PlatformMessageSubmissionRequest, **required**): Complete message request object

**Return Type:** `PlatformMessageSubmissionResponse`

#### `await messages.get_all()`
Get all messages for the authenticated project.

**Return Type:** `List[PlatformMessage]`

#### `await messages.get_by_id(message_id)`
Get a specific message by ID.

**Parameters:**
- `message_id` (UUID, required): Message identifier

**Return Type:** `PlatformMessage`

#### `await messages.get_by_agent(agent_id)`
Get all messages sent by a specific agent.

**Parameters:**
- `agent_id` (UUID, required): Agent identifier

**Return Type:** `List[PlatformMessage]`

### Users API

#### `await users.create(username, email, metadata=None)`
Create a new user.

**Parameters:**
- `username` (str, **required**): Unique username (e.g., "john_doe", "user123")
- `email` (str, **required**): User's email address (e.g., "john@example.com")
- `metadata` (dict, **optional**): Custom user attributes (e.g., `{"role": "premium", "subscription": "gold", "preferences": {"theme": "dark"}}`)

**Return Type:** `User`

**Example:**
```python
user = await client.users.create_user(
    username="john_doe",
    email="john@example.com",
    metadata={"role": "premium"}
)
print(f"Created user: {user.username}")
```

### Agents API

#### `await agents.create(name, platform, version=None, metadata=None)`
Create a new AI agent.

**Parameters:**
- `name` (str, **required**): Display name for the agent (e.g., "CustomerSupportBot", "CodeAssistant")
- `platform` (str, **required**): Platform/provider (e.g., "OpenAI", "Azure", "Anthropic")
- `version` (str, **optional**): Model version (e.g., "gpt-4", "claude-2", "gpt-3.5-turbo")
- `metadata` (dict, **optional**): Agent configuration (e.g., `{"temperature": 0.7, "max_tokens": 2000, "system_prompt": "You are a helpful assistant"}`)

**Return Type:** `Agent`

**Example:**
```python
agent = await client.agents.create_agent(
    name="ChatGPT-4",
    platform="OpenAI",
    version="4.0",
    metadata={"model": "gpt-4", "temperature": 0.7}
)
print(f"Created agent: {agent.name}")
```

### Analytics API

#### `await analytics.submit_feedback(message_id, feedback_title, feedback, liked=None, disliked=None, regeneration=None)`
Submit user feedback on a BOT message (multiple feedback per message allowed).

**Parameters:**
- `message_id` (UUID, **required**): ID of the BOT message receiving feedback
- `feedback_title` (str, **required**): Title for the feedback (e.g., "Response Quality Feedback")
- `feedback` (str, **required**): Feedback content (e.g., "The response was very helpful")
- `liked` (bool, **optional**): User liked the response (true/false)
- `disliked` (bool, **optional**): User disliked the response (true/false)
- `regeneration` (bool, **optional**): User requested regeneration (true/false)

**Return Type:** `FeedbackSubmissionResponse` (includes `feedbackId`, `submittedAt`)

#### `await analytics.get_message_feedback(message_id)`
Get all feedback submissions for a specific BOT message (most recent first).

**Parameters:**
- `message_id` (UUID, **required**): UUID of the BOT message

**Return Type:** `List[FeedbackDTO]`

#### `await analytics.get_dashboard()`
Get project dashboard metrics.

**Return Type:** `DashboardMetricsDTO`

#### `await analytics.get_top_agents(limit=5)`
Get top-performing agents by usage.

**Parameters:**
- `limit` (int, **optional**): Maximum number of results (default: 5, max: 100)

**Return Type:** `List[TopAgentDTO]`

#### `await analytics.get_top_users(limit=5)`
Get most active users.

**Parameters:**
- `limit` (int, **optional**): Maximum number of results (default: 5, max: 100)

**Return Type:** `List[TopUserDTO]`

#### `await analytics.get_user_analytics()`
Get analytics for all users.

**Return Type:** `List[UserAnalyticsDTO]`

#### `await analytics.get_project_data(top_limit=10)`
Get project-level analytics data.

**Parameters:**
- `top_limit` (int, **optional**): Limit for top results (default: 10, max: 100)

**Return Type:** `ProjectAnalyticsResponseDTO`

#### `await analytics.get_all(top_limit=5)`
Get comprehensive analytics data.

**Parameters:**
- `top_limit` (int, **optional**): Limit for top results (default: 5, max: 100)

**Return Type:** `Dict[str, Any]`

#### `await analytics.initialize()`
Initialize analytics for the project.

**Return Type:** `Dict[str, Any]`

### Conversations API

#### `await conversations.get_messages_by_conversation_id(conversation_id)`
Get all messages in a conversation.

**Parameters:**
- `conversation_id` (UUID, required): Conversation identifier

**Return Type:** `List[ConversationMessageResponse]`

#### `await conversations.get_all_conversations()`
Get all conversations for the project.

**Return Type:** `List[ConversationSummaryResponse]`

#### `await conversations.get_user_conversations(username)`
Get all conversations for a specific user.

**Parameters:**
- `username` (str, required): Username

**Return Type:** `List[ConversationSummaryResponse]`

## Error Handling

The SDK surfaces HTTP errors as typed exceptions:

```python
from shiftai.http import (
    ApiException,
    UnauthorizedException,
    BadRequestException,
    NotFoundException,
    ServerException
)

try:
    response = await client.messages.send_human_message(
        username="user",
        message="Hello",
        agent_name="Bot",
        agent_platform="OpenAI"
    )
except BadRequestException as e:
    print(f"Invalid request: {e}")
except UnauthorizedException as e:
    print("Invalid API key")
except ApiException as e:
    print(f"API error {e.status_code}: {e}")
```




## Why This SDK Is Safe to Use

### No Hidden Dependencies
- **Explicit dependency list**: Only 1 external library needed
- **No transitive dependencies**: No "dependency hell"
- **Standard async library**: httpx is the de facto async HTTP library for Python

### Proven Portability
- **Minimal setup**: Just add httpx to requirements.txt
- **No configuration**: No complex setup or initialization

This SDK is built to enable developers to easily integrate and use the Shift AI Agentic Infra in their own applications



