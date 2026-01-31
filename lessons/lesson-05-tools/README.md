# Lesson 5: Tools and Function Calling

## Overview

Tools (also called function calling) allow your agent to perform actions beyond generating text. In this lesson, you'll learn:
- What tools are and why they're essential
- How to add tools to agents
- Tool parameters and return types
- Using dependencies in tools
- Error handling in tools

## What are Tools?

Tools are Python functions that your agent can call to:
- Query databases
- Call external APIs
- Perform calculations
- Access files
- Execute any Python code

The agent decides when and how to use these tools based on the user's request.

## Creating Your First Tool

### Basic Tool

Use the `@agent.tool` decorator to register a function as a tool:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')

@agent.tool
def calculate_square(n: int) -> int:
    """Calculate the square of a number."""
    return n * n

# The agent can now use this tool
result = agent.run_sync('What is the square of 7?')
print(result.data)
# The agent will call calculate_square(7) and use the result
```

### Tool with Multiple Parameters

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')

@agent.tool
def calculate_rectangle_area(length: float, width: float) -> float:
    """Calculate the area of a rectangle."""
    return length * width

@agent.tool
def calculate_circle_area(radius: float) -> float:
    """Calculate the area of a circle."""
    import math
    return math.pi * radius ** 2

result = agent.run_sync('What is the area of a rectangle with length 5 and width 3?')
print(result.data)

result = agent.run_sync('What is the area of a circle with radius 4?')
print(result.data)
```

## Tool Descriptions

The docstring is crucial - it tells the agent what the tool does:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')

@agent.tool
def search_database(query: str, limit: int = 10) -> list[dict]:
    """
    Search the product database.
    
    Args:
        query: The search query string
        limit: Maximum number of results to return (default: 10)
    
    Returns:
        List of product dictionaries matching the query
    """
    # Simulate database search
    return [
        {'id': 1, 'name': 'Product A', 'price': 29.99},
        {'id': 2, 'name': 'Product B', 'price': 49.99}
    ]

result = agent.run_sync('Find products related to "laptop"')
print(result.data)
```

## Tools with Dependencies

Tools can access dependencies through `RunContext`:

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
import sqlite3

@dataclass
class DatabaseDeps:
    connection: sqlite3.Connection

agent = Agent(
    'openai:gpt-4',
    deps_type=DatabaseDeps
)

@agent.tool
def get_user_info(ctx: RunContext[DatabaseDeps], user_id: int) -> dict:
    """Get user information from the database."""
    cursor = ctx.deps.connection.cursor()
    cursor.execute('SELECT id, name, email FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'email': row[2]
        }
    return {'error': 'User not found'}

@agent.tool
def list_user_orders(ctx: RunContext[DatabaseDeps], user_id: int) -> list[dict]:
    """List all orders for a specific user."""
    cursor = ctx.deps.connection.cursor()
    cursor.execute('SELECT id, product, amount FROM orders WHERE user_id = ?', (user_id,))
    
    return [
        {'order_id': row[0], 'product': row[1], 'amount': row[2]}
        for row in cursor.fetchall()
    ]

# Usage
conn = sqlite3.connect(':memory:')
# Create tables and add sample data here...

deps = DatabaseDeps(connection=conn)
result = agent.run_sync('What orders does user 42 have?', deps=deps)
print(result.data)
```

## Async Tools

For I/O operations, use async tools:

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
import httpx

@dataclass
class APIDeps:
    http_client: httpx.AsyncClient
    api_key: str

agent = Agent(
    'openai:gpt-4',
    deps_type=APIDeps
)

@agent.tool
async def fetch_weather(ctx: RunContext[APIDeps], city: str) -> dict:
    """Fetch current weather for a city."""
    url = f"https://api.weather.com/v1/current"
    params = {
        'city': city,
        'apikey': ctx.deps.api_key
    }
    
    response = await ctx.deps.http_client.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    return {'error': 'Failed to fetch weather'}

@agent.tool
async def fetch_news(ctx: RunContext[APIDeps], topic: str) -> list[dict]:
    """Fetch latest news articles about a topic."""
    url = f"https://api.news.com/v1/search"
    params = {
        'q': topic,
        'apikey': ctx.deps.api_key
    }
    
    response = await ctx.deps.http_client.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()['articles']
    return []

# Usage (in async context)
async def main():
    async with httpx.AsyncClient() as client:
        deps = APIDeps(
            http_client=client,
            api_key='your-api-key'
        )
        
        result = await agent.run(
            'What is the weather in London?',
            deps=deps
        )
        print(result.data)
```

## Complex Return Types

Tools can return Pydantic models for structured data:

```python
from pydantic_ai import Agent
from pydantic import BaseModel
from datetime import datetime

