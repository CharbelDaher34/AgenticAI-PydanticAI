"""Lesson 01.3: Complex Dependencies - Using dataclasses and multiple deps.

This example demonstrates:
- Using dataclasses as dependencies
- Combining multiple services/dependencies
- Structured dependency types
- Real-world patterns
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
class AppContext:
    """Application context with multiple dependencies.
    
    This pattern allows you to inject multiple services/dependencies
    into your agent through a single context object.
    """
    
    database: MockDatabase
    current_user_id: int
    current_time: datetime
    is_admin: bool = False
    session_id: str = "unknown"


# Create agent with complex dependencies
customer_service_agent = Agent[AppContext, str](
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a customer service agent. "
        "You have access to the database, current user context, and time information. "
        "Provide helpful and personalized assistance."
    ),
)


@customer_service_agent.tool
async def get_my_info(ctx: RunContext[AppContext]) -> str:
    """Get information about the current user."""
    log.info("getting_user_info", user_id=ctx.deps.current_user_id, is_admin=ctx.deps.is_admin)
    user = await ctx.deps.database.get_user(ctx.deps.current_user_id)
    
    if not user:
        log.warning("user_not_found", user_id=ctx.deps.current_user_id)
        return "User information not found"
    
    admin_status = " (Admin)" if ctx.deps.is_admin else ""
    return (
        f"Name: {user.name}{admin_status}\n"
        f"Email: {user.email}\n"
        f"Account created: {user.created_at.strftime('%Y-%m-%d')}\n"
        f"Session ID: {ctx.deps.session_id}"
    )


@customer_service_agent.tool
async def get_my_orders(ctx: RunContext[AppContext]) -> str:
    """Get the current user's order history."""
    log.info("getting_user_orders", user_id=ctx.deps.current_user_id)
    orders = await ctx.deps.database.list_user_orders(ctx.deps.current_user_id)
    
    if not orders:
        return "You have no orders yet."
    
    log.info("orders_retrieved", user_id=ctx.deps.current_user_id, order_count=len(orders))
    result = f"You have {len(orders)} order(s):\n"
    for order in orders:
        product = await ctx.deps.database.get_product(order.product_id)
        product_name = product.name if product else "Unknown"
        
        days_ago = (ctx.deps.current_time.date() - order.order_date).days
        time_ref = f"{days_ago} days ago" if days_ago > 0 else "today"
        
        result += (
            f"- Order #{order.id}: {order.quantity}x {product_name} "
            f"({order.status}) - {time_ref}\n"
        )
    
    return result


@customer_service_agent.tool
async def place_order(
    ctx: RunContext[AppContext], product_id: int, quantity: int
) -> str:
    """Place a new order for the current user.
    
    Args:
        ctx: Runtime context with app dependencies
        product_id: ID of the product to order
        quantity: Quantity to order
    """
    log.info("placing_order", user_id=ctx.deps.current_user_id, product_id=product_id, quantity=quantity)
    
    # Verify user exists
    user = await ctx.deps.database.get_user(ctx.deps.current_user_id)
    if not user:
        log.error("order_failed_user_not_found", user_id=ctx.deps.current_user_id)
        return "Error: User not found"
    
    # Create the order
    order = await ctx.deps.database.create_order(
        ctx.deps.current_user_id, product_id, quantity
    )
    
    if not order:
        log.warning("order_failed_product_unavailable", product_id=product_id)
        return "Error: Could not create order. Product may be out of stock."
    
    product = await ctx.deps.database.get_product(product_id)
    product_name = product.name if product else "Unknown"
    
    log.info("order_placed_successfully", order_id=order.id, product_name=product_name)
    return (
        f"Order placed successfully!\n"
        f"Order ID: {order.id}\n"
        f"Product: {product_name}\n"
        f"Quantity: {quantity}\n"
        f"Status: {order.status}"
    )


@customer_service_agent.tool
async def check_business_hours(ctx: RunContext[AppContext]) -> str:
    """Check if customer service is available based on current time."""
    hour = ctx.deps.current_time.hour
    is_available = 9 <= hour < 17
    log.info("checking_business_hours", hour=hour, is_available=is_available)
    
    if is_available:
        return (
            f"Customer service is available now! "
            f"Current time: {ctx.deps.current_time.strftime('%H:%M')}"
        )
    else:
        return (
            f"Customer service hours are 9 AM - 5 PM. "
            f"Current time: {ctx.deps.current_time.strftime('%H:%M')}. "
            f"Please leave a message or try again during business hours."
        )


