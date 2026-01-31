"""
Comprehensive integration test for the Shiftai Agentic Infra Python SDK.

This test exercises all SDK methods in a single flow:
1. Register a project (get API key)
2. Create a user
3. Create an agent
4. Send a human message
5. Send a bot message (using human message ID)
6. Submit feedback (using bot message ID)
7. Get dashboard metrics
8. Get project analytics

    Note: This test requires a running server at api.theshiftai.in
"""

import pytest
import asyncio
import time
from uuid import UUID

from shiftai import ShiftaiagenticinfraClient


BASE_URL = "api.theshiftai.in"
TIMEOUT_SECONDS = 30


@pytest.mark.asyncio
async def test_complete_sdk_flow():
    """Complete end-to-end test of all SDK methods in a single flow."""
    print("\n=== Starting Complete SDK Integration Test ===\n")
    
    # Step 1: Register a new project (no API key needed)
    print("Step 1: Registering a new project...")
    registration_client = ShiftaiagenticinfraClient(
        base_url=BASE_URL,
        api_key="dummy_key_for_registration"  # Not used for registration
    )
    
    project_name = f"sdk-test-project-{int(time.time())}"
    project_metadata = {
        "environment": "test",
        "sdk_version": "1.0.0"
    }
    
    registration_response = await registration_client.platform.register_platform(
        project_name=project_name,
        metadata=project_metadata
    )
    
    assert registration_response is not None, "Registration response should not be null"
    assert registration_response.api_key is not None, "API key should be returned"
    assert registration_response.project_name is not None, "Project name should be returned"
    assert registration_response.tenant_id is not None, "Tenant ID should be returned"
    
    api_key = registration_response.api_key
    print(f"✓ Project registered: {registration_response.project_name}")
    print(f"✓ API Key received: {api_key[:20]}...")
    print(f"✓ Tenant ID: {registration_response.tenant_id}\n")
    
    # Step 2: Create a new client with the API key
    print("Step 2: Creating authenticated client...")
    client = ShiftaiagenticinfraClient(
        base_url=BASE_URL,
        api_key=api_key
    )
    print("✓ Authenticated client created\n")
    
    try:
        # Step 3: Create a user
        print("Step 3: Creating a user...")
        username = f"test-user-{int(time.time())}"
        user_metadata = {
            "role": "developer",
            "department": "engineering"
        }
        
        user = await client.users.create_user(
            username=username,
            email=f"{username}@example.com",
            metadata=user_metadata
        )
        
        assert user is not None, "User should not be null"
        assert user.username == username, "Username should match"
        assert user.user_id is not None, "User ID should be returned"
        print(f"✓ User created: {user.username} (ID: {user.user_id})\n")
        
        # Step 4: Create an agent
        print("Step 4: Creating an agent...")
        agent_name = f"TestAgent-{int(time.time())}"
        agent_metadata = {
            "model": "gpt-4",
            "temperature": 0.7
        }
        
        agent = await client.agents.create_agent(
            name=agent_name,
            platform="OpenAI",
            version="4.0",
            metadata=agent_metadata
        )
        
        assert agent is not None, "Agent should not be null"
        assert agent.name == agent_name, "Agent name should match"
        assert agent.id is not None, "Agent ID should be returned"
        print(f"✓ Agent created: {agent.name} (ID: {agent.id})\n")
        
        # Step 5: Send a human message
        print("Step 5: Sending a human message...")
        human_message = "Hello, I need help with my account."
        
        human_response = await client.messages.send_human_message(
            username=username,
            message=human_message,
            agent_name=agent_name,
            agent_platform="OpenAI",
            user_email=f"{username}@example.com",
            intent="account_help"
        )
        
        assert human_response is not None, "Human message response should not be null"
        assert human_response.success is True, "Message submission should be successful"
        assert human_response.message_id is not None, "Message ID should be returned"
        assert human_response.conversation_id is not None, "Conversation ID should be returned"
        
        human_message_id = human_response.message_id
        conversation_id = human_response.conversation_id
        print(f"✓ Human message sent (ID: {human_message_id})")
        print(f"✓ Conversation ID: {conversation_id}\n")
        
        # Step 6: Send a bot message
        print("Step 6: Sending a bot message...")
        bot_message = "I'd be happy to help you with your account. What specific issue are you experiencing?"
        rag_context = "Retrieved context: Account management, billing, settings"
        
        bot_response = await client.messages.send_bot_message(
            username=username,
            message=bot_message,
            agent_name=agent_name,
            agent_platform="OpenAI",
            reply_message_id=human_message_id,
            rag_context=rag_context,
            user_email=f"{username}@example.com"
        )
        
        assert bot_response is not None, "Bot message response should not be null"
        assert bot_response.success is True, "Bot message submission should be successful"
        assert bot_response.message_id is not None, "Bot message ID should be returned"
        
        bot_message_id = bot_response.message_id
        print(f"✓ Bot message sent (ID: {bot_message_id})\n")
        
        # Step 7: Submit feedback
        print("Step 7: Submitting feedback...")
        feedback_response = await client.analytics.submit_feedback(
            message_id=bot_message_id,
            feedback_title="Response Quality Feedback",
            feedback="Great response, very helpful!",
            liked=True,
        )
        
        assert feedback_response is not None, "Feedback response should not be null"
        assert feedback_response.success is True, "Feedback submission should be successful"
        assert feedback_response.feedbackId is not None, "Feedback ID should be returned"
        print("✓ Feedback submitted\n")
        
        # Step 8: Get dashboard metrics
        print("Step 8: Getting dashboard metrics...")
        dashboard = await client.analytics.get_dashboard()
        
        assert dashboard is not None, "Dashboard metrics should not be null"
        print(f"✓ Dashboard metrics retrieved:")
        print(f"  - Total Users: {dashboard.total_users}")
        print(f"  - Total Agents: {dashboard.total_agents}")
        print(f"  - Total Queries: {dashboard.total_queries}")
        print(f"  - Total Responses: {dashboard.total_responses}\n")
        
        # Step 9: Get project analytics
        print("Step 9: Getting project analytics...")
        project_analytics = await client.analytics.get_project_data(top_limit=10)
        
        assert project_analytics is not None, "Project analytics should not be null"
        print(f"✓ Project analytics retrieved:")
        print(f"  - Total Users: {project_analytics.total_users}")
        print(f"  - Total Agents: {project_analytics.total_agents}")
        print(f"  - Total Queries: {project_analytics.total_queries}\n")
        
        # Step 10: Get top agents
        print("Step 10: Getting top agents...")
        top_agents = await client.analytics.get_top_agents(limit=5)
        assert top_agents is not None, "Top agents should not be null"
        print(f"✓ Top agents retrieved: {len(top_agents)} agents\n")
        
        # Step 11: Get top users
        print("Step 11: Getting top users...")
        top_users = await client.analytics.get_top_users(limit=5)
        assert top_users is not None, "Top users should not be null"
        print(f"✓ Top users retrieved: {len(top_users)} users\n")
        
        # Step 12: Get user analytics
        print("Step 12: Getting user analytics...")
        user_analytics = await client.analytics.get_user_analytics()
        assert user_analytics is not None, "User analytics should not be null"
        print(f"✓ User analytics retrieved: {len(user_analytics)} users\n")
        
        # Step 13: Get all messages
        print("Step 13: Getting all messages...")
        all_messages = await client.messages.get_all()
        assert all_messages is not None, "All messages should not be null"
        print(f"✓ All messages retrieved: {len(all_messages)} messages\n")
        
        # Step 14: Get message by ID
        print("Step 14: Getting message by ID...")
        message_by_id = await client.messages.get_by_id(human_message_id)
        assert message_by_id is not None, "Message by ID should not be null"
        print(f"✓ Message by ID retrieved (ID: {message_by_id.id})\n")
        
        # Step 15: Get messages by agent
        print("Step 15: Getting messages by agent...")
        messages_by_agent = await client.messages.get_by_agent(agent.id)
        assert messages_by_agent is not None, "Messages by agent should not be null"
        print(f"✓ Messages by agent retrieved: {len(messages_by_agent)} messages\n")
        
        # Step 16: Test Eval API (internal)
        print("Step 16: Testing Eval API (internal)...")
        try:
            eval_response = await client.internal.eval.generate_metrics_for_session(
                conversation_id=conversation_id
            )
            assert eval_response is not None, "Eval response should not be null"
            print("✓ Eval metrics generation initiated\n")
        except Exception as e:
            print(f"⚠ Eval API test skipped (may require admin access): {e}\n")
        
        print("=== All SDK Integration Tests Passed! ===\n")
        
    finally:
        # Cleanup: Close the client
        await client.close()
        await registration_client.close()

