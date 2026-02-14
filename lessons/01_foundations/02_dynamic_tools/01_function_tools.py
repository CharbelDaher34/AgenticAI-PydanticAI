"""Lesson 02.1: Function Tools - Basic tool registration and usage.

This example demonstrates:
- Tool registration with @agent.tool and @agent.tool_plain decorators
- RunContext usage for accessing dependencies
- Different tool registration methods
- Tool with and without context
- Realistic database lookup scenarios
"""

import asyncio
import os
import random
import sys
from pathlib import Path

import logfire
from pydantic_ai import Agent, RunContext

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings
from common.database import MockDatabase, Product

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Get logger from centralized configuration
log = get_logger(__name__)

# Configure Logfire
logfire.configure(console=False)
logfire.instrument_pydantic_ai()


# Agent with dependency injection for database access
product_agent = Agent[MockDatabase, str](
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a product information assistant. Use the available tools to help users "
        "find products and get information about them. Be concise but informative."
    ),
)


# Tool with context - uses RunContext to access dependencies
# This is the STANDARD pattern - most tools need access to dependencies
@product_agent.tool
async def search_products(ctx: RunContext[MockDatabase], query: str) -> str:
    """Search for products by name or description.
    
    Args:
        ctx: Run context providing access to the database
        query: Search query to match against product names and descriptions
    
    Returns:
        Formatted string with search results or error message
    """
    # Access the database through ctx.deps
    products = await ctx.deps.search_products(query)
    
    if not products:
        return f"No products found matching '{query}'"
    
    # Format results for the model
    results = []
    for product in products:
        status = "In stock" if product.in_stock else "Out of stock"
        results.append(
            f"- {product.name} (${product.price}) - {product.category} - {status}"
        )
    
    return "Found products:\n" + "\n".join(results)


@product_agent.tool
async def get_product_details(ctx: RunContext[MockDatabase], product_id: int) -> str:
    """Get detailed information about a specific product.
    
    Args:
        ctx: Run context providing access to the database
        product_id: ID of the product to retrieve
    
    Returns:
        Detailed product information or error message
    """
    product = await ctx.deps.get_product(product_id)
    
    if not product:
        return f"Product with ID {product_id} not found"
    
    status = "Available" if product.in_stock else "Out of stock"
    description = product.description or "No description available"
    
    return (
        f"Product: {product.name}\n"
        f"Price: ${product.price}\n"
        f"Category: {product.category}\n"
        f"Status: {status}\n"
        f"Description: {description}"
    )


@product_agent.tool
async def list_categories(ctx: RunContext[MockDatabase]) -> str:
    """List all available product categories.
    
    Args:
        ctx: Run context providing access to the database
    
    Returns:
        List of unique product categories
    """
    products = await ctx.deps.list_products()
    
    # Extract unique categories
    categories = sorted(set(p.category for p in products))
    
    return "Available categories:\n" + "\n".join(f"- {cat}" for cat in categories)


# Tool WITHOUT context - uses @agent.tool_plain
# Use this when the tool doesn't need access to dependencies or context
# These tools are simpler but more limited
@product_agent.tool_plain
def roll_dice() -> str:
    """Roll a six-sided dice for random selection.
    
    Returns:
        Result of the dice roll (1-6)
    """
    # This tool doesn't need any context - it's completely self-contained
    result = random.randint(1, 6)
    return f"You rolled a {result}"


@product_agent.tool_plain
def calculate_discount(price: float, discount_percent: float) -> str:
    """Calculate the discounted price.
    
    Args:
        price: Original price
        discount_percent: Discount percentage (e.g., 20 for 20% off)
    
    Returns:
        Formatted string with discounted price
    """
    # Pure calculation - no need for context
    if discount_percent < 0 or discount_percent > 100:
        return "Invalid discount percentage. Must be between 0 and 100."
    
    discount_amount = price * (discount_percent / 100)
    final_price = price - discount_amount
    
    return (
        f"Original price: ${price:.2f}\n"
        f"Discount: {discount_percent}% (${discount_amount:.2f})\n"
        f"Final price: ${final_price:.2f}"
    )


async def example_basic_search():
    """Example: Search for products using the agent."""
    print("=== Example 1: Basic Product Search ===\n")
    
    db = MockDatabase()
    
    result = await product_agent.run(
        "Find me a laptop",
        deps=db,
    )
    
    print(f"User: Find me a laptop")
    print(f"Agent: {result.output}\n")


async def example_product_details():
    """Example: Get detailed information about a product."""
    print("=== Example 2: Product Details ===\n")
    
    db = MockDatabase()
    
    result = await product_agent.run(
        "Tell me about product ID 1",
        deps=db,
    )
    
    print(f"User: Tell me about product ID 1")
    print(f"Agent: {result.output}\n")


async def example_categories():
    """Example: List available categories."""
    print("=== Example 3: List Categories ===\n")
    
    db = MockDatabase()
    
    result = await product_agent.run(
        "What categories of products do you have?",
        deps=db,
    )
    
    print(f"User: What categories of products do you have?")
    print(f"Agent: {result.output}\n")


async def example_plain_tools():
    """Example: Using tools without context."""
    print("=== Example 4: Plain Tools (No Context) ===\n")
    
    db = MockDatabase()
    
    # The agent can use both context-aware and plain tools
    result = await product_agent.run(
        "If a laptop costs $999.99, what would it cost with a 15% discount?",
        deps=db,
    )
    
    print(f"User: If a laptop costs $999.99, what would it cost with a 15% discount?")
    print(f"Agent: {result.output}\n")


async def example_complex_query():
    """Example: Complex query using multiple tools."""
    print("=== Example 5: Complex Query (Multiple Tools) ===\n")
    
    db = MockDatabase()
    
    result = await product_agent.run(
        "Search for furniture, then tell me the details of the cheapest item you found",
        deps=db,
    )
    
    print(f"User: Search for furniture, then tell me the details of the cheapest item")
    print(f"Agent: {result.output}\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("FUNCTION TOOLS EXAMPLES")
    print("=" * 80 + "\n")
    
    print("Key Concepts:")
    print("1. @agent.tool - For tools that need RunContext (access to dependencies)")
    print("2. @agent.tool_plain - For self-contained tools without context")
    print("3. RunContext[T] - Type-safe access to dependencies")
    print("4. Tools are automatically discovered and called by the model\n")
    
    print("=" * 80 + "\n")
    
    await example_basic_search()
    print("-" * 80 + "\n")
    
    await example_product_details()
    print("-" * 80 + "\n")
    
    await example_categories()
    print("-" * 80 + "\n")
    
    await example_plain_tools()
    print("-" * 80 + "\n")
    
    await example_complex_query()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- Use @agent.tool when you need access to dependencies (database, APIs, etc.)")
    print("- Use @agent.tool_plain for pure functions that don't need context")
    print("- The model automatically selects and calls the right tools")
    print("- Tools should have clear docstrings - the model uses them to understand usage")
    print("\nCheck Logfire dashboard to see tool calls and execution traces!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
