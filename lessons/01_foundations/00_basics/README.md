# Lesson 00: PydanticAI Basics

## Overview

This lesson introduces the fundamentals of PydanticAI agents, covering:

- Creating and running agents (async-only)
- System prompts and instructions
- Streaming responses
- Complete observability with Logfire

## What You'll Learn

1. **Agent Creation** - How to instantiate agents with models and instructions
2. **Running Agents** - Asynchronous execution patterns
3. **Observability** - Using Logfire to trace and debug agent behavior (free tier)
4. **Basic Patterns** - Common patterns for building AI applications

## Prerequisites

```bash
# Install dependencies with Logfire support
uv add "pydantic-ai[logfire]"

# Authenticate with Logfire (free tier - no credit card required)
uv run logfire auth
uv run logfire projects use  # or create new
```

## Examples

All examples use **async-only** patterns and include **Logfire** tracing.

1. **01_simple_agent.py** - Basic agent creation and async execution
2. **02_streaming.py** - Streaming text responses asynchronously
3. **03_with_logfire.py** - Complete observability setup with advanced patterns

## Key Concepts

### Agent Structure

An agent consists of:
- **Model** - The LLM to use (e.g., `openai:gpt-4o-mini`)
- **Instructions** - System prompt guiding the agent's behavior
- **Tools** - Functions the agent can call (covered in next lessons)
- **Output Type** - Expected return type (str, structured models, etc.)

### Execution Modes

- `run()` - Async execution, returns complete result
- `run_stream()` - Stream text/structured output as it arrives asynchronously
- `run_stream_events()` - Stream all events including tool calls

## Best Practices

1. **Always use Logfire** for debugging and monitoring (free tier available)
2. **Use async** patterns exclusively for better performance and scalability
3. **Use structured outputs** with Pydantic models for type safety
4. **Keep system prompts clear and concise**
5. **Follow Clean Architecture** principles from coding standards

## Running the Examples

All examples require environment variables for API keys:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-key-here"

# Run basic example
uv run lessons/01_foundations/00_basics/01_simple_agent.py

# Run with streaming
uv run lessons/01_foundations/00_basics/02_streaming.py

# Run with Logfire tracing
uv run lessons/01_foundations/00_basics/03_with_logfire.py
```

## Logfire Benefits

With Logfire instrumentation, you get:
- **Complete visibility** into agent execution
- **Tool call traces** showing what the agent decided to do
- **Token usage tracking** for cost monitoring
- **Error tracking** with full context
- **Performance metrics** for optimization

Check your Logfire dashboard at https://logfire.pydantic.dev after running examples!

## Next Steps

Once you're comfortable with these basics, move on to:
- **Lesson 01**: Dependency Injection patterns
- **Lesson 02**: Dynamic Tools and deferred execution