@customer_service_agent.tool
async def admin_view_user(ctx: RunContext[AppContext], user_id: int) -> str:
    """Admin-only: View any user's information.
    
    Args:
        ctx: Runtime context with app dependencies
        user_id: ID of user to view
    """
    log.info("admin_viewing_user", admin_user_id=ctx.deps.current_user_id, target_user_id=user_id)
    
    if not ctx.deps.is_admin:
        log.warning("admin_access_denied", user_id=ctx.deps.current_user_id)
        return "Error: This function requires admin privileges"
    
    user = await ctx.deps.database.get_user(user_id)
    if not user:
        log.warning("admin_view_user_not_found", user_id=user_id)
        return f"User with ID {user_id} not found"
    
    orders = await ctx.deps.database.list_user_orders(user_id)
    
    return (
        f"[ADMIN VIEW]\n"
        f"User ID: {user.id}\n"
        f"Name: {user.name}\n"
        f"Email: {user.email}\n"
        f"Total Orders: {len(orders)}\n"
        f"Account Status: {'Active' if user.is_active else 'Inactive'}"
    )


async def example_regular_user():
    """Example with regular user context."""
    print("=== Example 1: Regular User ===\n")
    
    ctx = AppContext(
        database=MockDatabase(),
        current_user_id=1,
        current_time=datetime(2024, 1, 15, 14, 30),  # 2:30 PM
        is_admin=False,
        session_id="sess_abc123",
    )
    
    result = await customer_service_agent.run(
        "Can you show me my account information and recent orders?",
        deps=ctx,
    )
    
    print(f"User: Can you show me my account information and recent orders?")
    print(f"Agent: {result.output}\n")


async def example_place_order():
    """Example of placing an order."""
    print("=== Example 2: Place an Order ===\n")
    
    ctx = AppContext(
        database=MockDatabase(),
        current_user_id=2,
        current_time=datetime(2024, 1, 15, 10, 0),
        session_id="sess_xyz789",
    )
    
    result = await customer_service_agent.run(
        "I'd like to order 2 coffee makers (product ID 3)",
        deps=ctx,
    )
    
    print(f"User: I'd like to order 2 coffee makers (product ID 3)")
    print(f"Agent: {result.output}\n")


async def example_business_hours():
    """Example checking business hours."""
    print("=== Example 3: Business Hours Check ===\n")
    
    # After hours
    ctx_evening = AppContext(
        database=MockDatabase(),
        current_user_id=1,
        current_time=datetime(2024, 1, 15, 19, 0),  # 7 PM
        session_id="sess_evening",
    )
    
    result = await customer_service_agent.run(
        "Are you available to help me?",
        deps=ctx_evening,
    )
    
    print(f"User (7 PM): Are you available to help me?")
    print(f"Agent: {result.output}\n")


async def example_admin_access():
    """Example with admin privileges."""
    print("=== Example 4: Admin Access ===\n")
    
    ctx_admin = AppContext(
        database=MockDatabase(),
        current_user_id=1,
        current_time=datetime(2024, 1, 15, 11, 0),
        is_admin=True,
        session_id="sess_admin_001",
    )
    
    result = await customer_service_agent.run(
        "Show me information about user ID 2",
        deps=ctx_admin,
    )
    
    print(f"Admin: Show me information about user ID 2")
    print(f"Agent: {result.output}\n")
    
    # Try same query without admin
    ctx_regular = AppContext(
        database=MockDatabase(),
        current_user_id=3,
        current_time=datetime(2024, 1, 15, 11, 0),
        is_admin=False,
        session_id="sess_user_003",
    )
    
    result2 = await customer_service_agent.run(
        "Show me information about user ID 2",
        deps=ctx_regular,
    )
    
    print(f"Regular User: Show me information about user ID 2")
    print(f"Agent: {result2.output}\n")


async def main():
    """Run all complex dependency examples."""
    print("\n" + "=" * 80)
    print("COMPLEX DEPENDENCY INJECTION EXAMPLES")
    print("=" * 80 + "\n")
    
    await example_regular_user()
    await example_place_order()
    await example_business_hours()
    await example_admin_access()
    
    print("=" * 80)
    print("Check Logfire to see how context flows through all operations!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
