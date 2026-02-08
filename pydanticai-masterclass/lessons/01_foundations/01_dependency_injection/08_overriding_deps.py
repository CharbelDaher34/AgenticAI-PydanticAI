"""Lesson 01.8: Overriding Dependencies for Testing.

This example demonstrates:
- Using agent.override() to inject test dependencies
- Testing agent behavior without external dependencies
- Isolating tests from real APIs and databases
- The override pattern from PydanticAI documentation
"""

import asyncio
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import logfire
from pydantic_ai import Agent, RunContext

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings

# Get structured logger
log = get_logger(__name__)

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()


# ============================================================================
# Production Dependencies
# ============================================================================

@dataclass
class EmailDeps:
    """Real email sending dependencies.
    
    In production, this would connect to an actual email service.
    """
    
    api_key: str
    sender_email: str
    
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email via external service."""
        log.info("sending_real_email", to=to, subject=subject)
        
        # In production, this would call SendGrid, AWS SES, etc.
        # For this example, we'll just simulate it
        print(f"📧 [REAL] Sending email to {to}: {subject}")
        
        # Simulate network delay
        await asyncio.sleep(0.1)
        return True


# ============================================================================
# Test Dependencies (Override)
# ============================================================================

@dataclass
class MockEmailDeps(EmailDeps):
    """Test version of email dependencies.
    
    Inherits from EmailDeps but overrides behavior for testing.
    """
    
    # Track emails sent during tests
    sent_emails: list[dict[str, str]] = field(default_factory=list)
    should_fail: bool = False
    
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Mock email sending for tests."""
        log.info("sending_mock_email", to=to, subject=subject)
        
        print(f"📧 [MOCK] Recording email to {to}: {subject}")
        
        # Simulate failure if configured
        if self.should_fail:
            return False
        
        # Record email for assertions
        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body,
        })
        
        return True


# ============================================================================
# Agent Definition
# ============================================================================

notification_agent = Agent[EmailDeps, str](
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a notification assistant. "
        "You help send email notifications to users."
    ),
)


@notification_agent.tool
async def send_notification(
    ctx: RunContext[EmailDeps],
    recipient: str,
    message_type: str,
) -> str:
    """Send an email notification to a user.
    
    Args:
        ctx: Runtime context with email dependencies
        recipient: Email address of recipient
        message_type: Type of notification (welcome, alert, reminder)
    """
    # Prepare email content based on type
    subjects = {
        "welcome": "Welcome to our service!",
        "alert": "Important Alert",
        "reminder": "Friendly Reminder",
    }
    
    bodies = {
        "welcome": "Thank you for joining us. We're excited to have you!",
        "alert": "This is an important notification that requires your attention.",
        "reminder": "This is a friendly reminder about your upcoming task.",
    }
    
    subject = subjects.get(message_type, "Notification")
    body = bodies.get(message_type, "You have a new notification.")
    
    # Use dependency to send email
    success = await ctx.deps.send_email(recipient, subject, body)
    
    if success:
        return f"✓ Notification sent to {recipient}"
    else:
        return f"✗ Failed to send notification to {recipient}"


# ============================================================================
# Application Code (calls the agent)
# ============================================================================

async def welcome_new_user(email: str) -> str:
    """Application function that uses the agent.
    
    In a real app, this might be called from an API endpoint.
    Note: This uses real dependencies by default.
    """
    # In production, create real dependencies
    deps = EmailDeps(
        api_key="prod_key_12345",
        sender_email="noreply@example.com",
    )
    
    # Call agent
    result = await notification_agent.run(
        f"Send a welcome email to {email}",
        deps=deps,
    )
    
    return result.output


async def send_alert(email: str) -> str:
    """Send an alert notification."""
    deps = EmailDeps(
        api_key="prod_key_12345",
        sender_email="alerts@example.com",
    )
    
    result = await notification_agent.run(
        f"Send an alert notification to {email}",
        deps=deps,
    )
    
    return result.output


# ============================================================================
# Tests using agent.override()
# ============================================================================

async def test_welcome_email():
    """Test: Welcome emails are sent correctly."""
    print("=== Test 1: Welcome Email ===\n")
    
    # Create test dependencies
    mock_deps = MockEmailDeps(
        api_key="test_key",
        sender_email="test@example.com",
        sent_emails=[],
    )
    
    # Override the agent's dependencies for this test
    with notification_agent.override(deps=mock_deps):
        # Call application code - it will use our test dependencies!
        result = await welcome_new_user("alice@example.com")
        print(f"Result: {result}\n")
    
    # Verify email was "sent"
    assert len(mock_deps.sent_emails) == 1, "Should send 1 email"
    email = mock_deps.sent_emails[0]
    
    assert email["to"] == "alice@example.com"
    assert "welcome" in email["subject"].lower()
    
    print("✓ Test passed: Email sent correctly\n")


