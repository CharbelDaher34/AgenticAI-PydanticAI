"""Lesson 02.2: Advanced Tool Features - ToolReturn, prepare methods, retries, timeouts.

This example demonstrates:
- ToolReturn with metadata, content, and return_value
- Tool-to-tool communication via ToolReturn
- Dynamic tool preparation with prepare methods
- Error handling and retries with ModelRetry
- Tool timeouts
- Accessing tool metadata from results
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import logfire
from pydantic_ai import Agent, ModelRetry, RunContext, Tool, ToolDefinition, ToolReturn
from pydantic_ai.messages import ModelMessage, ToolReturnPart

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
    log.info("Checking status for user: %s (ID: %s)", username=user.username, user_id=user.user_id)
    
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
        log.info("Including admin tool for user: %s", username=ctx.deps.username)
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
    log.info("Executing admin action: %s", action=action)
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
    log.info("Performing premium analysis on data: %s", data=data)
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
    log.info("Fetching external data from: %s", endpoint=endpoint)
    
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
    log.info("Starting slow computation with complexity: %s", complexity=complexity)
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
    log.info("Collecting server metrics...")
    return {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 34.5,
        "active_users": 127,
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# NEW: Advanced ToolReturn with Content and Tool-to-Tool Communication
# ============================================================================

# Agent for demonstrating tool-to-tool communication
communication_agent = Agent[str, str](
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a data analysis assistant. You can fetch data, analyze it, "
        "and generate comprehensive reports. Use the available tools to complete tasks."
    ),
)


@communication_agent.tool
async def fetch_sales_data(ctx: RunContext[str], region: str) -> ToolReturn:
    """Fetch sales data for a specific region.
    
    This demonstrates ToolReturn with all three components:
    - return_value: The structured data (what gets serialized)
    - content: Additional context for the model (rich information)
    - metadata: Application-level data (not sent to model)
    
    Args:
        ctx: Run context
        region: Region to fetch data for (e.g., 'north', 'south', 'east', 'west')
    
    Returns:
        ToolReturn with sales data, analysis context, and metadata
    """
    log.info("Fetching sales data for region: %s", region=region)
    
    # Simulate fetching data
    sales_data = {
        "region": region,
        "total_sales": 125000 + hash(region) % 50000,
        "transactions": 450 + hash(region) % 200,
        "top_products": ["Product A", "Product B", "Product C"],
        "growth_rate": 12.5 + (hash(region) % 10),
    }
    
    # Return value is what the tool officially returns
    return_value = json.dumps(sales_data, indent=2)
    
    # Content provides additional context to the model
    # This is sent as a separate user message to give the model more context
    content = [
        f"📊 Sales Data for {region.upper()} Region",
        "-" * 50,
        f"Total Sales: ${sales_data['total_sales']:,}",
        f"Transactions: {sales_data['transactions']}",
        f"Growth Rate: {sales_data['growth_rate']:.1f}%",
        "",
        "Key Insights:",
        f"- Average transaction value: ${sales_data['total_sales'] / sales_data['transactions']:.2f}",
        f"- Top performing products: {', '.join(sales_data['top_products'][:2])}",
        f"- {'Strong' if sales_data['growth_rate'] > 15 else 'Moderate'} growth trajectory",
        "",
        "This data can be used for further analysis or report generation.",
    ]
    
    # Metadata is for application use only (not sent to the model)
    metadata = {
        "data_source": "sales_database",
        "fetch_timestamp": datetime.now().isoformat(),
        "region": region,
        "cache_key": f"sales_{region}_{datetime.now().date()}",
        "query_cost": 0.05,  # Simulated cost
    }
    
    return ToolReturn(
        return_value=return_value,
        content=content,
        metadata=metadata,
    )


@communication_agent.tool
async def analyze_sales_trends(ctx: RunContext[str], sales_data_json: str) -> ToolReturn:
    """Analyze sales data and identify trends.
    
    This tool can work with data from fetch_sales_data, demonstrating
    tool-to-tool communication where the model uses one tool's output
    as input to another tool.
    
    Args:
        ctx: Run context
        sales_data_json: JSON string of sales data (from fetch_sales_data)
    
    Returns:
        ToolReturn with analysis results and recommendations
    """
    log.info("Analyzing sales trends...")
    
    # Parse the input data
    try:
        data = json.loads(sales_data_json)
    except json.JSONDecodeError:
        return ToolReturn(
            return_value="Error: Invalid JSON data provided",
            content=["❌ Failed to parse sales data. Please provide valid JSON."],
            metadata={"error": "json_decode_error"},
        )
    
    # Perform analysis
    region = data.get("region", "unknown")
    total_sales = data.get("total_sales", 0)
    growth_rate = data.get("growth_rate", 0)
    transactions = data.get("transactions", 0)
    
    # Calculate additional metrics
    avg_transaction = total_sales / transactions if transactions > 0 else 0
    
    # Generate insights
    insights = []
    if growth_rate > 15:
        insights.append("Strong growth - consider expanding operations")
    elif growth_rate > 10:
        insights.append("Healthy growth - maintain current strategies")
    else:
        insights.append("Moderate growth - explore new opportunities")
    
    if avg_transaction > 300:
        insights.append("High-value transactions - focus on customer retention")
    else:
        insights.append("Increase average transaction value through upselling")
    
    analysis_result = {
        "region": region,
        "performance_score": min(100, int(growth_rate * 5 + avg_transaction / 10)),
        "insights": insights,
        "recommendations": [
            "Increase marketing budget" if growth_rate < 12 else "Optimize operations",
            "Launch loyalty program" if avg_transaction < 300 else "Premium tier program",
        ],
    }
    
    # Rich content for the model
    content = [
        f"📈 Sales Analysis for {region.upper()} Region",
        "=" * 50,
        f"Performance Score: {analysis_result['performance_score']}/100",
        "",
        "Key Insights:",
    ]
    for insight in insights:
        content.append(f"  • {insight}")
    
    content.extend([
        "",
        "Recommendations:",
    ])
    for rec in analysis_result["recommendations"]:
        content.append(f"  ✓ {rec}")
    
    # Metadata for application tracking
    metadata = {
        "analysis_timestamp": datetime.now().isoformat(),
        "analyzed_region": region,
        "performance_score": analysis_result["performance_score"],
        "model_version": "v1.0",
    }
    
    return ToolReturn(
        return_value=json.dumps(analysis_result, indent=2),
        content=content,
        metadata=metadata,
    )


@communication_agent.tool
async def generate_executive_summary(
    ctx: RunContext[str], 
    analysis_json: str
) -> ToolReturn:
    """Generate an executive summary from analysis data.
    
    This is the third tool in the chain, demonstrating multi-step
    tool communication: fetch -> analyze -> summarize
    
    Args:
        ctx: Run context
        analysis_json: JSON string of analysis data (from analyze_sales_trends)
    
    Returns:
        ToolReturn with executive summary
    """
    log.info("Generating executive summary...")
    
    try:
        analysis = json.loads(analysis_json)
    except json.JSONDecodeError:
        return ToolReturn(
            return_value="Error: Invalid analysis data",
            content=["❌ Failed to parse analysis data."],
            metadata={"error": "json_decode_error"},
        )
    
    region = analysis.get("region", "unknown")
    score = analysis.get("performance_score", 0)
    insights = analysis.get("insights", [])
    recommendations = analysis.get("recommendations", [])
    
    # Generate summary
    summary_lines = [
        f"EXECUTIVE SUMMARY - {region.upper()} REGION",
        "=" * 60,
        "",
        f"Overall Performance: {score}/100 - {'Excellent' if score > 80 else 'Good' if score > 60 else 'Needs Improvement'}",
        "",
        "Strategic Insights:",
    ]
    
    for i, insight in enumerate(insights, 1):
        summary_lines.append(f"{i}. {insight}")
    
    summary_lines.extend([
        "",
        "Action Items:",
    ])
    
    for i, rec in enumerate(recommendations, 1):
        summary_lines.append(f"{i}. {rec}")
    
    summary_lines.extend([
        "",
        "Next Steps:",
        "- Review quarterly targets",
        "- Schedule strategy meeting",
        "- Allocate resources accordingly",
    ])
    
    summary_text = "\n".join(summary_lines)
    
    return ToolReturn(
        return_value=summary_text,
        content=[
            "📋 Executive Summary Generated",
            "The summary is ready for presentation to stakeholders.",
            f"Performance rating: {'⭐' * (score // 20)}",
        ],
        metadata={
            "summary_timestamp": datetime.now().isoformat(),
            "region_analyzed": region,
            "summary_length": len(summary_text),
            "format": "text",
        },
    )


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


async def example_tool_return_with_content():
    """Example: ToolReturn with return_value, content, and metadata."""
    print("=== Example 6: ToolReturn with Content ===\n")
    
    result = await communication_agent.run(
        "Fetch sales data for the north region",
        deps="analysis_session",
    )
    
    print(f"User: Fetch sales data for the north region")
    print(f"Agent: {result.output}\n")
    
    # Access tool metadata from message history
    print("📦 Accessing Tool Metadata from Result:")
    print("-" * 50)
    
    for message in result.all_messages():
        if isinstance(message, ModelMessage):
            for part in message.parts:
                if isinstance(part, ToolReturnPart):
                    if part.tool_name == "fetch_sales_data" and part.metadata:
                        print(f"Tool: {part.tool_name}")
                        print(f"Metadata: {json.dumps(part.metadata, indent=2)}")
                        print(f"Timestamp: {part.metadata.get('fetch_timestamp')}")
                        print(f"Query Cost: ${part.metadata.get('query_cost')}")
                        print()


async def example_tool_to_tool_communication():
    """Example: Tools communicating with each other."""
    print("=== Example 7: Tool-to-Tool Communication ===\n")
    
    result = await communication_agent.run(
        "Fetch sales data for the east region and analyze the trends",
        deps="analysis_session",
    )
    
    print(f"User: Fetch sales data for the east region and analyze the trends")
    print(f"Agent: {result.output}\n")
    
    # Show tool call sequence
    print("🔄 Tool Call Sequence:")
    print("-" * 50)
    
    tool_calls = []
    for message in result.all_messages():
        if isinstance(message, ModelMessage):
            for part in message.parts:
                if isinstance(part, ToolReturnPart):
                    tool_calls.append({
                        "tool": part.tool_name,
                        "has_metadata": part.metadata is not None,
                        "has_content": len(part.content) > 1 if hasattr(part, 'content') else False,
                    })
    
    for i, call in enumerate(tool_calls, 1):
        print(f"{i}. {call['tool']}")
        print(f"   - Metadata: {'✓' if call['has_metadata'] else '✗'}")
        print(f"   - Rich Content: {'✓' if call['has_content'] else '✗'}")
    print()


async def example_multi_step_analysis():
    """Example: Multi-step analysis with full pipeline."""
    print("=== Example 8: Multi-Step Analysis Pipeline ===\n")
    
    result = await communication_agent.run(
        "Get sales data for the west region, analyze it, and create an executive summary",
        deps="analysis_session",
    )
    
    print(f"User: Get sales data for the west region, analyze it, and create an executive summary")
    print(f"Agent:\n{result.output}\n")
    
    # Extract all metadata from the pipeline
    print("📊 Pipeline Metadata Summary:")
    print("-" * 50)
    
    all_metadata = []
    for message in result.all_messages():
        if isinstance(message, ModelMessage):
            for part in message.parts:
                if isinstance(part, ToolReturnPart) and part.metadata:
                    all_metadata.append({
                        "tool": part.tool_name,
                        "metadata": part.metadata,
                    })
    
    for item in all_metadata:
        print(f"\n{item['tool']}:")
        for key, value in item['metadata'].items():
            print(f"  • {key}: {value}")
    print()


async def example_accessing_tool_returns():
    """Example: Accessing tool return data from results."""
    print("=== Example 9: Accessing Tool Return Data ===\n")
    
    result = await communication_agent.run(
        "Fetch and analyze sales data for the south region",
        deps="analysis_session",
    )
    
    print(f"User: Fetch and analyze sales data for the south region")
    print(f"Agent: {result.output}\n")
    
    # Demonstrate accessing different parts of ToolReturn
    print("🔍 Analyzing ToolReturn Components:")
    print("-" * 50)
    
    for message in result.all_messages():
        if isinstance(message, ModelMessage):
            for part in message.parts:
                if isinstance(part, ToolReturnPart):
                    print(f"\nTool: {part.tool_name}")
                    print(f"├─ Return Value Type: {type(part.content[0] if part.content else None).__name__}")
                    print(f"├─ Content Parts: {len(part.content)}")
                    print(f"└─ Has Metadata: {part.metadata is not None}")
                    
                    if part.metadata:
                        print(f"\n   Metadata Keys: {', '.join(part.metadata.keys())}")
    print()


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("ADVANCED TOOL FEATURES")
    print("=" * 80 + "\n")
    
    print("Key Concepts:")
    print("1. ToolReturn - Return values with metadata and multi-modal content")
    print("2. Tool-to-tool communication via ToolReturn")
    print("3. prepare methods - Dynamically include/exclude tools per run")
    print("4. ModelRetry - Signal transient errors for automatic retry")
    print("5. Timeouts - Prevent tools from hanging")
    print("6. Accessing tool metadata from results\n")
    
    print("=" * 80 + "\n")
    
    # Basic examples
    await example_metadata()
    print("-" * 80 + "\n")
    
    await example_dynamic_tools_admin()
    print("-" * 80 + "\n")
    
    await example_dynamic_tools_regular()
    print("-" * 80 + "\n")
    
    await example_premium_tools()
    print("-" * 80 + "\n")
    
    await example_structured_output()
    print("-" * 80 + "\n")
    
    # Advanced ToolReturn examples
    await example_tool_return_with_content()
    print("-" * 80 + "\n")
    
    await example_tool_to_tool_communication()
    print("-" * 80 + "\n")
    
    await example_multi_step_analysis()
    print("-" * 80 + "\n")
    
    await example_accessing_tool_returns()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- ToolReturn has 3 components: return_value, content, metadata")
    print("- return_value: Official tool output (sent to model)")
    print("- content: Rich context for the model (separate user message)")
    print("- metadata: Application-only data (NOT sent to model)")
    print("- Tools can communicate by passing data through the model")
    print("- Access metadata via result.all_messages() and ToolReturnPart")
    print("- prepare methods enable dynamic, permission-based tool access")
    print("\nCheck Logfire dashboard to see tool execution details!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
