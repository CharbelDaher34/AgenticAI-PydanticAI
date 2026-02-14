"""Lesson 02.2: Advanced Tool Features - ToolReturn, prepare methods, retries, timeouts.

This example demonstrates:
- ToolReturn with metadata and multi-modal content
- Dynamic tool preparation with prepare methods
- Error handling and retries with ModelRetry
- Tool timeouts
- Sequential vs parallel tool execution
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import logfire
from pydantic_ai import Agent, ModelRetry, RunContext, Tool, ToolReturn
from pydantic_ai.tools import ToolDefinition

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings
from common.database import MockDatabase

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Get logger from centralized configuration
log = get_logger(__name__)

# Configure Logfire
logfire.configure(console=False)
logfire.instrument_pydantic_ai()


@dataclass
class UserContext:
    """User context with permissions and preferences."""
    
    user_id: int
    is_admin: bool
    is_premium: bool
    username: str


# Agent demonstrating advanced tool features
advanced_agent = Agent[UserContext, str](
    "openai:gpt-4o-mini",
    system_prompt="You are an assistant with access to various tools based on user permissions.",
)


# Example 1: ToolReturn with metadata
# Use ToolReturn when you need to pass additional information back to the model
@advanced_agent.tool
async def check_user_status(ctx: RunContext[UserContext]) -> ToolReturn:
    """Check the current user's status and permissions.
    
    Returns:
        ToolReturn with user info and metadata
    """
    user = ctx.deps
    
    # Build the response message
    status_lines = [
        f"User: {user.username} (ID: {user.user_id})",
        f"Account Type: {'Premium' if user.is_premium else 'Standard'}",
        f"Admin Access: {'Yes' if user.is_admin else 'No'}",
    ]
    
    # ToolReturn allows returning both a value and metadata
    # The metadata is available to tools but not sent to the model
    return ToolReturn(
        return_value="\n".join(status_lines),
        metadata={
            "user_id": user.user_id,
            "permissions": {
                "admin": user.is_admin,
                "premium": user.is_premium,
            },
            "timestamp": datetime.now().isoformat(),
        },
    )


# Example 2: Dynamic tool with prepare method
# The prepare method determines if a tool should be available for this run
async def only_for_admins(
    ctx: RunContext[UserContext], tool_def: ToolDefinition
) -> Optional[ToolDefinition]:
    """Only include this tool if the user is an admin.
    
    This is called BEFORE the model sees the tool list.
    Return None to omit the tool, or return tool_def to include it.
    """
    if ctx.deps.is_admin:
        return tool_def  # Include tool
    return None  # Omit tool


@advanced_agent.tool(prepare=only_for_admins)
async def admin_function(ctx: RunContext[UserContext], action: str) -> str:
    """Perform an admin-only action.
    
    This tool is only available to admin users due to the prepare method.
    
    Args:
        ctx: Run context
        action: The admin action to perform
    
    Returns:
        Result of the admin action
    """
    return f"Admin action '{action}' executed by {ctx.deps.username}"


async def only_for_premium(
    ctx: RunContext[UserContext], tool_def: ToolDefinition
) -> Optional[ToolDefinition]:
    """Only include this tool for premium users."""
    if ctx.deps.is_premium:
        return tool_def
    return None


@advanced_agent.tool(prepare=only_for_premium)
async def premium_analysis(ctx: RunContext[UserContext], data: str) -> str:
    """Perform premium data analysis.
    
    This tool is only available to premium users.
    
    Args:
        ctx: Run context
        data: Data to analyze
    
    Returns:
        Analysis result
    """
    return f"Premium analysis of '{data}': Advanced insights available for {ctx.deps.username}"


# Example 3: Tool with error handling and retry
# Use ModelRetry to signal transient failures that should be retried
@advanced_agent.tool
async def fetch_external_data(
    ctx: RunContext[UserContext], endpoint: str
) -> str:
    """Fetch data from an external API (simulated).
    
    Args:
        ctx: Run context
        endpoint: API endpoint to fetch
    
    Returns:
        API response data
    
    Raises:
        ModelRetry: If the request fails transiently
    """
    # Simulate API call
    # In a real implementation, this would make an actual HTTP request
    
    if endpoint == "error":
        # Signal a transient error that the model should retry
        raise ModelRetry("API is temporarily unavailable. Please try again.")
    
    if endpoint == "invalid":
        # Return an error message (not a retry)
        return f"Error: Invalid endpoint '{endpoint}'"
    
    # Simulate successful API response
    return f"Data from {endpoint}: {{'status': 'ok', 'data': [...]}}"


# Example 4: Tool with timeout
# Set timeout to prevent tools from hanging
@advanced_agent.tool(timeout=5)
async def slow_computation(ctx: RunContext[UserContext], complexity: int) -> str:
    """Perform a computation that might take time.
    
    This tool has a 5-second timeout to prevent hanging.
    
    Args:
        ctx: Run context
        complexity: Complexity level (1-10)
    
    Returns:
        Computation result
    """
    # Simulate slow computation
    await asyncio.sleep(min(complexity * 0.5, 3))
    
    return f"Computation completed: Result for complexity {complexity}"


# Example 5: Tool that returns structured data
@advanced_agent.tool
async def get_server_metrics(ctx: RunContext[UserContext]) -> dict:
    """Get current server metrics.
    
    Tools can return dictionaries, which are automatically JSON-serialized.
    
    Returns:
        Dictionary with server metrics
    """
    return {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 34.5,
        "active_users": 127,
        "timestamp": datetime.now().isoformat(),
    }


async def example_metadata():
    """Example: ToolReturn with metadata."""
    print("=== Example 1: ToolReturn with Metadata ===\n")
    
    user = UserContext(
        user_id=1,
        is_admin=True,
        is_premium=True,
        username="alice",
    )
    
    result = await advanced_agent.run(
        "What's my user status?",
        deps=user,
    )
    
    print(f"User: What's my user status?")
    print(f"Agent: {result.output}\n")


async def example_dynamic_tools_admin():
    """Example: Tools that only appear for admins."""
    print("=== Example 2: Dynamic Tools (Admin User) ===\n")
    
    admin_user = UserContext(
        user_id=1,
        is_admin=True,
        is_premium=False,
        username="admin_alice",
    )
    
    result = await advanced_agent.run(
        "Can you perform an admin action to reset the cache?",
        deps=admin_user,
    )
    
    print(f"Admin User: Can you perform an admin action to reset the cache?")
    print(f"Agent: {result.output}\n")


async def example_dynamic_tools_regular():
    """Example: Regular user doesn't see admin tools."""
    print("=== Example 3: Dynamic Tools (Regular User) ===\n")
    
    regular_user = UserContext(
        user_id=2,
        is_admin=False,
        is_premium=False,
        username="bob",
    )
    
    result = await advanced_agent.run(
        "Can you perform an admin action to reset the cache?",
        deps=regular_user,
    )
    
    print(f"Regular User: Can you perform an admin action to reset the cache?")
    print(f"Agent: {result.output}\n")


