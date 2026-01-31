# Lesson 4: Dependencies and Dependency Injection

## Overview

Dependencies are a core feature of PydanticAI that enable clean, testable code. In this lesson, you'll learn:
- What dependencies are and why they're important
- How to use dependencies in agents
- Accessing dependencies in system prompts and tools
- Testing with mock dependencies

## What are Dependencies?

Dependencies are services, data, or context that your agent needs to function. Common examples:
- Database connections
- API clients
- Configuration objects
- User session data
- File system access

PydanticAI uses dependency injection to provide these to your agent in a clean, testable way.

## Basic Dependencies

### Defining Dependency Type

Specify the dependency type when creating an agent:

```python
from pydantic_ai import Agent, RunContext

# String dependency
agent = Agent(
    'openai:gpt-4',
    deps_type=str
)

@agent.system_prompt
def get_prompt(ctx: RunContext[str]) -> str:
    user_name = ctx.deps
    return f"You are assisting {user_name}."

# Run with dependency
result = agent.run_sync(
    'Hello!',
    deps='Alice'
)
print(result.data)
```

### Using Dataclasses

Dataclasses are perfect for structured dependencies:

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass

@dataclass
class AppDependencies:
    user_id: str
    database_url: str
    api_key: str
    debug_mode: bool = False

agent = Agent(
    'openai:gpt-4',
    deps_type=AppDependencies
)

@agent.system_prompt
def get_prompt(ctx: RunContext[AppDependencies]) -> str:
    deps = ctx.deps
    prompt = f"You are assisting user {deps.user_id}."
    
    if deps.debug_mode:
        prompt += "\n\nDEBUG MODE: Explain your reasoning."
    
    return prompt

# Create and use dependencies
deps = AppDependencies(
    user_id='user_123',
    database_url='postgresql://localhost/mydb',
    api_key='sk-...',
    debug_mode=True
)

result = agent.run_sync('Help me', deps=deps)
```

## Dependencies in System Prompts

Access dependencies in dynamic system prompts:

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from typing import List

@dataclass
class UserProfile:
    name: str
    interests: List[str]
    skill_level: str

agent = Agent(
    'openai:gpt-4',
    deps_type=UserProfile
)

@agent.system_prompt
def personalized_prompt(ctx: RunContext[UserProfile]) -> str:
    profile = ctx.deps
    interests_str = ', '.join(profile.interests)
    
    return f"""
    You are a personalized learning assistant for {profile.name}.
    
    User Profile:
    - Skill Level: {profile.skill_level}
    - Interests: {interests_str}
    
    Tailor your teaching style to their level and interests.
    """

# Use the agent
user = UserProfile(
    name='Bob',
    interests=['web development', 'APIs', 'databases'],
    skill_level='intermediate'
)

result = agent.run_sync(
    'How do I build a REST API?',
    deps=user
)
print(result.data)
```

## Real-World Example: Database Access

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
import sqlite3
from typing import List, Optional

