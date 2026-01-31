# Lesson 8: Advanced Features

## Overview

This lesson covers advanced PydanticAI features for production-grade applications. You'll learn:
- Retry logic and error handling
- Model configuration and switching
- Context management
- Performance optimization
- Testing strategies
- Production best practices

## Retry Logic

### Automatic Retries

PydanticAI includes built-in retry logic for handling transient failures:

```python
from pydantic_ai import Agent

agent = Agent(
    'openai:gpt-4',
    retries=3  # Retry up to 3 times on failure
)

result = agent.run_sync('Hello!')
print(result.data)
```

### Custom Retry Configuration

```python
from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

agent = Agent(
    'openai:gpt-4',
    retries=5,  # Number of retries
    # The agent will retry on validation errors and API failures
)

# Even if the model returns invalid data, it will retry automatically
from pydantic import BaseModel

class ValidatedResponse(BaseModel):
    count: int  # Must be an integer
    items: list[str]

agent_with_validation = Agent(
    'openai:gpt-4',
    result_type=ValidatedResponse,
    retries=3  # Will retry if response doesn't match schema
)
```

## Error Handling

### Handling Specific Exceptions

```python
from pydantic_ai import Agent
from pydantic_ai.exceptions import (
    UnexpectedModelBehavior,
    UserError,
    ModelRetry
)
import asyncio

agent = Agent('openai:gpt-4')

async def robust_agent_call():
    """Handle various error types."""
    try:
        result = await agent.run('Process this request')
        return result.data
    
    except UnexpectedModelBehavior as e:
        # Model returned unexpected output
        print(f"Model error: {e}")
        return None
    
    except ModelRetry as e:
        # Retries exhausted
        print(f"All retries failed: {e}")
        return None
    
    except Exception as e:
        # Other errors
        print(f"Unexpected error: {e}")
        return None

asyncio.run(robust_agent_call())
```

### Graceful Degradation

```python
from pydantic_ai import Agent
from typing import Optional

primary_agent = Agent('openai:gpt-4')
fallback_agent = Agent('openai:gpt-3.5-turbo')

async def resilient_query(prompt: str) -> Optional[str]:
    """Try primary model, fall back to secondary if it fails."""
    try:
        result = await primary_agent.run(prompt)
        return result.data
    except Exception as e:
        print(f"Primary model failed: {e}")
        print("Trying fallback model...")
        
        try:
            result = await fallback_agent.run(prompt)
            return result.data
        except Exception as e:
            print(f"Fallback also failed: {e}")
            return None
```

## Model Configuration

### Advanced Model Parameters

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Create a model with custom settings
model = OpenAIModel(
    'gpt-4',
    temperature=0.7,      # Creativity (0.0-2.0)
    max_tokens=1000,      # Max response length
    top_p=0.9,            # Nucleus sampling
    frequency_penalty=0.5, # Reduce repetition
    presence_penalty=0.3,  # Encourage new topics
)

agent = Agent(model)

result = agent.run_sync('Write a creative story opening.')
print(result.data)
```

### Dynamic Model Selection

```python
from pydantic_ai import Agent
from typing import Literal

def get_agent_for_task(
    task_type: Literal['simple', 'complex', 'creative']
) -> Agent:
    """Select appropriate model based on task complexity."""
    
    if task_type == 'simple':
        # Use faster, cheaper model for simple tasks
        return Agent('openai:gpt-3.5-turbo')
    
    elif task_type == 'complex':
        # Use most capable model for complex reasoning
        return Agent('openai:gpt-4')
    
    else:  # creative
        # Use model with higher temperature for creativity
        from pydantic_ai.models.openai import OpenAIModel
        model = OpenAIModel('gpt-4', temperature=1.2)
        return Agent(model)

# Use appropriate agent for each task
simple_agent = get_agent_for_task('simple')
result = simple_agent.run_sync('What is 2+2?')

complex_agent = get_agent_for_task('complex')
result = complex_agent.run_sync('Explain quantum entanglement')

creative_agent = get_agent_for_task('creative')
result = creative_agent.run_sync('Write a poem about AI')
```

## Context Management

### Conversation History

Properly manage conversation context:

```python
from pydantic_ai import Agent
from typing import List

class ConversationManager:
    """Manage multi-turn conversations."""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self.history = []
        self.max_history = 10  # Keep last 10 exchanges
    
    async def send_message(self, message: str) -> str:
        """Send a message and get response."""
        result = await self.agent.run(
            message,
            message_history=self.history
        )
        
        # Update history, keeping only recent messages
        self.history = result.all_messages()
        if len(self.history) > self.max_history * 2:  # user + assistant messages
            # Keep system message and recent history
            self.history = [self.history[0]] + self.history[-(self.max_history * 2):]
        
        return result.data
    
    def clear_history(self):
        """Clear conversation history."""
        self.history = []