async def example_premium_tools():
    """Example: Premium-only features."""
    print("=== Example 4: Premium Features ===\n")
    
    premium_user = UserContext(
        user_id=3,
        is_admin=False,
        is_premium=True,
        username="charlie_premium",
    )
    
    result = await advanced_agent.run(
        "Run a premium analysis on sales data",
        deps=premium_user,
    )
    
    print(f"Premium User: Run a premium analysis on sales data")
    print(f"Agent: {result.output}\n")


async def example_structured_output():
    """Example: Tool returning structured data."""
    print("=== Example 5: Structured Data Output ===\n")
    
    user = UserContext(
        user_id=1,
        is_admin=True,
        is_premium=False,
        username="alice",
    )
    
    result = await advanced_agent.run(
        "What are the current server metrics?",
        deps=user,
    )
    
    print(f"User: What are the current server metrics?")
    print(f"Agent: {result.output}\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("ADVANCED TOOL FEATURES")
    print("=" * 80 + "\n")
    
    print("Key Concepts:")
    print("1. ToolReturn - Return values with metadata and multi-modal content")
    print("2. prepare methods - Dynamically include/exclude tools per run")
    print("3. ModelRetry - Signal transient errors for automatic retry")
    print("4. Timeouts - Prevent tools from hanging")
    print("5. Structured output - Return dictionaries and Pydantic models\n")
    
    print("=" * 80 + "\n")
    
    await example_metadata()
    print("-" * 80 + "\n")
    
    await example_dynamic_tools_admin()
    print("-" * 80 + "\n")
    
    await example_dynamic_tools_regular()
    print("-" * 80 + "\n")
    
    await example_premium_tools()
    print("-" * 80 + "\n")
    
    await example_structured_output()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- ToolReturn provides richer responses with metadata")
    print("- prepare methods enable permission-based tool access")
    print("- ModelRetry for transient failures, regular errors for permanent failures")
    print("- Timeouts prevent runaway tools")
    print("- Tools can return any JSON-serializable data structure")
    print("\nCheck Logfire dashboard to see tool execution details!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
