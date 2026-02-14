"""Lesson 02.6: Common Tools - Ready-to-use tool implementations.

This example demonstrates:
- DuckDuckGo search tool (free)
- Tavily search tool (paid with free credits)
- Exa neural search toolset
- When to use each search tool
- Integrating common tools with your agents
"""

import asyncio
import os
import sys
from pathlib import Path

import logfire
from pydantic_ai import Agent

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Get logger from centralized configuration
log = get_logger(__name__)

# Configure Logfire
logfire.configure(console=False)
logfire.instrument_pydantic_ai()


# Example 1: DuckDuckGo Search (Free)
# DuckDuckGo provides free web search without API keys
try:
    from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
    
    ddg_agent = Agent(
        "openai:gpt-4o-mini",
        system_prompt=(
            "You are a research assistant with access to DuckDuckGo search. "
            "Use search to find current information about any topic."
        ),
        tools=[duckduckgo_search_tool()],
    )
    
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    print("Note: DuckDuckGo tool requires 'duckduckgo-search' package")
    print("Install with: uv add duckduckgo-search\n")


# Example 2: Tavily Search (Paid with free tier)
# Tavily provides high-quality search results optimized for LLMs
# Requires API key but offers free credits
try:
    from pydantic_ai.common_tools.tavily import tavily_search_tool
    
    # Check if TAVILY_API_KEY is set
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    
    if tavily_api_key:
        tavily_agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=(
                "You are a research assistant with access to Tavily search. "
                "Tavily provides high-quality, LLM-optimized search results."
            ),
            tools=[tavily_search_tool(api_key=tavily_api_key)],
        )
        TAVILY_AVAILABLE = True
    else:
        TAVILY_AVAILABLE = False
        print("Note: Tavily tool requires TAVILY_API_KEY environment variable")
        print("Get your free API key at: https://tavily.com\n")
except ImportError:
    TAVILY_AVAILABLE = False
    print("Note: Tavily tool is included in pydantic-ai")


# Example 3: Exa Search (Neural/AI Search)
# Exa provides neural search, similar pages, content retrieval, and AI answers
try:
    from pydantic_ai.common_tools.exa import ExaToolset
    
    exa_api_key = os.environ.get("EXA_API_KEY")
    
    if exa_api_key:
        # Create Exa toolset with all features
        exa_toolset = ExaToolset(
            api_key=exa_api_key,
            num_results=5,  # Number of search results
            max_characters=1000,  # Max characters per result
            include_search=True,  # Include neural search
            include_find_similar=True,  # Include find similar pages
            include_get_contents=True,  # Include content retrieval
            include_answer=True,  # Include AI answer generation
        )
        
        exa_agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=(
                "You are a research assistant with access to Exa's neural search. "
                "Exa provides AI-powered semantic search and content retrieval."
            ),
            toolsets=[exa_toolset],
        )
        EXA_AVAILABLE = True
    else:
        EXA_AVAILABLE = False
        print("Note: Exa toolset requires EXA_API_KEY environment variable")
        print("Get your API key at: https://exa.ai\n")
except ImportError:
    EXA_AVAILABLE = False
    print("Note: Exa toolset is included in pydantic-ai")


async def example_duckduckgo():
    """Example: Using DuckDuckGo for free web search."""
    if not DUCKDUCKGO_AVAILABLE:
        print("=== Example 1: DuckDuckGo Search (Not Available) ===\n")
        print("Install duckduckgo-search to use this tool")
        print("Command: uv add duckduckgo-search\n")
        return
    
    print("=== Example 1: DuckDuckGo Search ===\n")
    
    try:
        result = await ddg_agent.run(
            "What is PydanticAI and what are its main features?"
        )
        
        print(f"User: What is PydanticAI and what are its main features?")
        print(f"Agent: {result.output}\n")
        print("✓ DuckDuckGo search was used to find current information")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure duckduckgo-search package is installed\n")


async def example_tavily():
    """Example: Using Tavily for LLM-optimized search."""
    if not TAVILY_AVAILABLE:
        print("=== Example 2: Tavily Search (Not Available) ===\n")
        print("Set TAVILY_API_KEY environment variable to use this tool")
        print("Get free API key at: https://tavily.com\n")
        return
    
    print("=== Example 2: Tavily Search ===\n")
    
    try:
        result = await tavily_agent.run(
            "What are the latest developments in AI agents in 2024?"
        )
        
        print(f"User: What are the latest developments in AI agents in 2024?")
        print(f"Agent: {result.output}\n")
        print("✓ Tavily provided LLM-optimized search results")
    except Exception as e:
        print(f"Error: {e}\n")