# Usage
agent = Agent('openai:gpt-4', system_prompt='You are a helpful assistant.')
conv = ConversationManager(agent)

import asyncio

async def conversation():
    response1 = await conv.send_message('My name is Alice')
    print(response1)
    
    response2 = await conv.send_message('What is my name?')
    print(response2)  # Should remember "Alice"
    
    conv.clear_history()
    response3 = await conv.send_message('What is my name?')
    print(response3)  # Won't remember

asyncio.run(conversation())
```

### Context Window Management

```python
from pydantic_ai import Agent
import tiktoken

class TokenAwareAgent:
    """Agent that monitors and manages token usage."""
    
    def __init__(self, model: str, max_tokens: int = 8000):
        self.agent = Agent(model)
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def trim_history(self, history: list) -> list:
        """Trim history to fit within token limit."""
        total_tokens = sum(
            self.count_tokens(str(msg))
            for msg in history
        )
        
        # Keep system message and trim oldest messages
        if total_tokens > self.max_tokens * 0.8:  # 80% threshold
            # Keep first (system) and recent messages
            return [history[0]] + history[-(len(history) // 2):]
        
        return history
    
    async def run(self, message: str, history: list = None) -> tuple:
        """Run agent with token management."""
        if history:
            history = self.trim_history(history)
        
        result = await self.agent.run(message, message_history=history)
        
        # Return result and token usage
        usage = result.usage()
        return result.data, usage

# Usage
import asyncio

async def main():
    agent = TokenAwareAgent('gpt-4')
    response, usage = await agent.run('Hello!')
    
    print(f"Response: {response}")
    print(f"Tokens used: {usage.total_tokens if usage else 'N/A'}")

asyncio.run(main())
```

## Performance Optimization

### Caching Responses

```python
from pydantic_ai import Agent
from functools import lru_cache
import hashlib
import json

class CachedAgent:
    """Agent with response caching."""
    
    def __init__(self, model: str):
        self.agent = Agent(model)
        self.cache = {}
    
    def _make_cache_key(self, prompt: str, **kwargs) -> str:
        """Create a cache key from prompt and parameters."""
        data = {'prompt': prompt, **kwargs}
        return hashlib.md5(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
    
    async def run(self, prompt: str, use_cache: bool = True, **kwargs):
        """Run with optional caching."""
        cache_key = self._make_cache_key(prompt, **kwargs)
        
        if use_cache and cache_key in self.cache:
            print("Cache hit!")
            return self.cache[cache_key]
        
        result = await self.agent.run(prompt, **kwargs)
        
        if use_cache:
            self.cache[cache_key] = result.data
        
        return result.data
    
    def clear_cache(self):
        """Clear the cache."""
        self.cache.clear()

# Usage
import asyncio

async def main():
    agent = CachedAgent('openai:gpt-4')
    
    # First call - makes API request
    response1 = await agent.run('What is Python?')
    print(response1)
    
    # Second call - uses cache
    response2 = await agent.run('What is Python?')
    print(response2)

asyncio.run(main())
```

### Batch Processing

```python
from pydantic_ai import Agent
import asyncio
from typing import List

async def batch_process(
    agent: Agent,
    prompts: List[str],
    max_concurrent: int = 5
) -> List[str]:
    """Process multiple prompts with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_one(prompt: str) -> str:
        async with semaphore:
            result = await agent.run(prompt)
            return result.data
    
    # Process all prompts concurrently (with limit)
    results = await asyncio.gather(
        *[process_one(prompt) for prompt in prompts]
    )
    
    return results

# Usage
async def main():
    agent = Agent('openai:gpt-4')
    
    prompts = [
        'What is Python?',
        'What is JavaScript?',
        'What is Rust?',
        'What is Go?',
        'What is TypeScript?',
    ]
    
    results = await batch_process(agent, prompts, max_concurrent=3)
    
    for prompt, result in zip(prompts, results):
        print(f"\nQ: {prompt}")
        print(f"A: {result[:100]}...")

asyncio.run(main())
```

## Testing Strategies

### Mock Agent for Testing

```python
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    name: str
    age: int
    email: str

# Production agent
production_agent = Agent(
    'openai:gpt-4',
    result_type=User
)

# Mock for testing
class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self, mock_response: any):
        self.mock_response = mock_response
    
    async def run(self, prompt: str, **kwargs):
        """Return mock response."""
        class MockResult:
            def __init__(self, data):
                self.data = data
        
        return MockResult(self.mock_response)
    
    def run_sync(self, prompt: str, **kwargs):
        """Sync version."""
        class MockResult:
            def __init__(self, data):
                self.data = data
        
        return MockResult(self.mock_response)

# Test using mock
def test_user_extraction():
    """Test user extraction without API calls."""
    mock_user = User(name='Test User', age=30, email='test@example.com')
    mock_agent = MockAgent(mock_user)
    
    result = mock_agent.run_sync('Extract user info...')
    
    assert result.data.name == 'Test User'
    assert result.data.age == 30
    assert result.data.email == 'test@example.com'
    
    print("✅ Test passed!")

test_user_extraction()
```

### Integration Testing

```python
import pytest
from pydantic_ai import Agent

@pytest.fixture
def agent():
    """Create agent for testing."""
    return Agent('openai:gpt-4')

@pytest.mark.asyncio
async def test_basic_response(agent):
    """Test basic agent functionality."""
    result = await agent.run('Say hello')
    assert result.data is not None
    assert len(result.data) > 0

@pytest.mark.asyncio
async def test_structured_output(agent):
    """Test structured output."""
    from pydantic import BaseModel
    
    class Response(BaseModel):
        answer: int
    
    typed_agent = Agent('openai:gpt-4', result_type=Response)
    result = await typed_agent.run('What is 2 + 2?')
    
    assert isinstance(result.data, Response)
    assert result.data.answer == 4
```

## Production Best Practices

### Monitoring and Logging

```python
from pydantic_ai import Agent
import logging
from datetime import datetime
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoredAgent:
    """Agent with monitoring and logging."""
    
    def __init__(self, model: str):
        self.agent = Agent(model)
        self.call_count = 0
        self.total_tokens = 0
        self.errors = []
    
    async def run(self, prompt: str, **kwargs) -> Any:
        """Run with monitoring."""
        self.call_count += 1
        start_time = datetime.now()
        
        logger.info(f"Agent call #{self.call_count} started")
        logger.debug(f"Prompt: {prompt[:100]}...")
        
        try:
            result = await self.agent.run(prompt, **kwargs)
            
            # Track usage
            usage = result.usage()
            if usage:
                self.total_tokens += usage.total_tokens
                logger.info(f"Tokens used: {usage.total_tokens}")
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Agent call completed in {duration:.2f}s")
            
            return result.data
        
        except Exception as e:
            self.errors.append({
                'timestamp': datetime.now(),
                'error': str(e),
                'prompt': prompt
            })
            logger.error(f"Agent call failed: {e}")
            raise
    
    def get_stats(self) -> dict:
        """Get usage statistics."""
        return {
            'total_calls': self.call_count,
            'total_tokens': self.total_tokens,
            'error_count': len(self.errors),
            'errors': self.errors
        }

# Usage
import asyncio

async def main():
    agent = MonitoredAgent('openai:gpt-4')
    
    await agent.run('What is Python?')
    await agent.run('What is JavaScript?')
    
    stats = agent.get_stats()
    print(f"\nAgent Statistics:")
    print(f"Total calls: {stats['total_calls']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Errors: {stats['error_count']}")

asyncio.run(main())
```

### Rate Limiting

```python
import asyncio
from datetime import datetime, timedelta
from collections import deque
from pydantic_ai import Agent

class RateLimitedAgent:
    """Agent with rate limiting."""
    
    def __init__(
        self,
        model: str,
        max_requests: int = 10,
        time_window: int = 60  # seconds
    ):
        self.agent = Agent(model)
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    async def _wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = datetime.now()
        
        # Remove old requests outside time window
        while self.requests and (now - self.requests[0]) > timedelta(seconds=self.time_window):
            self.requests.popleft()
        
        # Check if we need to wait
        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest = self.requests[0]
            wait_until = oldest + timedelta(seconds=self.time_window)
            wait_seconds = (wait_until - now).total_seconds()
            
            if wait_seconds > 0:
                print(f"Rate limit reached. Waiting {wait_seconds:.1f}s...")
                await asyncio.sleep(wait_seconds)
                # Try again
                await self._wait_if_needed()
    
    async def run(self, prompt: str, **kwargs):
        """Run with rate limiting."""
        await self._wait_if_needed()
        
        # Add this request
        self.requests.append(datetime.now())
        
        # Execute
        result = await self.agent.run(prompt, **kwargs)
        return result.data

# Usage
async def main():
    # Allow max 3 requests per 10 seconds
    agent = RateLimitedAgent('openai:gpt-4', max_requests=3, time_window=10)
    
    for i in range(5):
        print(f"\nRequest {i+1}")
        result = await agent.run(f'Say hello {i+1}')
        print(result)

asyncio.run(main())
```

### Environment Configuration

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import Literal
import os

class AgentConfig(BaseModel):
    """Agent configuration."""
    model: str = Field(default='openai:gpt-4')
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0)
    retries: int = Field(default=3, ge=0)
    environment: Literal['development', 'staging', 'production'] = 'development'
    
    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Load configuration from environment variables."""
        return cls(
            model=os.getenv('AGENT_MODEL', 'openai:gpt-4'),
            temperature=float(os.getenv('AGENT_TEMPERATURE', '0.7')),
            max_tokens=int(os.getenv('AGENT_MAX_TOKENS', '1000')),
            retries=int(os.getenv('AGENT_RETRIES', '3')),
            environment=os.getenv('ENVIRONMENT', 'development')
        )

def create_agent(config: AgentConfig = None) -> Agent:
    """Create agent from configuration."""
    if config is None:
        config = AgentConfig.from_env()
    
    # Adjust settings based on environment
    if config.environment == 'production':
        # Use more conservative settings in production
        config.retries = max(config.retries, 5)
    
    from pydantic_ai.models.openai import OpenAIModel
    model = OpenAIModel(
        config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens
    )
    
    return Agent(model, retries=config.retries)

# Usage
config = AgentConfig.from_env()
agent = create_agent(config)
```

## Complete Production Example

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from dataclasses import dataclass
import logging
import asyncio
from typing import Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class CustomerQuery(BaseModel):
    query_id: str
    customer_id: str
    question: str
    category: Optional[str]

class SupportResponse(BaseModel):
    response_text: str
    category: str
    requires_escalation: bool
    confidence_score: float

# Dependencies
@dataclass
class SupportDeps:
    customer_id: str
    knowledge_base: dict
    
    def search_kb(self, query: str) -> list:
        """Search knowledge base."""
        # Simplified
        return self.knowledge_base.get(query, [])

# Create agent
agent = Agent(
    'openai:gpt-4',
    deps_type=SupportDeps,
    result_type=SupportResponse,
    retries=3
)

@agent.system_prompt
def support_prompt(ctx: RunContext[SupportDeps]) -> str:
    return f"""
    You are a customer support assistant for customer {ctx.deps.customer_id}.
    
    Provide helpful, accurate responses.
    Set requires_escalation=true for complex issues.
    Set confidence_score based on how certain you are (0.0-1.0).
    """

# Main application
class SupportAgent:
    """Production-ready support agent."""
    
    def __init__(self):
        self.agent = agent
        self.request_count = 0
    
    async def handle_query(
        self,
        query: CustomerQuery,
        knowledge_base: dict
    ) -> SupportResponse:
        """Handle a customer query."""
        self.request_count += 1
        
        logger.info(
            f"Processing query {query.query_id} "
            f"from customer {query.customer_id}"
        )
        
        deps = SupportDeps(
            customer_id=query.customer_id,
            knowledge_base=knowledge_base
        )
        
        try:
            result = await self.agent.run(
                query.question,
                deps=deps
            )
            
            logger.info(
                f"Query {query.query_id} completed. "
                f"Escalation needed: {result.data.requires_escalation}"
            )
            
            return result.data
        
        except Exception as e:
            logger.error(f"Query {query.query_id} failed: {e}")
            raise

# Usage
async def main():
    support = SupportAgent()
    
    query = CustomerQuery(
        query_id='Q-001',
        customer_id='CUST-123',
        question='How do I reset my password?',
        category='account'
    )
    
    knowledge_base = {
        'password': ['Use forgot password link', 'Check email for reset link']
    }
    
    response = await support.handle_query(query, knowledge_base)
    
    print(f"Response: {response.response_text}")
    print(f"Category: {response.category}")
    print(f"Escalation needed: {response.requires_escalation}")
    print(f"Confidence: {response.confidence_score}")

asyncio.run(main())
```

## Exercise

Build a production-ready agent system with:
1. Configuration management
2. Logging and monitoring
3. Error handling and retries
4. Rate limiting
5. Caching
6. Testing suite

Use case: A document summarization service that processes multiple documents concurrently.

## Congratulations!

You've completed the PydanticAI tutorial! You now know:
- ✅ Core concepts and architecture
- ✅ Agent creation and configuration
- ✅ System prompts and dependencies
- ✅ Tools and function calling
- ✅ Result validation with Pydantic
- ✅ Streaming responses
- ✅ Advanced production features

## Next Steps

1. **Build a real project**: Apply what you've learned
2. **Read the docs**: [ai.pydantic.dev](https://ai.pydantic.dev)
3. **Join the community**: Share your experiences
4. **Explore examples**: Check out official examples
5. **Stay updated**: PydanticAI is actively developed

## Resources

- [PydanticAI Documentation](https://ai.pydantic.dev/)
- [GitHub Repository](https://github.com/pydantic/pydantic-ai)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Discord Community](https://discord.gg/pydantic)

---

**Previous Lesson**: [Lesson 7: Streaming Responses](../lesson-07-streaming/README.md)  
**Back to Start**: [Lesson 1: Introduction](../lesson-01-introduction/README.md)
