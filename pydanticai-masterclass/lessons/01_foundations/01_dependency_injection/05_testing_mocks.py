"""Lesson 01.5: Testing with Mock Dependencies - How DI enables easy testing.

This example demonstrates:
- Testing agents with mock dependencies
- Isolation of business logic
- Predictable test behavior
- Integration vs unit testing
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import logfire
from pydantic_ai import Agent, RunContext

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import settings, get_logger
from common.database import MockDatabase, Product, User

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Get logger from centralized configuration
log = get_logger(__name__)

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()


# Create a mock database for testing
class TestDatabase:
    """Simplified mock database for testing.
    
    This allows us to control exactly what data the agent sees,
    making tests predictable and repeatable.
    """
    
    def __init__(self):
        self.users: dict[int, User] = {}
        self.products: dict[int, Product] = {}
        self.call_log: list[str] = []  # Track what methods were called
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        self.call_log.append(f"get_user({user_id})")
        return self.users.get(user_id)
    
    async def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        self.call_log.append(f"get_product({product_id})")
        return self.products.get(product_id)
    
    async def search_products(self, query: str) -> list[Product]:
        """Search products."""
        self.call_log.append(f"search_products('{query}')")
        # Simple search: match query in product name
        return [
            p
            for p in self.products.values()
            if query.lower() in p.name.lower()
        ]
    
    def add_test_user(self, user: User):
        """Add a test user."""
        self.users[user.id] = user
    
    def add_test_product(self, product: Product):
        """Add a test product."""
        self.products[product.id] = product
    
    def reset_log(self):
        """Clear the call log."""
        self.call_log = []


# Agent under test
test_agent = Agent[TestDatabase, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a product information assistant.",
)


@test_agent.tool
async def find_product(ctx: RunContext[TestDatabase], product_name: str) -> str:
    """Find a product by name."""
    products = await ctx.deps.search_products(product_name)
    
    if not products:
        return f"No products found matching '{product_name}'"
    
    product = products[0]
    return f"Found: {product.name} - ${product.price}"


@test_agent.tool
async def get_product_price(ctx: RunContext[TestDatabase], product_id: int) -> str:
    """Get price of a specific product."""
    product = await ctx.deps.get_product(product_id)
    
    if not product:
        return f"Product {product_id} not found"
    
    return f"${product.price}"


async def test_product_search():
    """Test: Agent can search for products."""
    print("=== Test 1: Product Search ===\n")
    
    # Arrange: Set up test database
    db = TestDatabase()
    db.add_test_product(Product(
        id=1,
        name="Test Laptop",
        price=999.99,
        category="Electronics",
        in_stock=True,
    ))
    
    # Act: Run the agent
    result = await test_agent.run(
        "Find me a laptop",
        deps=db,
    )
    
    # Assert: Check results
    print(f"Query: Find me a laptop")
    print(f"Response: {result.output}")
    print(f"Database calls: {db.call_log}")
    
    # Verify the agent called the right methods
    assert "search_products('laptop')" in db.call_log or "search_products('Laptop')" in db.call_log
    assert "laptop" in result.output.lower()
    
    print("✓ Test passed!\n")


async def test_product_not_found():
    """Test: Agent handles missing products gracefully."""
    print("=== Test 2: Product Not Found ===\n")
    
    # Arrange: Empty database
    db = TestDatabase()
    
    # Act: Search for non-existent product
    result = await test_agent.run(
        "Find me a spaceship",
        deps=db,
    )
    
    # Assert
    print(f"Query: Find me a spaceship")
    print(f"Response: {result.output}")
    print(f"Database calls: {db.call_log}")
    
    assert "search_products" in str(db.call_log)
    assert "not found" in result.output.lower() or "no" in result.output.lower()
    
    print("✓ Test passed!\n")


async def test_price_lookup():
    """Test: Agent can look up prices by ID."""
    print("=== Test 3: Price Lookup ===\n")
    
    # Arrange
    db = TestDatabase()
    db.add_test_product(Product(
        id=42,
        name="Test Widget",
        price=19.99,
        category="Gadgets",
        in_stock=True,
    ))
    
    # Act
    result = await test_agent.run(
        "What's the price of product 42?",
        deps=db,
    )
    
    # Assert
    print(f"Query: What's the price of product 42?")
    print(f"Response: {result.output}")
    print(f"Database calls: {db.call_log}")
    
    assert "get_product(42)" in db.call_log
    assert "19.99" in result.output
    
    print("✓ Test passed!\n")


async def test_multiple_products():
    """Test: Agent handles multiple search results."""
    print("=== Test 4: Multiple Products ===\n")
    
    # Arrange: Add multiple matching products
    db = TestDatabase()
    db.add_test_product(Product(
        id=1,
        name="Gaming Keyboard",
        price=79.99,
        category="Electronics",
        in_stock=True,
    ))
    db.add_test_product(Product(
        id=2,
        name="Mechanical Keyboard",
        price=129.99,
        category="Electronics",
        in_stock=True,
    ))
    
    # Act
    result = await test_agent.run(
        "Show me keyboards",
        deps=db,
    )
    
    # Assert
    print(f"Query: Show me keyboards")
    print(f"Response: {result.output}")
    print(f"Database calls: {db.call_log}")
    
    # Agent should find at least one
    assert "keyboard" in result.output.lower()
    
    print("✓ Test passed!\n")


async def test_with_real_database():
    """Integration test: Use real mock database."""
    print("=== Integration Test: Real Mock Database ===\n")
    
    # Use the actual mock database from common/database.py
    db = MockDatabase()
    
    result = await test_agent.run(
        "Find me a laptop and tell me its price",
        deps=db,
    )
    
    print(f"Query: Find me a laptop and tell me its price")
    print(f"Response: {result.output}")
    
    # This should work with the real data
    assert "laptop" in result.output.lower()
    assert "$" in result.output or "price" in result.output.lower()
    
    print("✓ Integration test passed!\n")


async def test_dependency_isolation():
    """Test: Different test instances are isolated."""
    print("=== Test 5: Dependency Isolation ===\n")
    
    # Create two separate test databases
    db1 = TestDatabase()
    db1.add_test_product(Product(
        id=1,
        name="Product A",
        price=10.0,
        category="Test",
        in_stock=True,
    ))
    
    db2 = TestDatabase()
    db2.add_test_product(Product(
        id=1,
        name="Product B",
        price=20.0,
        category="Test",
        in_stock=True,
    ))
    
    # Run agent with both databases
    result1 = await test_agent.run("What is product 1?", deps=db1)
    result2 = await test_agent.run("What is product 1?", deps=db2)
    
    print(f"Database 1 result: {result1.output}")
    print(f"Database 2 result: {result2.output}")
    
    # Each should have different results
    assert "Product A" in result1.output or "10" in result1.output
    assert "Product B" in result2.output or "20" in result2.output
    
    print("✓ Isolation test passed!\n")


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("TESTING WITH MOCK DEPENDENCIES")
    print("=" * 80 + "\n")
    
    try:
        await test_product_search()
        await test_product_not_found()
        await test_price_lookup()
        await test_multiple_products()
        await test_with_real_database()
        await test_dependency_isolation()
        
        print("=" * 80)
        print("ALL TESTS PASSED! ✓")
        print("=" * 80)
        print("\nKey Takeaways:")
        print("1. DI makes testing easy - inject test data instead of real data")
        print("2. Tests are isolated - each test gets its own dependencies")
        print("3. Tests are predictable - control exact data the agent sees")
        print("4. Easy to test edge cases - just inject edge case data")
        print("\nCheck Logfire to see test traces!")
        print("=" * 80 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
