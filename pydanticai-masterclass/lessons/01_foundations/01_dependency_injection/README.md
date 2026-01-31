# Lesson 01: Dependency Injection with PydanticAI

## Overview

This lesson covers dependency injection patterns in PydanticAI, one of the most powerful features for building maintainable and testable agent applications.

## What You'll Learn

1. **RunContext Basics** - Accessing dependencies in tools
2. **Database Dependencies** - Injecting database connections
3. **Multiple Dependencies** - Working with complex dependency types
4. **Dynamic System Prompts** - Using dependencies in system prompts
5. **Testing with Mocks** - How DI makes testing easier

## Key Concepts

### Why Dependency Injection?

Dependency injection (DI) allows you to:
- **Decouple** agent logic from infrastructure (databases, APIs, etc.)
- **Test** agents easily by injecting mock dependencies
- **Reuse** agents across different contexts (dev, prod, testing)
- **Follow** Clean Architecture principles

### RunContext[T]

`RunContext[T]` is PydanticAI's mechanism for passing dependencies:

```python
from pydantic_ai import Agent, RunContext

# Define dependency type
agent = Agent[MyDatabase, str]('openai:gpt-4')

@agent.tool
async def my_tool(ctx: RunContext[MyDatabase], param: str) -> str:
    # Access dependency via ctx.deps
    data = await ctx.deps.query(param)
    return data
```

### Dependency Types

Dependencies can be:
- **Simple types** - `int`, `str`, database connections
- **Dataclasses** - Structured dependencies with multiple fields
- **Protocol types** - Interface-based dependencies for flexibility
- **Any Python object** - As long as it's consistent

## Examples

1. **01_basic_deps.py** - Simple dependency injection
2. **02_database_deps.py** - Using the mock database
3. **03_complex_deps.py** - Multiple dependencies with dataclasses
4. **04_dynamic_prompts.py** - System prompts using dependencies
5. **05_testing_mocks.py** - Testing agents with mock dependencies

## Running the Examples

```bash
# Run basic example
uv run lessons/01_foundations/01_dependency_injection/01_basic_deps.py

# Run database example
uv run lessons/01_foundations/01_dependency_injection/02_database_deps.py

# Run all examples
for f in lessons/01_foundations/01_dependency_injection/*.py; do
    echo "Running $f..."
    uv run "$f"
done
```

## Best Practices

1. **Type your dependencies** - Use specific types, not `Any`
2. **Use protocols** for interfaces when you need flexibility
3. **Keep dependencies immutable** when possible
4. **Inject at the edges** - create dependencies at the outermost layer
5. **Test with mocks** - DI makes testing trivial

## Next Steps

After mastering dependency injection, proceed to:
- **Lesson 02**: Dynamic Tools and deferred execution
- **Lesson 03**: Multi-agent architectures