async def test_multiple_notifications():
    """Test: Multiple notifications in sequence."""
    print("=== Test 2: Multiple Notifications ===\n")
    
    mock_deps = MockEmailDeps(
        api_key="test_key",
        sender_email="test@example.com",
        sent_emails=[],
    )
    
    with notification_agent.override(deps=mock_deps):
        await welcome_new_user("user1@example.com")
        await welcome_new_user("user2@example.com")
        await send_alert("user1@example.com")
    
    # Verify all emails were sent
    assert len(mock_deps.sent_emails) == 3, "Should send 3 emails"
    
    print(f"✓ Test passed: {len(mock_deps.sent_emails)} emails sent")
    for email in mock_deps.sent_emails:
        print(f"  - {email['to']}: {email['subject']}")
    print()


async def test_email_failure_handling():
    """Test: Handle email sending failures gracefully."""
    print("=== Test 3: Email Failure Handling ===\n")
    
    # Configure mock to simulate failure
    mock_deps = MockEmailDeps(
        api_key="test_key",
        sender_email="test@example.com",
        sent_emails=[],
        should_fail=True,  # Simulate failure
    )
    
    with notification_agent.override(deps=mock_deps):
        result = await welcome_new_user("user@example.com")
        print(f"Result: {result}\n")
    
    # Email should not be in sent list (it failed)
    assert len(mock_deps.sent_emails) == 0, "Should not record failed emails"
    assert "Failed to send" in result, "Should indicate failure"
    
    print("✓ Test passed: Failure handled correctly\n")


async def test_nested_overrides():
    """Test: Nested override contexts."""
    print("=== Test 4: Nested Overrides ===\n")
    
    # First level override
    mock_deps_1 = MockEmailDeps(
        api_key="test_key_1",
        sender_email="test1@example.com",
        sent_emails=[],
    )
    
    with notification_agent.override(deps=mock_deps_1):
        await welcome_new_user("outer@example.com")
        
        # Second level override
        mock_deps_2 = MockEmailDeps(
            api_key="test_key_2",
            sender_email="test2@example.com",
            sent_emails=[],
        )
        
        with notification_agent.override(deps=mock_deps_2):
            await welcome_new_user("inner@example.com")
        
        # Back to first override
        await send_alert("outer2@example.com")
    
    # Verify separation
    assert len(mock_deps_1.sent_emails) == 2, "Outer context: 2 emails"
    assert len(mock_deps_2.sent_emails) == 1, "Inner context: 1 email"
    
    print(f"✓ Test passed: Nested overrides work correctly")
    print(f"  Outer context: {len(mock_deps_1.sent_emails)} emails")
    print(f"  Inner context: {len(mock_deps_2.sent_emails)} emails\n")


# ============================================================================
# Integration test (without override)
# ============================================================================

async def test_production_integration():
    """Integration test: Use real dependencies (no override).
    
    This demonstrates that the agent works with real dependencies
    when override is not used.
    """
    print("=== Integration Test: Real Dependencies ===\n")
    
    # Real dependencies (but still simulated in this example)
    real_deps = EmailDeps(
        api_key="real_prod_key",
        sender_email="production@example.com",
    )
    
    # No override - uses real dependencies
    result = await notification_agent.run(
        "Send a welcome email to production-user@example.com",
        deps=real_deps,
    )
    
    print(f"Result: {result.output}")
    print("✓ Integration test passed\n")


async def example_comparison():
    """Compare running with and without override."""
    print("=== Example: With vs Without Override ===\n")
    
    print("1. WITHOUT override (uses whatever deps are passed):")
    real_deps = EmailDeps(
        api_key="real_key",
        sender_email="real@example.com",
    )
    result1 = await notification_agent.run(
        "Send a reminder to user@example.com",
        deps=real_deps,
    )
    print(f"   Result: {result1.output}\n")
    
    print("2. WITH override (test deps replace any passed deps):")
    mock_deps = MockEmailDeps(
        api_key="test_key",
        sender_email="test@example.com",
        sent_emails=[],
    )
    
    with notification_agent.override(deps=mock_deps):
        # Even if we call application code that creates its own deps,
        # the override takes precedence!
        result2 = await welcome_new_user("user@example.com")
        print(f"   Result: {result2.output}")
        print(f"   Emails captured: {len(mock_deps.sent_emails)}\n")


async def main():
    """Run all override examples and tests."""
    print("\n" + "=" * 80)
    print("OVERRIDING DEPENDENCIES FOR TESTING")
    print("=" * 80 + "\n")
    
    print("The agent.override() pattern allows you to:")
    print("1. Test agents without external dependencies (no real API calls)")
    print("2. Control agent behavior precisely in tests")
    print("3. Verify what the agent did (e.g., which emails were sent)")
    print("4. Test error conditions safely\n")
    
    # Run tests
    await test_welcome_email()
    await test_multiple_notifications()
    await test_email_failure_handling()
    await test_nested_overrides()
    await test_production_integration()
    await example_comparison()
    
    print("=" * 80)
    print("ALL TESTS PASSED! ✓")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("- Use agent.override(deps=...) to inject test dependencies")
    print("- Override works even when application code creates its own deps")
    print("- Override context can be nested")
    print("- Tests are isolated and don't affect real systems")
    print("- Mock dependencies can track calls for assertions")
    print("\nCheck Logfire to see both real and mocked operations!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
