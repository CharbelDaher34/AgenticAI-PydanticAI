"""Lesson 01.1: Basic Dependency Injection - Understanding RunContext.

This example demonstrates:
- Basic dependency injection with RunContext
- Accessing dependencies in tools
- Different dependency types (simple types)
- Using Logfire for tracing
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings
import logfire
from pydantic_ai import Agent, RunContext

# Get structured logger
log = get_logger(__name__)

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Configure Logfire for tracing
logfire.configure(console=False)
logfire.instrument_pydantic_ai()

# Example 1: Simple string dependency
simple_agent = Agent[str, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a helpful assistant with access to user information.",
)


@simple_agent.tool
async def get_user_name(ctx: RunContext[str]) -> str:
    """Get the current user's name from dependencies."""
    log.info("getting_user_name", user=ctx.deps)
    return f"The user's name is {ctx.deps}"


# Example 2: Integer dependency (user ID)
user_id_agent = Agent[int, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a user support assistant.",
)


@user_id_agent.tool
async def get_user_id(ctx: RunContext[int]) -> str:
    """Get the current user's ID."""
    log.info("getting_user_id", user_id=ctx.deps)
    return f"User ID: {ctx.deps}"


@user_id_agent.tool
async def check_premium_status(ctx: RunContext[int]) -> bool:
    """Check if user has premium status (IDs > 1000 are premium)."""
    is_premium = ctx.deps > 1000
    log.info("checking_premium_status", user_id=ctx.deps, is_premium=is_premium)
    return is_premium


# Example 3: datetime dependency
time_agent = Agent[datetime, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a time-aware assistant.",
)


@time_agent.tool
async def get_current_time(ctx: RunContext[datetime]) -> str:
    """Get the current time from dependencies."""
    log.info("getting_current_time", time=ctx.deps.isoformat())
    return ctx.deps.strftime("%Y-%m-%d %H:%M:%S")


@time_agent.tool
async def is_business_hours(ctx: RunContext[datetime]) -> bool:
    """Check if current time is during business hours (9 AM - 5 PM)."""
    hour = ctx.deps.hour
    is_business = 9 <= hour < 17
    log.info("checking_business_hours", hour=hour, is_business_hours=is_business)
    return is_business


async def example_simple_dependency():
    """Example with simple string dependency."""
    log.info("running_example", example="simple_dependency")
    print("=== Example 1: Simple String Dependency ===\n")
    
    user_name = "Alice Johnson"
    
    result = await simple_agent.run(
        "What is my name?",
        deps=user_name,  # Inject the user's name
    )
    
    print(f"User: {user_name}")
    print(f"Response: {result.output}\n")


async def example_user_id_dependency():
    """Example with integer dependency."""
    print("=== Example 2: Integer Dependency (User ID) ===\n")
    
    # Test with regular user
    regular_user_id = 500
    result1 = await user_id_agent.run(
        "What is my user ID and do I have premium status?",
        deps=regular_user_id,
    )
    
    print(f"User ID: {regular_user_id}")
    print(f"Response: {result1.output}\n")
    
    # Test with premium user
    premium_user_id = 1500
    result2 = await user_id_agent.run(
        "What is my user ID and do I have premium status?",
        deps=premium_user_id,
    )
    
    print(f"User ID: {premium_user_id}")
    print(f"Response: {result2.output}\n")


async def example_datetime_dependency():
    """Example with datetime dependency."""
    print("=== Example 3: DateTime Dependency ===\n")
    
    # Simulate different times
    morning_time = datetime(2024, 1, 15, 10, 30)  # 10:30 AM
    evening_time = datetime(2024, 1, 15, 19, 30)  # 7:30 PM
    
    # Morning query
    result1 = await time_agent.run(
        "What time is it and are we in business hours?",
        deps=morning_time,
    )
    
    print(f"Current time: {morning_time}")
    print(f"Response: {result1.output}\n")
    
    # Evening query
    result2 = await time_agent.run(
        "What time is it and are we in business hours?",
        deps=evening_time,
    )
    
    print(f"Current time: {evening_time}")
    print(f"Response: {result2.output}\n")


async def example_reusing_agent():
    """Demonstrate reusing the same agent with different dependencies."""
    print("=== Example 4: Reusing Agent with Different Dependencies ===\n")
    
    users = ["Alice", "Bob", "Charlie"]
    
    for user in users:
        result = await simple_agent.run(
            "Greet me by name",
            deps=user,
        )
        print(f"{user}: {result.output}")
    
    print()


async def main():
    """Run all dependency injection examples."""
    print("\n" + "=" * 80)
    print("BASIC DEPENDENCY INJECTION EXAMPLES")
    print("=" * 80 + "\n")
    
    # await example_simple_dependency()
    # await example_user_id_dependency()
    # await example_datetime_dependency()
    await example_reusing_agent()
    
    print("=" * 80)
    print("Check Logfire dashboard to see dependency usage in traces!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