async def example_exa():
    """Example: Using Exa for neural search."""
    if not EXA_AVAILABLE:
        print("=== Example 3: Exa Neural Search (Not Available) ===\n")
        print("Set EXA_API_KEY environment variable to use this tool")
        print("Get API key at: https://exa.ai\n")
        return
    
    print("=== Example 3: Exa Neural Search ===\n")
    
    try:
        result = await exa_agent.run(
            "Find research papers about agentic AI frameworks"
        )
        
        print(f"User: Find research papers about agentic AI frameworks")
        print(f"Agent: {result.output}\n")
        print("✓ Exa used neural search to find semantically relevant content")
    except Exception as e:
        print(f"Error: {e}\n")


async def example_exa_similar_pages():
    """Example: Using Exa to find similar pages."""
    if not EXA_AVAILABLE:
        print("=== Example 4: Exa Similar Pages (Not Available) ===\n")
        return
    
    print("=== Example 4: Exa Find Similar Pages ===\n")
    
    try:
        result = await exa_agent.run(
            "Find pages similar to https://docs.pydantic.dev/latest/"
        )
        
        print(f"User: Find pages similar to https://docs.pydantic.dev/latest/")
        print(f"Agent: {result.output}\n")
    except Exception as e:
        print(f"Error: {e}\n")


async def example_comparison():
    """Example: Comparing search tools."""
    print("=== Example 5: Search Tool Comparison ===\n")
    
    query = "What is agentic AI?"
    
    # Test each available tool
    print(f"Query: {query}\n")
    print("-" * 80)
    
    if DUCKDUCKGO_AVAILABLE:
        print("\n1. DuckDuckGo (Free)")
        try:
            result = await ddg_agent.run(query)
            print(f"Result: {result.output[:200]}...\n")
        except Exception as e:
            print(f"Error: {e}\n")
    
    if TAVILY_AVAILABLE:
        print("\n2. Tavily (LLM-Optimized)")
        try:
            result = await tavily_agent.run(query)
            print(f"Result: {result.output[:200]}...\n")
        except Exception as e:
            print(f"Error: {e}\n")
    
    if EXA_AVAILABLE:
        print("\n3. Exa (Neural Search)")
        try:
            result = await exa_agent.run(query)
            print(f"Result: {result.output[:200]}...\n")
        except Exception as e:
            print(f"Error: {e}\n")
    
    print("-" * 80)


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("COMMON TOOLS EXAMPLES")
    print("=" * 80 + "\n")
    
    print("Available Common Tools:")
    print("1. DuckDuckGo Search - Free, no API key required")
    print("2. Tavily Search - Paid (free tier), LLM-optimized results")
    print("3. Exa - Neural search, similar pages, AI answers\n")
    
    print("When to Use Each:")
    print("- DuckDuckGo: Quick prototyping, free projects, basic search needs")
    print("- Tavily: Production apps, better quality, LLM-optimized")
    print("- Exa: Semantic/neural search, finding similar content, research\n")
    
    print("=" * 80 + "\n")
    
    await example_duckduckgo()
    print("-" * 80 + "\n")
    
    await example_tavily()
    print("-" * 80 + "\n")
    
    await example_exa()
    print("-" * 80 + "\n")
    
    await example_exa_similar_pages()
    print("-" * 80 + "\n")
    
    await example_comparison()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- Common tools provide ready-to-use search capabilities")
    print("- DuckDuckGo: Best for free, quick prototyping")
    print("- Tavily: Best for production with LLM-optimized results")
    print("- Exa: Best for semantic/neural search and research tasks")
    print("- Choose based on your needs: free vs quality vs features")
    print("\nSetup:")
    print("1. DuckDuckGo: uv add duckduckgo-search")
    print("2. Tavily: Set TAVILY_API_KEY (free tier available)")
    print("3. Exa: Set EXA_API_KEY")
    print("\nCheck Logfire dashboard to see search tool usage!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
