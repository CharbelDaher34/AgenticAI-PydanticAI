"""Lesson 01.2: Database Dependencies - Injecting database access into agents.

This example demonstrates:
- Using the mock database as a dependency
- Querying data through tools
- Clean separation of concerns
- Comprehensive Logfire tracing
"""

import asyncio
import os
import sys
from pathlib import Path

import logfire
from pydantic_ai import Agent, RunContext

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings
from common.database import MockDatabase

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Configure Logfire
logfire.configure(console=False)
logfire.instrument_pydantic_ai()

# Get structured logger
log = get_logger(__name__)

# Create an agent that works with our database
shop_agent = Agent[MockDatabase, str](
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a helpful shopping assistant. "
        "You can help users find products, check availability, "
        "and provide information about their orders."
    ),
)


@shop_agent.tool
async def search_products(ctx: RunContext[MockDatabase], query: str) -> str:
    """Search for products by name or description.
    
    Args:
        ctx: Runtime context with database access
        query: Search query string
    """
    log.info("searching_products", query=query)
    
    products = await ctx.deps.search_products(query)
    
    if not products:
        return f"No products found matching '{query}'"
    
    result = f"Found {len(products)} product(s):\n"
    for product in products:
        stock_status = "In Stock" if product.in_stock else "Out of Stock"
        result += (
            f"- {product.name} (${product.price}) - "
            f"{product.category} - {stock_status}\n"
        )
    
    log.info("products_found", count=len(products))
    return result


@shop_agent.tool
async def get_product_details(ctx: RunContext[MockDatabase], product_id: int) -> str:
    """Get detailed information about a specific product.
    
    Args:
        ctx: Runtime context with database access
        product_id: ID of the product to look up
    """
    log.info("fetching_product", product_id=product_id)
    
    product = await ctx.deps.get_product(product_id)
    
    if not product:
        return f"Product with ID {product_id} not found"
    
    stock_status = "Available" if product.in_stock else "Out of Stock"
    description = product.description or "No description available"
    
    return (
        f"Product: {product.name}\n"
        f"Price: ${product.price}\n"
        f"Category: {product.category}\n"
        f"Status: {stock_status}\n"
        f"Description: {description}"
    )


@shop_agent.tool
async def list_products_by_category(
    ctx: RunContext[MockDatabase], category: str, in_stock_only: bool = True
) -> str:
    """List all products in a specific category.
    
    Args:
        ctx: Runtime context with database access
        category: Product category to filter by
        in_stock_only: Only show products that are in stock
    """
    log.info("listing_products", category=category, in_stock_only=in_stock_only)
    
    products = await ctx.deps.list_products(
        category=category, in_stock_only=in_stock_only
    )
    
    if not products:
        return f"No products found in category '{category}'"
    
    result = f"Products in {category} category ({len(products)} found):\n"
    for product in products:
        result += f"- {product.name} (${product.price})\n"
    
    return result


@shop_agent.tool
async def check_user_orders(ctx: RunContext[MockDatabase], user_id: int) -> str:
    """Check orders for a specific user.
    
    Args:
        ctx: Runtime context with database access
        user_id: ID of the user
    """
    log.info("checking_orders", user_id=user_id)
    
    # Get user info
    user = await ctx.deps.get_user(user_id)
    if not user:
        return f"User with ID {user_id} not found"
    
    # Get user's orders
    orders = await ctx.deps.list_user_orders(user_id)
    
    if not orders:
        return f"No orders found for {user.name}"
    
    result = f"Orders for {user.name}:\n"
    for order in orders:
        product = await ctx.deps.get_product(order.product_id)
        product_name = product.name if product else "Unknown"
        result += (
            f"- Order #{order.id}: {order.quantity}x {product_name} "
            f"({order.status}) - {order.order_date}\n"
        )
    
    log.info("orders_found", count=len(orders))
    return result


async def example_product_search():
    """Search for products."""
    print("=== Example 1: Product Search ===\n")
    
    db = MockDatabase()
    
    result = await shop_agent.run(
        "Can you help me find a laptop?",
        deps=db,
    )
    
    print(f"User: Can you help me find a laptop?")
    print(f"Agent: {result.output}\n")


async def example_product_details():
    """Get detailed product information."""
    print("=== Example 2: Product Details ===\n")
    
    db = MockDatabase()
    
    result = await shop_agent.run(
        "Tell me more about product ID 2",
        deps=db,
    )
    
    print(f"User: Tell me more about product ID 2")
    print(f"Agent: {result.output}\n")


async def example_category_browse():
    """Browse products by category."""
    print("=== Example 3: Browse by Category ===\n")
    
    db = MockDatabase()
    
    result = await shop_agent.run(
        "Show me all electronics that are in stock",
        deps=db,
    )
    
    print(f"User: Show me all electronics that are in stock")
    print(f"Agent: {result.output}\n")


async def example_order_history():
    """Check user's order history."""
    print("=== Example 4: Order History ===\n")
    
    db = MockDatabase()
    
    # Check orders for user ID 1
    result = await shop_agent.run(
        "Can you show me the orders for user ID 1?",
        deps=db,
    )
    
    print(f"User: Can you show me the orders for user ID 1?")
    print(f"Agent: {result.output}\n")


async def example_complex_query():
    """Handle a complex multi-tool query."""
    print("=== Example 5: Complex Multi-Tool Query ===\n")
    
    db = MockDatabase()
    
    result = await shop_agent.run(
        "I'm looking for office furniture that's in stock. "
        "Can you show me what you have and tell me more about the most expensive item?",
        deps=db,
    )
    
    print(f"User: I'm looking for office furniture that's in stock...")
    print(f"Agent: {result.output}\n")


async def main():
    """Run all database dependency examples."""
    print("\n" + "=" * 80)
    print("DATABASE DEPENDENCY INJECTION EXAMPLES")
    print("=" * 80 + "\n")
    
    # await example_product_search()
    # await example_product_details()
    await example_category_browse()
    # await example_order_history()
    # await example_complex_query()
    
    print("=" * 80)
    print("Check Logfire dashboard to see all database queries traced!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
