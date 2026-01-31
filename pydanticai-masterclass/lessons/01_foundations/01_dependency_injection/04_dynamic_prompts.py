"""Lesson 01.4: Dynamic System Prompts - Using dependencies in prompts.

This example demonstrates:
- Dynamic system prompts based on dependencies
- Personalizing agent behavior per user
- Context-aware prompts
- Time-based prompt adaptation
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import logfire
from pydantic_ai import Agent, RunContext

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings
from common.database import MockDatabase

# Get structured logger
log = get_logger(__name__)

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()


@dataclass
class UserContext:
    """User context for personalized interactions."""
    
    database: MockDatabase
    user_id: int
    user_name: str
    subscription_tier: str  # "free", "pro", "enterprise"
    current_time: datetime


# Create agent with dynamic system prompt
personalized_agent = Agent[UserContext, str](
    "openai:gpt-4o-mini",
)


@personalized_agent.system_prompt
async def get_system_prompt(ctx: RunContext[UserContext]) -> str:
    """Generate dynamic system prompt based on user context.
    
    This function is called BEFORE each agent run, allowing you to
    customize the agent's behavior based on current dependencies.
    """
    # Get user info from database
    user = await ctx.deps.database.get_user(ctx.deps.user_id)
    
    # Time-based greeting
    hour = ctx.deps.current_time.hour
    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 18:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    # Subscription-based features
    tier_info = {
        "free": "They have a free account with basic features.",
        "pro": "They have a Pro account with access to premium features.",
        "enterprise": "They have an Enterprise account with full access to all features.",
    }
    
    # Build dynamic prompt
    prompt = f"""You are a helpful AI assistant for our platform.

Current Context:
- User: {ctx.deps.user_name} (ID: {ctx.deps.user_id})
- Email: {user.email if user else 'unknown'}
- Subscription: {ctx.deps.subscription_tier.upper()} tier
- Time: {ctx.deps.current_time.strftime('%Y-%m-%d %H:%M')}

Greeting: {time_greeting}, {ctx.deps.user_name}!

Subscription Info: {tier_info.get(ctx.deps.subscription_tier, 'Unknown tier')}

