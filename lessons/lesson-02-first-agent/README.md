# Lesson 2: Creating Your First Agent

## Overview

In this lesson, we'll dive deeper into creating and configuring PydanticAI agents. You'll learn how to:
- Initialize agents with different models
- Run agents synchronously and asynchronously
- Handle agent responses
- Configure basic agent parameters

## Creating a Basic Agent

### Simple Agent

The simplest way to create an agent:

```python
from pydantic_ai import Agent

# Create an agent with OpenAI's GPT-4
agent = Agent('openai:gpt-4')

# Run the agent
result = agent.run_sync('Tell me a fun fact about Python programming.')
print(result.data)
```

### Specifying Different Models

PydanticAI supports multiple model providers:

```python
# OpenAI models
agent_gpt4 = Agent('openai:gpt-4')
agent_gpt35 = Agent('openai:gpt-3.5-turbo')

# Anthropic models
agent_claude = Agent('anthropic:claude-3-5-sonnet-20241022')
agent_claude_opus = Agent('anthropic:claude-3-opus-20240229')

# Google Gemini
agent_gemini = Agent('gemini-1.5-pro')
agent_gemini_flash = Agent('gemini-1.5-flash')

# Ollama (local models)
agent_llama = Agent('ollama:llama3.1')
agent_mistral = Agent('ollama:mistral')
```

## Running Agents

### Synchronous Execution

Use `run_sync()` for blocking execution:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')

# Simple synchronous run
result = agent.run_sync('What is 2 + 2?')
print(result.data)  # "4" or "2 + 2 equals 4"

# With message history
result = agent.run_sync(
    'What about 3 + 3?',
    message_history=result.new_messages()
)
print(result.data)
```

### Asynchronous Execution

Use `run()` for async/await patterns:

```python
import asyncio
from pydantic_ai import Agent

async def main():
    agent = Agent('openai:gpt-4')
    
    # Async run
    result = await agent.run('Explain async/await in Python.')
    print(result.data)
    
    # Multiple parallel requests
    results = await asyncio.gather(
        agent.run('What is Python?'),
        agent.run('What is JavaScript?'),
        agent.run('What is Rust?')
    )
    
    for i, result in enumerate(results, 1):
        print(f"\nAnswer {i}: {result.data}")

# Run the async function
asyncio.run(main())
```

## Understanding Agent Results

The `RunResult` object contains important information:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')
result = agent.run_sync('Hello, how are you?')

# Access the response
print(result.data)  # The actual response text

# Access message history
print(result.all_messages())  # All messages including system prompts

# Get new messages only (useful for continuing conversations)
print(result.new_messages())  # Only the messages from this run

# Access usage information
print(result.usage())  # Token usage statistics
```

### Result Structure

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')
result = agent.run_sync('What is the meaning of life?')

# Result properties
print(f"Data: {result.data}")
print(f"All messages: {len(result.all_messages())}")
print(f"New messages: {len(result.new_messages())}")

# Usage information (if available)
usage = result.usage()
if usage:
    print(f"Total tokens: {usage.total_tokens}")
    print(f"Request tokens: {usage.request_tokens}")
    print(f"Response tokens: {usage.response_tokens}")
```

## Agent Configuration

### Model Settings

Configure model-specific parameters:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

# Create a model with custom settings
model = OpenAIModel(
    'gpt-4',
    temperature=0.7,  # Creativity level (0.0 to 2.0)
    max_tokens=500,   # Maximum response length
    top_p=0.9,        # Nucleus sampling
)

agent = Agent(model)
result = agent.run_sync('Write a creative short story opening.')
print(result.data)
```

### Agent Name and Metadata

```python
from pydantic_ai import Agent

agent = Agent(
    'openai:gpt-4',
    name='customer-support-bot',  # Agent name for logging
)

result = agent.run_sync('How can I help you today?')
```

## Conversation Context

Maintain conversation history across multiple runs:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')

# First message
result1 = agent.run_sync('My name is Alice.')
print(f"Agent: {result1.data}")

# Continue conversation with context
result2 = agent.run_sync(
    'What is my name?',
    message_history=result1.new_messages()
)
print(f"Agent: {result2.data}")  # Should remember "Alice"

# Continue further
result3 = agent.run_sync(
    'Can you repeat it?',
    message_history=result2.all_messages()
)
print(f"Agent: {result3.data}")
```

## Handling Errors

Always implement error handling:

```python
from pydantic_ai import Agent, UnexpectedModelBehavior

agent = Agent('openai:gpt-4')

try:
    result = agent.run_sync('Hello!')
    print(result.data)
except UnexpectedModelBehavior as e:
    print(f"Model error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Complete Example: Simple Chatbot

```python
import asyncio
from pydantic_ai import Agent

async def chatbot():
    """A simple chatbot with conversation memory."""
    agent = Agent('openai:gpt-4')
    message_history = []
    
    print("Chatbot started! Type 'quit' to exit.")
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            # Run agent with conversation history
            result = await agent.run(
                user_input,
                message_history=message_history
            )
            
            # Update message history
            message_history = result.all_messages()
            
            # Display response
            print(f"\nBot: {result.data}")
            
        except Exception as e:
            print(f"Error: {e}")

# Run the chatbot
if __name__ == '__main__':
    asyncio.run(chatbot())
```

## Best Practices

1. **Choose the right execution mode**: Use async for I/O-bound operations
2. **Preserve message history**: Keep context for multi-turn conversations
3. **Handle errors gracefully**: Always use try-except blocks
4. **Monitor token usage**: Track costs using `result.usage()`
5. **Set appropriate timeouts**: Don't let requests hang indefinitely
6. **Use appropriate models**: Balance cost and capability

## Common Pitfalls

1. **Forgetting to pass message history**: Conversations lose context
2. **Not handling exceptions**: Application crashes on API errors
3. **Using sync in async contexts**: Blocks the event loop
4. **Ignoring token limits**: Requests fail or get truncated
5. **Hardcoding API keys**: Security risk

## Exercise

Create a simple agent that:
1. Asks the user for their favorite programming language
2. Remembers their answer
3. Provides a fun fact about that language
4. Asks if they want to learn about another language
5. Maintains conversation context throughout

Try implementing this with both synchronous and asynchronous approaches.

## What's Next?

In the next lesson, we'll learn about:
- System prompts for agent personality and behavior
- Dynamic prompts based on context
- Prompt templates and best practices

---

**Previous Lesson**: [Lesson 1: Introduction to PydanticAI](../lesson-01-introduction/README.md)  
**Next Lesson**: [Lesson 3: System Prompts and Configuration](../lesson-03-system-prompts/README.md)