class Product(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool
    last_updated: datetime

agent = Agent('openai:gpt-4')

@agent.tool
def get_product(product_id: int) -> Product:
    """Get detailed product information."""
    return Product(
        id=product_id,
        name=f'Product {product_id}',
        price=99.99,
        in_stock=True,
        last_updated=datetime.now()
    )

result = agent.run_sync('Tell me about product 123')
print(result.data)
```

## Error Handling in Tools

Handle errors gracefully in tools:

```python
from pydantic_ai import Agent
from typing import Optional

agent = Agent('openai:gpt-4')

@agent.tool
def divide_numbers(a: float, b: float) -> Optional[float]:
    """
    Divide two numbers.
    
    Returns None if division by zero.
    """
    if b == 0:
        return None
    return a / b

@agent.tool
def safe_fetch_user(user_id: int) -> dict:
    """Safely fetch user data with error handling."""
    try:
        # Simulate database operation
        if user_id < 0:
            raise ValueError("Invalid user ID")
        
        if user_id > 1000:
            return {'error': 'User not found'}
        
        return {
            'id': user_id,
            'name': f'User {user_id}',
            'status': 'active'
        }
    except Exception as e:
        return {'error': str(e)}

result = agent.run_sync('Divide 10 by 0')
print(result.data)  # Agent handles the None return gracefully
```

## Real-World Example: E-commerce Assistant

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category: str
    in_stock: bool

@dataclass
class ShopDeps:
    user_id: str
    cart: dict[int, int]  # product_id -> quantity
    
    def get_cart_total(self) -> float:
        # In real app, would fetch prices from database
        return sum(q * 10.0 for q in self.cart.values())

agent = Agent(
    'openai:gpt-4',
    deps_type=ShopDeps,
    system_prompt="""
    You are a helpful e-commerce shopping assistant.
    Help users find products, manage their cart, and complete purchases.
    Be friendly and provide accurate product information.
    """
)

@agent.tool
def search_products(ctx: RunContext[ShopDeps], query: str, category: Optional[str] = None) -> List[Product]:
    """
    Search for products by name or description.
    
    Args:
        query: Search query string
        category: Optional category filter
    """
    # Simulate database search
    products = [
        Product(
            id=1,
            name='Laptop Pro',
            description='High-performance laptop',
            price=1299.99,
            category='electronics',
            in_stock=True
        ),
        Product(
            id=2,
            name='Wireless Mouse',
            description='Ergonomic wireless mouse',
            price=29.99,
            category='electronics',
            in_stock=True
        ),
        Product(
            id=3,
            name='Desk Chair',
            description='Comfortable office chair',
            price=299.99,
            category='furniture',
            in_stock=False
        )
    ]
    
    # Filter by category if specified
    if category:
        products = [p for p in products if p.category == category]
    
    # Filter by query
    query_lower = query.lower()
    products = [
        p for p in products 
        if query_lower in p.name.lower() or query_lower in p.description.lower()
    ]
    
    return products

@agent.tool
def add_to_cart(ctx: RunContext[ShopDeps], product_id: int, quantity: int = 1) -> dict:
    """
    Add a product to the shopping cart.
    
    Args:
        product_id: ID of the product to add
        quantity: Number of items to add (default: 1)
    """
    if quantity <= 0:
        return {'success': False, 'message': 'Quantity must be positive'}
    
    current_qty = ctx.deps.cart.get(product_id, 0)
    ctx.deps.cart[product_id] = current_qty + quantity
    
    return {
        'success': True,
        'message': f'Added {quantity} item(s) to cart',
        'cart_size': sum(ctx.deps.cart.values())
    }

@agent.tool
def view_cart(ctx: RunContext[ShopDeps]) -> dict:
    """View the current shopping cart contents."""
    if not ctx.deps.cart:
        return {
            'items': [],
            'total': 0.0,
            'message': 'Cart is empty'
        }
    
    # In real app, would fetch product details from database
    items = [
        {
            'product_id': pid,
            'quantity': qty,
            'price': 10.0  # Simplified
        }
        for pid, qty in ctx.deps.cart.items()
    ]
    
    return {
        'items': items,
        'total': ctx.deps.cart_total(),
        'item_count': sum(ctx.deps.cart.values())
    }

@agent.tool
def remove_from_cart(ctx: RunContext[ShopDeps], product_id: int) -> dict:
    """Remove a product from the shopping cart."""
    if product_id in ctx.deps.cart:
        del ctx.deps.cart[product_id]
        return {
            'success': True,
            'message': 'Product removed from cart'
        }
    return {
        'success': False,
        'message': 'Product not in cart'
    }

# Usage
deps = ShopDeps(user_id='user_123', cart={})

result = agent.run_sync('Find me laptops', deps=deps)
print(result.data)

result = agent.run_sync('Add product 1 to my cart', deps=deps)
print(result.data)

result = agent.run_sync('Show me my cart', deps=deps)
print(result.data)
```

## Tool Calling Flow

Here's what happens when an agent uses tools:

1. **User sends message**: "What is 5 squared?"
2. **Agent analyzes**: Determines it needs to use the `calculate_square` tool
3. **Tool call**: Agent calls `calculate_square(5)`
4. **Tool returns**: Returns `25`
5. **Agent responds**: "The square of 5 is 25"

The agent can make multiple tool calls before responding:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')

@agent.tool
def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get exchange rate between two currencies."""
    # Simplified example
    rates = {
        ('USD', 'EUR'): 0.85,
        ('EUR', 'USD'): 1.18,
        ('USD', 'GBP'): 0.73,
        ('GBP', 'USD'): 1.37
    }
    return rates.get((from_currency, to_currency), 1.0)

@agent.tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

# The agent might:
# 1. Call get_exchange_rate('USD', 'EUR') -> 0.85
# 2. Call multiply(100, 0.85) -> 85.0
# 3. Respond: "100 USD is approximately 85 EUR"

result = agent.run_sync('Convert 100 USD to EUR')
print(result.data)
```

## Tool Best Practices

### 1. Clear Tool Names

```python
# ✅ Good - Descriptive names
@agent.tool
def fetch_user_purchase_history(user_id: int) -> list:
    ...

# ❌ Bad - Vague names
@agent.tool
def get_data(id: int) -> list:
    ...
```

### 2. Detailed Docstrings

```python
@agent.tool
def search_products(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> List[Product]:
    """
    Search for products in the catalog.
    
    This tool searches the product database based on the provided criteria.
    Results are sorted by relevance.
    
    Args:
        query: Search term to match against product names and descriptions
        category: Optional category filter (e.g., 'electronics', 'clothing')
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
    
    Returns:
        List of products matching the search criteria, sorted by relevance
    
    Example:
        search_products('laptop', category='electronics', max_price=1000)
    """
    ...
```

### 3. Validate Inputs

```python
@agent.tool
def schedule_meeting(date: str, time: str, duration_minutes: int) -> dict:
    """Schedule a meeting."""
    # Validate inputs
    if duration_minutes <= 0:
        return {'error': 'Duration must be positive'}
    
    if duration_minutes > 480:  # 8 hours
        return {'error': 'Duration cannot exceed 8 hours'}
    
    # Validate date format
    try:
        from datetime import datetime
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return {'error': 'Invalid date format. Use YYYY-MM-DD'}
    
    # Process meeting
    return {'success': True, 'meeting_id': '12345'}
```

### 4. Return Structured Data

```python
from pydantic import BaseModel

class SearchResult(BaseModel):
    query: str
    results: List[dict]
    total_count: int
    page: int

@agent.tool
def search(query: str, page: int = 1) -> SearchResult:
    """Search with structured results."""
    return SearchResult(
        query=query,
        results=[...],
        total_count=100,
        page=page
    )
```

### 5. Handle Async Operations

```python
import asyncio

@agent.tool
async def fetch_multiple_sources(sources: List[str]) -> dict:
    """Fetch data from multiple sources in parallel."""
    
    async def fetch_one(source: str) -> dict:
        # Simulate API call
        await asyncio.sleep(0.1)
        return {'source': source, 'data': 'example'}
    
    # Fetch all in parallel
    results = await asyncio.gather(
        *[fetch_one(source) for source in sources]
    )
    
    return {'sources': sources, 'results': results}
```

## Testing Tools

Test tools independently:

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass

@dataclass
class MockDeps:
    test_data: dict

agent = Agent('openai:gpt-4', deps_type=MockDeps)

@agent.tool
def fetch_data(ctx: RunContext[MockDeps], key: str) -> any:
    """Fetch data by key."""
    return ctx.deps.test_data.get(key)

# Test the tool directly
def test_fetch_data():
    mock_deps = MockDeps(test_data={'key1': 'value1'})
    ctx = RunContext(deps=mock_deps, retry=0)
    
    result = fetch_data(ctx, 'key1')
    assert result == 'value1'
    
    result = fetch_data(ctx, 'missing_key')
    assert result is None

test_fetch_data()
```

## Exercise

Create a task management agent with tools to:
1. `create_task(title: str, description: str, priority: str)` - Create a new task
2. `list_tasks(status: Optional[str])` - List tasks, optionally filtered by status
3. `update_task_status(task_id: int, new_status: str)` - Update task status
4. `get_task_details(task_id: int)` - Get detailed information about a task
5. `delete_task(task_id: int)` - Delete a task

Use dependencies to store the task list and implement proper error handling.

## What's Next?

In the next lesson, we'll explore:
- Using Pydantic models to validate agent outputs
- Structured data extraction
- Ensuring type-safe responses
- Handling validation errors

---

**Previous Lesson**: [Lesson 4: Dependencies and Dependency Injection](../lesson-04-dependencies/README.md)  
**Next Lesson**: [Lesson 6: Result Validation with Pydantic](../lesson-06-result-validation/README.md)