Instructions:
- Address the user by name naturally
- Be aware of their subscription tier and only suggest features they have access to
- Use appropriate time-based greetings
- Provide personalized assistance based on their account history
- Be friendly but professional
"""
    
    return prompt


@personalized_agent.tool
async def get_my_subscription(ctx: RunContext[UserContext]) -> str:
    """Get current subscription tier information."""
    tier = ctx.deps.subscription_tier
    
    features = {
        "free": [
            "Basic product search",
            "Up to 5 orders per month",
            "Email support",
        ],
        "pro": [
            "Advanced product search",
            "Unlimited orders",
            "Priority email support",
            "Order tracking",
            "Exclusive deals",
        ],
        "enterprise": [
            "All Pro features",
            "Dedicated account manager",
            "24/7 phone support",
            "Custom integrations",
            "API access",
            "Volume discounts",
        ],
    }
    
    result = f"Your current subscription: {tier.upper()}\n\nFeatures:\n"
    for feature in features.get(tier, []):
        result += f"- {feature}\n"
    
    return result


@personalized_agent.tool
async def upgrade_subscription(ctx: RunContext[UserContext], target_tier: str) -> str:
    """Suggest subscription upgrade options.
    
    Args:
        ctx: Runtime context with user dependencies
        target_tier: Target subscription tier ("pro" or "enterprise")
    """
    current_tier = ctx.deps.subscription_tier
    
    if target_tier.lower() not in ["pro", "enterprise"]:
        return "Invalid tier. Choose 'pro' or 'enterprise'."
    
    if current_tier == target_tier.lower():
        return f"You're already on the {target_tier.upper()} tier!"
    
    prices = {
        "pro": 29.99,
        "enterprise": 299.99,
    }
    
    return (
        f"Upgrade to {target_tier.upper()}!\n"
        f"Price: ${prices[target_tier.lower()]}/month\n"
        f"Contact sales@example.com to upgrade your account."
    )


async def example_free_tier_user():
    """Example with free tier user."""
    print("=== Example 1: Free Tier User (Morning) ===\n")
    
    ctx = UserContext(
        database=MockDatabase(),
        user_id=1,
        user_name="Alice",
        subscription_tier="free",
        current_time=datetime(2024, 1, 15, 9, 30),  # 9:30 AM
    )
    
    result = await personalized_agent.run(
        "What features do I have access to?",
        deps=ctx,
    )
    
    print(f"User: What features do I have access to?")
    print(f"Agent: {result.output}\n")


async def example_pro_tier_user():
    """Example with pro tier user."""
    print("=== Example 2: Pro Tier User (Afternoon) ===\n")
    
    ctx = UserContext(
        database=MockDatabase(),
        user_id=2,
        user_name="Bob",
        subscription_tier="pro",
        current_time=datetime(2024, 1, 15, 14, 0),  # 2:00 PM
    )
    
    result = await personalized_agent.run(
        "I'm interested in upgrading to enterprise. What are the benefits?",
        deps=ctx,
    )
    
    print(f"User: I'm interested in upgrading to enterprise. What are the benefits?")
    print(f"Agent: {result.output}\n")


async def example_enterprise_user():
    """Example with enterprise tier user."""
    print("=== Example 3: Enterprise User (Evening) ===\n")
    
    ctx = UserContext(
        database=MockDatabase(),
        user_id=3,
        user_name="Charlie",
        subscription_tier="enterprise",
        current_time=datetime(2024, 1, 15, 19, 30),  # 7:30 PM
    )
    
    result = await personalized_agent.run(
        "Tell me about my subscription and what makes it special.",
        deps=ctx,
    )
    
    print(f"User: Tell me about my subscription and what makes it special.")
    print(f"Agent: {result.output}\n")


async def example_time_awareness():
    """Demonstrate time-aware prompts."""
    print("=== Example 4: Time-Aware Responses ===\n")
    
    times = [
        (datetime(2024, 1, 15, 8, 0), "8 AM"),
        (datetime(2024, 1, 15, 13, 0), "1 PM"),
        (datetime(2024, 1, 15, 20, 0), "8 PM"),
    ]
    
    for time, label in times:
        ctx = UserContext(
            database=MockDatabase(),
            user_id=1,
            user_name="Alice",
            subscription_tier="pro",
            current_time=time,
        )
        
        result = await personalized_agent.run(
            "Hello! How are you?",
            deps=ctx,
        )
        
        print(f"Time: {label}")
        print(f"Agent: {result.output}\n")


async def example_same_agent_different_users():
    """Show how one agent adapts to different users."""
    print("=== Example 5: One Agent, Different Users ===\n")
    
    users = [
        ("Alice", 1, "free"),
        ("Bob", 2, "pro"),
        ("Charlie", 3, "enterprise"),
    ]
    
    current_time = datetime(2024, 1, 15, 10, 0)
    
    for name, user_id, tier in users:
        ctx = UserContext(
            database=MockDatabase(),
            user_id=user_id,
            user_name=name,
            subscription_tier=tier,
            current_time=current_time,
        )
        
        result = await personalized_agent.run(
            "Give me a quick summary of my account.",
            deps=ctx,
        )
        
        print(f"User: {name} ({tier})")
        print(f"Agent: {result.output}\n")


async def main():
    """Run all dynamic prompt examples."""
    print("\n" + "=" * 80)
    print("DYNAMIC SYSTEM PROMPT EXAMPLES")
    print("=" * 80 + "\n")
    
    await example_free_tier_user()
    await example_pro_tier_user()
    await example_enterprise_user()
    await example_time_awareness()
    await example_same_agent_different_users()
    
    print("=" * 80)
    print("Check Logfire to see how prompts change based on context!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