@dataclass
class DatabaseDeps:
    """Dependencies for database operations."""
    connection: sqlite3.Connection
    
    def get_user(self, user_id: int) -> Optional[dict]:
        """Fetch user from database."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'email': row[2]
            }
        return None
    
    def get_user_orders(self, user_id: int) -> List[dict]:
        """Fetch user orders from database."""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,))
        return [
            {'id': row[0], 'product': row[1], 'amount': row[2]}
            for row in cursor.fetchall()
        ]

# Create agent with database dependencies
agent = Agent(
    'openai:gpt-4',
    deps_type=DatabaseDeps
)

@agent.system_prompt
def get_prompt(ctx: RunContext[DatabaseDeps]) -> str:
    return """
    You are a customer service assistant with access to customer data.
    Provide helpful and accurate information based on the data available.
    """

# We'll add tools in the next lesson, but here's the concept
# Tools can access dependencies via ctx.deps

# Usage
conn = sqlite3.connect('example.db')
db_deps = DatabaseDeps(connection=conn)

result = agent.run_sync(
    'What orders does user 123 have?',
    deps=db_deps
)
```

## Complex Dependencies

### Multiple Services

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
import httpx
from typing import Optional

@dataclass
class AppServices:
    """Collection of application services."""
    http_client: httpx.AsyncClient
    cache: dict
    config: dict
    
    async def fetch_weather(self, city: str) -> Optional[dict]:
        """Fetch weather data from API."""
        # Check cache first
        if city in self.cache:
            return self.cache[city]
        
        # Fetch from API
        api_key = self.config.get('weather_api_key')
        url = f"https://api.weather.com/v1/weather?city={city}&key={api_key}"
        
        response = await self.http_client.get(url)
        if response.status_code == 200:
            data = response.json()
            self.cache[city] = data  # Cache the result
            return data
        
        return None

agent = Agent(
    'openai:gpt-4',
    deps_type=AppServices
)

@agent.system_prompt
def get_prompt(ctx: RunContext[AppServices]) -> str:
    return "You are a helpful weather assistant."

# Later, when we learn about tools, we can use fetch_weather in tools
```

## Pydantic Models as Dependencies

Use Pydantic models for validation:

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field, validator
from typing import List

class UserContext(BaseModel):
    """Validated user context."""
    user_id: str = Field(..., min_length=1)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    roles: List[str] = Field(default_factory=list)
    subscription_tier: str = Field(default='free')
    
    @validator('subscription_tier')
    def validate_tier(cls, v):
        allowed = ['free', 'basic', 'premium', 'enterprise']
        if v not in allowed:
            raise ValueError(f'tier must be one of {allowed}')
        return v

agent = Agent(
    'openai:gpt-4',
    deps_type=UserContext
)

@agent.system_prompt
def get_prompt(ctx: RunContext[UserContext]) -> str:
    user = ctx.deps
    
    prompt = f"You are assisting a {user.subscription_tier} tier user."
    
    if 'admin' in user.roles:
        prompt += "\n\nThis user has admin access."
    
    return prompt

# Pydantic will validate the input
try:
    user = UserContext(
        user_id='usr_123',
        email='user@example.com',
        roles=['user', 'admin'],
        subscription_tier='premium'
    )
    
    result = agent.run_sync(
        'What features do I have access to?',
        deps=user
    )
    print(result.data)
    
except ValueError as e:
    print(f"Validation error: {e}")
```

## Dependency Lifecycle

### Per-Request Dependencies

Create fresh dependencies for each request:

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class RequestContext:
    request_id: str
    timestamp: datetime
    user_agent: str

def create_request_context(user_agent: str) -> RequestContext:
    """Factory function to create request context."""
    return RequestContext(
        request_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        user_agent=user_agent
    )

agent = Agent(
    'openai:gpt-4',
    deps_type=RequestContext
)

@agent.system_prompt
def get_prompt(ctx: RunContext[RequestContext]) -> str:
    req = ctx.deps
    return f"""
    Request ID: {req.request_id}
    Timestamp: {req.timestamp}
    You are processing a user request.
    """

# Each request gets its own context
for i in range(3):
    ctx = create_request_context('Mozilla/5.0')
    result = agent.run_sync(f'Request {i}', deps=ctx)
    print(f"Processed request {ctx.request_id}")
```

## Testing with Mock Dependencies

Dependencies make testing easy:

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from typing import List
import pytest

@dataclass
class DataService:
    """Service to fetch data."""
    
    def get_products(self) -> List[str]:
        # In production, this would call a real database
        raise NotImplementedError("Should be mocked")

agent = Agent(
    'openai:gpt-4',
    deps_type=DataService
)

@agent.system_prompt
def get_prompt(ctx: RunContext[DataService]) -> str:
    return "You are a product assistant."

# Real dependencies for production
class RealDataService(DataService):
    def get_products(self) -> List[str]:
        # Real database query
        return ['Product A', 'Product B', 'Product C']

# Mock dependencies for testing
class MockDataService(DataService):
    def __init__(self, mock_products: List[str]):
        self.mock_products = mock_products
    
    def get_products(self) -> List[str]:
        return self.mock_products

# Production use
prod_service = RealDataService()
result = agent.run_sync('List products', deps=prod_service)

# Testing use
def test_agent_with_mock():
    mock_service = MockDataService(['Test Product 1', 'Test Product 2'])
    result = agent.run_sync('List products', deps=mock_service)
    # Agent can access mock_service.get_products() through tools
    assert result is not None

test_agent_with_mock()
```

## Best Practices

### 1. Use Type Hints

Always specify the dependency type:

```python
# ✅ Good
agent = Agent('openai:gpt-4', deps_type=MyDependencies)

# ❌ Bad
agent = Agent('openai:gpt-4')  # No dependency type
```

### 2. Keep Dependencies Immutable

Use frozen dataclasses when possible:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    api_key: str
    timeout: int
    max_retries: int
```

### 3. Separate Concerns

Don't mix different types of dependencies:

```python
# ✅ Good - Separate concerns
@dataclass
class DatabaseDeps:
    connection: Connection

@dataclass
class APIDeps:
    http_client: httpx.Client

# ❌ Bad - Mixed concerns
@dataclass
class AllDeps:
    db_connection: Connection
    http_client: httpx.Client
    random_string: str
```

### 4. Use Factories

Create factory functions for complex dependencies:

```python
from dataclasses import dataclass
import httpx

@dataclass
class AppDeps:
    http_client: httpx.AsyncClient
    config: dict

def create_app_deps(config_path: str) -> AppDeps:
    """Factory to create app dependencies."""
    # Load config
    config = load_config(config_path)
    
    # Create HTTP client with config
    client = httpx.AsyncClient(
        timeout=config.get('timeout', 30),
        headers={'User-Agent': config.get('user_agent')}
    )
    
    return AppDeps(
        http_client=client,
        config=config
    )

def load_config(path: str) -> dict:
    # Load configuration from file
    return {'timeout': 30, 'user_agent': 'MyApp/1.0'}
```

### 5. Document Dependencies

Add docstrings to dependency classes:

```python
@dataclass
class UserSession:
    """
    User session context for the agent.
    
    Attributes:
        user_id: Unique user identifier
        session_id: Current session ID
        permissions: List of user permissions
        created_at: Session creation timestamp
    """
    user_id: str
    session_id: str
    permissions: List[str]
    created_at: datetime
```

## Complete Example: E-commerce Assistant

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from typing import List, Optional
import httpx

@dataclass
class EcommerceDeps:
    """Dependencies for e-commerce agent."""
    user_id: str
    session_id: str
    http_client: httpx.AsyncClient
    
    async def get_cart(self) -> List[dict]:
        """Get user's shopping cart."""
        url = f"https://api.example.com/cart?user_id={self.user_id}"
        response = await self.http_client.get(url)
        return response.json() if response.status_code == 200 else []
    
    async def search_products(self, query: str) -> List[dict]:
        """Search for products."""
        url = f"https://api.example.com/products/search?q={query}"
        response = await self.http_client.get(url)
        return response.json() if response.status_code == 200 else []

