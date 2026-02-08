"""Lesson 02.5: Built-in Tools - Provider-native tools executed by LLM infrastructure.

This example demonstrates:
- WebSearchTool for web searches
- CodeExecutionTool for secure code execution
- Dynamic configuration of built-in tools
- Provider-specific built-in tools
- Conditional inclusion based on context

Note: Built-in tools are executed by the LLM provider's infrastructure, not your code.
They're available for providers like OpenAI, Anthropic, Google, xAI, and Groq.
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.builtin_tools import (
    CodeExecutionTool,
    WebSearchTool,
)

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Get logger from centralized configuration
log = get_logger(__name__)

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()


@dataclass
class SearchContext:
    """Context for search operations."""
    
    user_location: Optional[str] = None
    enable_code_execution: bool = False
    max_search_results: int = 5


# Example 1: Agent with web search
# WebSearchTool enables the model to search the web for current information
# Note: This requires a provider that supports web search (OpenAI with 'gpt-5', etc.)
search_agent = Agent[SearchContext, str](
    "openai:gpt-4o-mini",  # Web search available on supported models
    system_prompt=(
        "You are a research assistant with access to web search. "
        "Use web search to find current information when needed."
    ),
)


# Example 2: Dynamic built-in tool configuration
# Use a function to configure built-in tools based on context
async def configure_web_search(
    ctx: RunContext[SearchContext],
) -> Optional[WebSearchTool]:
    """Configure web search tool dynamically.
    
    This function is called before each run to configure the WebSearchTool.
    Return None to disable web search for this run.
    
    Args:
        ctx: Run context with user preferences
    
    Returns:
        WebSearchTool configuration or None to disable
    """
    # Enable web search with user's location if available
    if ctx.deps.user_location:
        return WebSearchTool(
            # user_location helps provide localized search results
            user_location={"city": ctx.deps.user_location},
        )
    
    # Enable basic web search without location
    return WebSearchTool()


async def configure_code_execution(
    ctx: RunContext[SearchContext],
) -> Optional[CodeExecutionTool]:
    """Configure code execution tool dynamically.
    
    Only enable code execution if explicitly allowed in context.
    
    Args:
        ctx: Run context
    
    Returns:
        CodeExecutionTool or None to disable
    """
    if ctx.deps.enable_code_execution:
        return CodeExecutionTool()
    
    return None  # Disabled by default for security


# Agent with dynamically configured built-in tools
dynamic_agent = Agent[SearchContext, str](
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a versatile assistant. Your capabilities depend on the user's context. "
        "Use web search and code execution when available."
    ),
    builtin_tools=[configure_web_search, configure_code_execution],
)


async def example_web_search():
    """Example: Using web search for current information.
    
    Note: This example demonstrates the pattern, but web search requires
    a compatible model (OpenAI's gpt-5, Anthropic Claude, etc.)
    """
    print("=== Example 1: Web Search Tool ===\n")
    
    ctx = SearchContext(user_location="San Francisco")
    
    try:
        # Ask a question that requires current information
        result = await dynamic_agent.run(
            "What's the current weather in San Francisco?",
            deps=ctx,
        )
        
        print(f"User: What's the current weather in San Francisco?")
        print(f"Agent: {result.output}\n")
        print("(Web search was used to get current weather data)\n")
    except Exception as e:
        print(f"Note: Web search requires a compatible model.")
        print(f"Error: {type(e).__name__}: {e}\n")
        print("Web search is available on:")
        print("- OpenAI: gpt-5 models")
        print("- Anthropic: Claude models")
        print("- Google: Gemini models")
        print("- xAI: Grok models\n")


async def example_code_execution():
    """Example: Using code execution for calculations.
    
    Note: This demonstrates the pattern. Code execution requires
    a compatible model and proper configuration.
    """
    print("=== Example 2: Code Execution Tool ===\n")
    
    # Context with code execution enabled
    ctx = SearchContext(enable_code_execution=True)
    
    try:
        result = await dynamic_agent.run(
            "Calculate the factorial of 20 and format it with commas",
            deps=ctx,
        )
        
        print(f"User: Calculate the factorial of 20 and format it with commas")
        print(f"Agent: {result.output}\n")
        print("(Code execution was used to perform the calculation)\n")
    except Exception as e:
        print(f"Note: Code execution requires a compatible model.")
        print(f"Error: {type(e).__name__}: {e}\n")


async def example_conditional_tools():
    """Example: Built-in tools that conditionally appear."""
    print("=== Example 3: Conditional Built-in Tools ===\n")
    
    # Scenario A: No location, no code execution
    print("Scenario A: Limited capabilities")
    ctx_limited = SearchContext(user_location=None, enable_code_execution=False)
    
    result = await dynamic_agent.run(
        "What tools do you have available?",
        deps=ctx_limited,
    )
    
    print(f"User: What tools do you have available?")
    print(f"Agent (limited): {result.output}\n")
    
    # Scenario B: Full capabilities
    print("Scenario B: Full capabilities")
    ctx_full = SearchContext(
        user_location="New York", enable_code_execution=True
    )
    
    result = await dynamic_agent.run(
        "What tools do you have available?",
        deps=ctx_full,
    )
    
    print(f"User: What tools do you have available?")
    print(f"Agent (full): {result.output}\n")


async def example_web_search_research():
    """Example: Research task using web search."""
    print("=== Example 4: Research Task ===\n")
    
    ctx = SearchContext(user_location="Seattle")
    
    try:
        result = await dynamic_agent.run(
            "What are the top 3 programming languages in 2024 according to recent surveys?",
            deps=ctx,
        )
        
        print(f"User: What are the top 3 programming languages in 2024?")
        print(f"Agent: {result.output}\n")
    except Exception as e:
        print(f"Note: This requires a model with web search support.")
        print(f"Current model may not support this feature.\n")


async def example_location_based_search():
    """Example: Location-aware search results."""
    print("=== Example 5: Location-Based Search ===\n")
    
    # Different locations
    locations = ["Tokyo", "London", "Sydney"]
    
    for location in locations:
        ctx = SearchContext(user_location=location)
        
        print(f"\nSearching from: {location}")
        print(f"Query: What are popular local restaurants?")
        
        try:
            result = await dynamic_agent.run(
                "What are popular local restaurants?",
                deps=ctx,
            )
            
            print(f"Results: {result.output[:100]}...")
        except Exception as e:
            print(f"Note: Requires web search support in the model")
    
    print()


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("BUILT-IN TOOLS EXAMPLES")
    print("=" * 80 + "\n")
    
    print("Key Concepts:")
    print("1. Built-in tools are executed by the LLM provider, not your code")
    print("2. WebSearchTool - Search the web for current information")
    print("3. CodeExecutionTool - Securely execute code in sandboxed environment")
    print("4. Dynamic configuration - Enable/disable tools based on context")
    print("5. Provider-specific - Different providers support different built-in tools\n")
    
    print("Available Built-in Tools:")
    print("- WebSearchTool (OpenAI, Anthropic, Google, xAI, Groq)")
    print("- CodeExecutionTool (OpenAI, Anthropic)")
    print("- ImageGenerationTool (OpenAI)")
    print("- WebFetchTool (Anthropic)")
    print("- MemoryTool (Anthropic)")
    print("- FileSearchTool (OpenAI)\n")
    
    print("=" * 80 + "\n")
    
    await example_web_search()
    print("-" * 80 + "\n")
    
    await example_code_execution()
    print("-" * 80 + "\n")
    
    await example_conditional_tools()
    print("-" * 80 + "\n")
    
    await example_web_search_research()
    print("-" * 80 + "\n")
    
    await example_location_based_search()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- Built-in tools extend agent capabilities without custom code")
    print("- Use dynamic configuration to enable/disable tools per request")
    print("- WebSearchTool provides access to current, real-time information")
    print("- CodeExecutionTool enables complex calculations and data processing")
    print("- Different providers support different built-in tools")
    print("\nNote: Some examples may not work with gpt-4o-mini.")
    print("Upgrade to gpt-5 or use compatible providers for full functionality.")
    print("\nCheck Logfire dashboard to see built-in tool usage!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
