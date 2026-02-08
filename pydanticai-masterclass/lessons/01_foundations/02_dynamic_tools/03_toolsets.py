"""Lesson 02.3: Toolsets - Managing collections of reusable tools.

This example demonstrates:
- Creating FunctionToolsets
- Combining multiple toolsets
- Filtering toolsets dynamically
- Prefixing toolsets for namespacing
- Adding toolsets at different stages (creation, run, override)
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import FunctionToolset, CombinedToolset

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings
from common.database import MockDatabase

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Get logger from centralized configuration
log = get_logger(__name__)

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()


@dataclass
class AppContext:
    """Application context with database and user info."""
    
    db: MockDatabase
    user_id: int
    enable_analytics: bool = False


# Create toolset #1: Date/Time utilities
# Toolsets group related tools together for reusability
datetime_toolset = FunctionToolset()


@datetime_toolset.tool_plain
def get_current_time() -> str:
    """Get the current time.
    
    Returns:
        Current time formatted as HH:MM:SS
    """
    return datetime.now().strftime("%H:%M:%S")


@datetime_toolset.tool_plain
def get_current_date() -> str:
    """Get the current date.
    
    Returns:
        Current date formatted as YYYY-MM-DD
    """
    return datetime.now().strftime("%Y-%m-%d")


@datetime_toolset.tool_plain
def get_day_of_week() -> str:
    """Get the current day of the week.
    
    Returns:
        Day name (e.g., 'Monday')
    """
    return datetime.now().strftime("%A")


# Create toolset #2: Product operations
product_toolset = FunctionToolset()


@product_toolset.tool
async def search_products(ctx: RunContext[AppContext], query: str) -> str:
    """Search for products by name.
    
    Args:
        ctx: Run context with database access
        query: Search query
    
    Returns:
        List of matching products
    """
    products = await ctx.deps.db.search_products(query)
    
    if not products:
        return f"No products found matching '{query}'"
    
    results = [f"- {p.name} (${p.price})" for p in products]
    return "Found:\n" + "\n".join(results)


@product_toolset.tool
async def get_product_price(ctx: RunContext[AppContext], product_id: int) -> str:
    """Get the price of a specific product.
    
    Args:
        ctx: Run context with database access
        product_id: ID of the product
    
    Returns:
        Product price or error message
    """
    product = await ctx.deps.db.get_product(product_id)
    
    if not product:
        return f"Product {product_id} not found"
    
    return f"${product.price}"


# Create toolset #3: Analytics (only for users with analytics enabled)
analytics_toolset = FunctionToolset()


@analytics_toolset.tool
async def get_popular_products(ctx: RunContext[AppContext]) -> str:
    """Get the most popular products based on orders.
    
    Args:
        ctx: Run context with database access
    
    Returns:
        List of popular products
    """
    # In a real app, this would query order statistics
    # For demo, just return all products sorted by price (simulating popularity)
    products = await ctx.deps.db.list_products()
    products_sorted = sorted(products, key=lambda p: p.price, reverse=True)[:3]
    
    results = [f"- {p.name} (${p.price})" for p in products_sorted]
    return "Top products:\n" + "\n".join(results)


@analytics_toolset.tool
async def get_sales_stats(ctx: RunContext[AppContext]) -> str:
    """Get sales statistics.
    
    Args:
        ctx: Run context with database access
    
    Returns:
        Sales statistics summary
    """
    # Simulate sales stats
    return (
        "Sales Statistics:\n"
        "- Total orders: 150\n"
        "- Revenue: $45,320\n"
        "- Average order value: $302"
    )


# Create a combined toolset from datetime and product toolsets
basic_toolset = CombinedToolset([datetime_toolset, product_toolset])


# Agent with toolsets at construction time
agent_with_toolsets = Agent[AppContext, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a helpful assistant with access to product information.",
    toolsets=[basic_toolset],  # Add toolsets at construction
)


# Agent without toolsets (will add them at runtime)
flexible_agent = Agent[AppContext, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a flexible assistant. Available tools depend on context.",
)


async def example_basic_toolset():
    """Example: Using toolsets added at agent creation."""
    print("=== Example 1: Basic Toolset Usage ===\n")
    
    ctx = AppContext(db=MockDatabase(), user_id=1)
    
    result = await agent_with_toolsets.run(
        "What time is it, and do you have any laptops?",
        deps=ctx,
    )
    
    print(f"User: What time is it, and do you have any laptops?")
    print(f"Agent: {result.output}\n")


async def example_runtime_toolsets():
    """Example: Adding toolsets at runtime."""
    print("=== Example 2: Runtime Toolset Addition ===\n")
    
    ctx = AppContext(db=MockDatabase(), user_id=1)
    
    # Add additional toolsets at runtime
    result = await flexible_agent.run(
        "What day is it today?",
        deps=ctx,
        toolsets=[datetime_toolset],  # Add toolset for this run only
    )
    
    print(f"User: What day is it today?")
    print(f"Agent: {result.output}\n")


async def example_filtered_toolset():
    """Example: Filtering toolsets based on context."""
    print("=== Example 3: Filtered Toolsets ===\n")
    
    # Create a filtered version of analytics toolset
    # Only include analytics tools if user has analytics enabled
    def should_include_analytics(ctx: RunContext[AppContext], tool_def):
        return ctx.deps.enable_analytics
    
    filtered_analytics = analytics_toolset.filtered(should_include_analytics)
    
    # User WITHOUT analytics
    ctx_no_analytics = AppContext(
        db=MockDatabase(), user_id=1, enable_analytics=False
    )
    
    result = await flexible_agent.run(
        "Show me sales statistics",
        deps=ctx_no_analytics,
        toolsets=[basic_toolset, filtered_analytics],
    )
    
    print(f"User (no analytics): Show me sales statistics")
    print(f"Agent: {result.output}\n")
    
    # User WITH analytics
    ctx_with_analytics = AppContext(
        db=MockDatabase(), user_id=1, enable_analytics=True
    )
    
    result = await flexible_agent.run(
        "Show me sales statistics",
        deps=ctx_with_analytics,
        toolsets=[basic_toolset, filtered_analytics],
    )
    
    print(f"User (with analytics): Show me sales statistics")
    print(f"Agent: {result.output}\n")


async def example_prefixed_toolset():
    """Example: Using prefixed toolsets for namespacing."""
    print("=== Example 4: Prefixed Toolsets ===\n")
    
    # Create prefixed versions of toolsets
    # This is useful when you have tools with similar names from different sources
    time_toolset = datetime_toolset.prefixed("time")
    prod_toolset = product_toolset.prefixed("products")
    
    ctx = AppContext(db=MockDatabase(), user_id=1)
    
    result = await flexible_agent.run(
        "What time is it?",
        deps=ctx,
        toolsets=[time_toolset, prod_toolset],
    )
    
    print(f"User: What time is it?")
    print(f"Agent: {result.output}")
    print(f"Note: Tools are namespaced (e.g., 'time_get_current_time')\n")


async def example_override_toolsets():
    """Example: Overriding toolsets with context manager."""
    print("=== Example 5: Override Toolsets ===\n")
    
    ctx = AppContext(db=MockDatabase(), user_id=1)
    
    # Temporarily override toolsets for a block of code
    with agent_with_toolsets.override(toolsets=[datetime_toolset]):
        result = await agent_with_toolsets.run(
            "What's the current date?",
            deps=ctx,
        )
        
        print(f"User (with override): What's the current date?")
        print(f"Agent: {result.output}")
        print(f"Note: Only datetime tools available in this context\n")


async def example_combined_toolsets():
    """Example: Combining multiple toolsets."""
    print("=== Example 6: Combined Toolsets ===\n")
    
    # Combine all three toolsets
    all_toolsets = CombinedToolset([
        datetime_toolset,
        product_toolset,
        analytics_toolset,
    ])
    
    ctx = AppContext(db=MockDatabase(), user_id=1, enable_analytics=True)
    
    result = await flexible_agent.run(
        "What are today's top products and what time is it?",
        deps=ctx,
        toolsets=[all_toolsets],
    )
    
    print(f"User: What are today's top products and what time is it?")
    print(f"Agent: {result.output}\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("TOOLSETS EXAMPLES")
    print("=" * 80 + "\n")
    
    print("Key Concepts:")
    print("1. FunctionToolset - Group related tools for reusability")
    print("2. CombinedToolset - Merge multiple toolsets together")
    print("3. filtered() - Dynamically filter tools based on context")
    print("4. prefixed() - Add namespace prefix to avoid name collisions")
    print("5. Toolsets can be added at creation, runtime, or via override\n")
    
    print("=" * 80 + "\n")
    
    await example_basic_toolset()
    print("-" * 80 + "\n")
    
    await example_runtime_toolsets()
    print("-" * 80 + "\n")
    
    await example_filtered_toolset()
    print("-" * 80 + "\n")
    
    await example_prefixed_toolset()
    print("-" * 80 + "\n")
    
    await example_override_toolsets()
    print("-" * 80 + "\n")
    
    await example_combined_toolsets()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- Toolsets organize tools into reusable collections")
    print("- CombinedToolset merges multiple toolsets")
    print("- filtered() enables dynamic tool availability")
    print("- prefixed() prevents tool name conflicts")
    print("- Toolsets promote modularity and code reuse")
    print("\nCheck Logfire dashboard to see toolset operations!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