agent = Agent(
    'openai:gpt-4',
    deps_type=EcommerceDeps
)

@agent.system_prompt
def get_prompt(ctx: RunContext[EcommerceDeps]) -> str:
    return f"""
    You are an e-commerce shopping assistant.
    
    Current session: {ctx.deps.session_id}
    User: {ctx.deps.user_id}
    
    You can help with:
    - Product search and recommendations
    - Shopping cart management
    - Order tracking
    - Product comparisons
    
    Be friendly, helpful, and provide accurate product information.
    """

# Usage (in an async context)
async def main():
    async with httpx.AsyncClient() as client:
        deps = EcommerceDeps(
            user_id='user_123',
            session_id='session_abc',
            http_client=client
        )
        
        result = await agent.run(
            'Show me my cart',
            deps=deps
        )
        print(result.data)

# We'll use tools to actually call get_cart() in the next lesson
```

## Exercise

Create a blogging assistant with dependencies that:
1. Uses a `BlogService` dependency with methods to:
   - `get_post(post_id: int)`
   - `list_posts(author: str)`
   - `search_posts(query: str)`
2. Has a `UserContext` dependency with user info
3. Provides different capabilities based on user role (reader, author, admin)
4. Can be tested with mock dependencies

## What's Next?

In the next lesson, we'll learn about Tools (function calling):
- Adding tools to agents
- Using dependencies within tools
- Handling tool errors
- Best practices for tool design

---

**Previous Lesson**: [Lesson 3: System Prompts and Configuration](../lesson-03-system-prompts/README.md)  
**Next Lesson**: [Lesson 5: Tools and Function Calling](../lesson-05-tools/README.md)
