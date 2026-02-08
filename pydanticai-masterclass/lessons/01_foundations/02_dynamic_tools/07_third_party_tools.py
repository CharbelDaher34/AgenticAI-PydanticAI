"""Lesson 02.7: Third-Party Tools - LangChain and ACI.dev integrations.

This example demonstrates:
- Converting LangChain tools to PydanticAI
- Using LangChain toolkits
- ACI.dev tool integration
- When to use third-party tool ecosystems
- Best practices for integration
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
logfire.configure()
logfire.instrument_pydantic_ai()


# Example 1: LangChain Tool Integration
# LangChain has a large ecosystem of tools that can be used with PydanticAI
try:
    from pydantic_ai.ext.langchain import tool_from_langchain, LangChainToolset
    from langchain_community.tools import DuckDuckGoSearchRun
    
    # Create a LangChain tool
    langchain_search = DuckDuckGoSearchRun()
    
    # Convert to PydanticAI tool
    pydantic_search_tool = tool_from_langchain(langchain_search)
    
    # Create agent with converted tool
    langchain_agent = Agent(
        "openai:gpt-4o-mini",
        system_prompt="You are a research assistant with access to web search via LangChain.",
        tools=[pydantic_search_tool],
    )
    
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    print(f"Note: LangChain integration requires additional packages")
    print("Install with: uv add langchain-community duckduckgo-search")
    print(f"Error: {e}\n")


# Example 2: LangChain Toolkit Integration
# Toolkits are collections of related tools
try:
    from pydantic_ai.ext.langchain import LangChainToolset
    # from langchain_community.agent_toolkits import FileManagementToolkit
    
    # Note: This is a conceptual example - actual toolkit setup may require more config
    # toolkit = FileManagementToolkit(root_dir="/tmp")
    # file_toolset = LangChainToolset(toolkit.get_tools())
    
    # toolkit_agent = Agent(
    #     "openai:gpt-4o-mini",
    #     toolsets=[file_toolset],
    # )
    
    TOOLKIT_AVAILABLE = False  # Disabled for demo
except ImportError:
    TOOLKIT_AVAILABLE = False


# Example 3: ACI.dev Integration (API-based third-party tools)
try:
    from pydantic_ai.ext.aci import tool_from_aci, ACIToolset
    
    # Check if ACI credentials are available
    aci_account_id = os.environ.get("ACI_ACCOUNT_ID")
    aci_api_key = os.environ.get("ACI_API_KEY")
    
    if aci_account_id and aci_api_key:
        # Create a single ACI tool
        # github_tool = tool_from_aci(
        #     tool_name="github_search",
        #     linked_account_owner_id=aci_account_id,
        # )
        
        # Or create a toolset with multiple ACI tools
        # aci_toolset = ACIToolset(
        #     tools=["github_search", "notion_search"],
        #     linked_account_owner_id=aci_account_id,
        # )
        
        ACI_AVAILABLE = False  # Disabled for demo - requires ACI setup
    else:
        ACI_AVAILABLE = False
        print("Note: ACI.dev integration requires ACI_ACCOUNT_ID and ACI_API_KEY")
        print("Sign up at: https://aci.dev\n")
except ImportError:
    ACI_AVAILABLE = False


async def example_langchain_tool():
    """Example: Using a converted LangChain tool."""
    if not LANGCHAIN_AVAILABLE:
        print("=== Example 1: LangChain Tool (Not Available) ===\n")
        print("Install LangChain to use this example:")
        print("uv add langchain-community duckduckgo-search\n")
        return
    
    print("=== Example 1: LangChain Tool Integration ===\n")
    
    try:
        result = await langchain_agent.run(
            "What is the latest version of Python?"
        )
        
        print(f"User: What is the latest version of Python?")
        print(f"Agent: {result.output}\n")
        print("✓ Used LangChain's DuckDuckGo tool via PydanticAI")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure langchain-community and duckduckgo-search are installed\n")


async def example_langchain_toolkit():
    """Example: Using a LangChain toolkit."""
    if not TOOLKIT_AVAILABLE:
        print("=== Example 2: LangChain Toolkit (Not Available) ===\n")
        print("This is a conceptual example showing toolkit integration")
        print("\nPattern:")
        print("```python")
        print("from langchain_community.agent_toolkits import FileManagementToolkit")
        print("from pydantic_ai.ext.langchain import LangChainToolset")
        print("")
        print("toolkit = FileManagementToolkit(root_dir='/tmp')")
        print("file_toolset = LangChainToolset(toolkit.get_tools())")
        print("")
        print("agent = Agent(")
        print("    'openai:gpt-4o-mini',")
        print("    toolsets=[file_toolset],")
        print(")")
        print("```\n")
        return
    
    print("=== Example 2: LangChain Toolkit ===\n")
    # Toolkit example would go here if enabled


async def example_aci_tools():
    """Example: Using ACI.dev tools."""
    if not ACI_AVAILABLE:
        print("=== Example 3: ACI.dev Integration (Not Available) ===\n")
        print("ACI.dev provides API-based access to third-party services")
        print("\nSupported services:")
        print("- GitHub (issues, PRs, search)")
        print("- Notion (pages, databases)")
        print("- Slack (messages, channels)")
        print("- Google Drive (files, folders)")
        print("- And many more...")
        print("\nSetup:")
        print("1. Sign up at https://aci.dev")
        print("2. Set ACI_ACCOUNT_ID and ACI_API_KEY environment variables")
        print("\nPattern:")
        print("```python")
        print("from pydantic_ai.ext.aci import tool_from_aci, ACIToolset")
        print("")
        print("# Single tool")
        print("github_tool = tool_from_aci(")
        print("    tool_name='github_search',")
        print("    linked_account_owner_id=account_id,")
        print(")")
        print("")
        print("# Multiple tools as toolset")
        print("aci_toolset = ACIToolset(")
        print("    tools=['github_search', 'notion_search'],")
        print("    linked_account_owner_id=account_id,")
        print(")")
        print("```\n")
        return
    
    print("=== Example 3: ACI.dev Integration ===\n")
    # ACI example would go here if enabled


async def example_when_to_use():
    """Example: When to use third-party tool ecosystems."""
    print("=== Example 4: When to Use Third-Party Tools ===\n")
    
    print("Use LangChain Tools When:")
    print("- You need access to LangChain's extensive tool ecosystem")
    print("- You're migrating from LangChain to PydanticAI")
    print("- The tool you need already exists in LangChain")
    print("- You want to use LangChain's community tools\n")
    
    print("Use ACI.dev Tools When:")
    print("- You need API-based access to third-party services")
    print("- You want managed OAuth/authentication")
    print("- You need enterprise-grade tool integrations")
    print("- You want to avoid managing API keys for each service\n")
    
    print("Use Native PydanticAI Tools When:")
    print("- You need maximum performance and type safety")
    print("- You want full control over tool behavior")
    print("- The tool is simple enough to implement yourself")
    print("- You need deep integration with PydanticAI features\n")


async def example_best_practices():
    """Example: Best practices for third-party tool integration."""
    print("=== Example 5: Integration Best Practices ===\n")
    
    print("1. Wrap Third-Party Tools:")
    print("   - Add error handling around third-party calls")
    print("   - Validate inputs before passing to third-party tools")
    print("   - Transform outputs to match your schema")
    print("")
    print("2. Handle Failures Gracefully:")
    print("   - Third-party APIs may be down or rate-limited")
    print("   - Provide fallback behavior when possible")
    print("   - Use ModelRetry for transient failures")
    print("")
    print("3. Monitor Performance:")
    print("   - Third-party tools add latency")
    print("   - Use Logfire to track tool execution time")
    print("   - Consider caching for frequently accessed data")
    print("")
    print("4. Security Considerations:")
    print("   - Validate all inputs from third-party tools")
    print("   - Be cautious with tools that execute code")
    print("   - Use approval workflows for sensitive operations")
    print("   - Keep API keys secure and rotate regularly")
    print("")
    print("5. Testing:")
    print("   - Mock third-party tools in tests")
    print("   - Test error handling paths")
    print("   - Validate tool output schemas")
    print("   - Test rate limiting behavior\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("THIRD-PARTY TOOLS EXAMPLES")
    print("=" * 80 + "\n")
    
    print("Third-Party Ecosystems:")
    print("1. LangChain - Large ecosystem of community tools")
    print("2. ACI.dev - Managed API integrations with OAuth")
    print("3. MCP Servers - Model Context Protocol integrations\n")
    
    print("=" * 80 + "\n")
    
    await example_langchain_tool()
    print("-" * 80 + "\n")
    
    await example_langchain_toolkit()
    print("-" * 80 + "\n")
    
    await example_aci_tools()
    print("-" * 80 + "\n")
    
    await example_when_to_use()
    print("-" * 80 + "\n")
    
    await example_best_practices()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- Third-party tools extend PydanticAI with existing ecosystems")
    print("- LangChain: Large tool ecosystem, easy migration path")
    print("- ACI.dev: Managed API integrations, enterprise features")
    print("- Always wrap third-party tools with error handling")
    print("- Choose based on needs: ecosystem size, management, control")
    print("\nSetup:")
    print("1. LangChain: uv add langchain-community")
    print("2. ACI.dev: Set ACI_ACCOUNT_ID and ACI_API_KEY")
    print("\nNote: These examples show integration patterns.")
    print("Install required packages to test functionality.")
    print("\nCheck Logfire dashboard to see third-party tool integration!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
