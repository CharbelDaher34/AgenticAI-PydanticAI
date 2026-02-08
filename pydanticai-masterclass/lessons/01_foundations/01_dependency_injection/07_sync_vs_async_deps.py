"""Lesson 01.7: Synchronous vs Asynchronous Dependencies.

This example demonstrates:
- The difference between sync and async dependencies
- When to use each approach
- How PydanticAI handles both patterns
- Performance considerations
"""

import asyncio
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import logfire
from pydantic_ai import Agent, RunContext

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings

# Get structured logger
log = get_logger(__name__)

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()


# ============================================================================
# Asynchronous Dependencies (Preferred for I/O operations)
# ============================================================================

@dataclass
class AsyncAPIDeps:
    """Asynchronous dependencies for API calls.
    
    Use async when:
    - Making HTTP requests
    - Querying databases
    - Reading/writing files
    - Any I/O-bound operations
    """
    
    api_key: str
    base_url: str
    timeout: float = 5.0


async_agent = Agent[AsyncAPIDeps, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a weather information assistant.",
)


@async_agent.tool
async def fetch_weather_async(ctx: RunContext[AsyncAPIDeps], city: str) -> str:
    """Asynchronously fetch weather data.
    
    This is an async function, so it can use 'await' for I/O operations.
    """
    log.info("fetching_weather_async", city=city)
    
    # Simulate async API call
    await asyncio.sleep(0.1)  # Simulated network delay
    
    # In real code, you'd use httpx or aiohttp:
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(
    #         f"{ctx.deps.base_url}/weather",
    #         params={"city": city},
    #         headers={"Authorization": f"Bearer {ctx.deps.api_key}"},
    #         timeout=ctx.deps.timeout,
    #     )
    #     return response.json()
    
    # Simulated response
    return f"Weather in {city}: Sunny, 72°F (using async API)"


# ============================================================================
# Synchronous Dependencies (Works, but less efficient for I/O)
# ============================================================================

@dataclass
class SyncAPIDeps:
    """Synchronous dependencies for blocking operations.
    
    Use sync when:
    - Doing CPU-bound computations
    - Accessing in-memory data structures
    - Using libraries that don't support async
    """
    
    api_key: str
    base_url: str
    timeout: float = 5.0


sync_agent = Agent[SyncAPIDeps, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a weather information assistant.",
)


@sync_agent.tool
def fetch_weather_sync(ctx: RunContext[SyncAPIDeps], city: str) -> str:
    """Synchronously fetch weather data.
    
    This is a regular function (not async), so it blocks during I/O.
    PydanticAI will run it in a thread pool to avoid blocking the event loop.
    """
    log.info("fetching_weather_sync", city=city)
    
    # Simulate blocking API call
    time.sleep(0.1)  # Simulated network delay
    
    # In real code, you'd use requests:
    # import requests
    # response = requests.get(
    #     f"{ctx.deps.base_url}/weather",
    #     params={"city": city},
    #     headers={"Authorization": f"Bearer {ctx.deps.api_key}"},
    #     timeout=ctx.deps.timeout,
    # )
    # return response.json()
    
    # Simulated response
    return f"Weather in {city}: Sunny, 72°F (using sync API)"


# ============================================================================
# CPU-Bound Operations (Good use case for sync)
# ============================================================================

@dataclass
class ComputationDeps:
    """Dependencies for CPU-intensive operations."""
    
    max_iterations: int
    precision: int


compute_agent = Agent[ComputationDeps, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a mathematical computation assistant.",
)


@compute_agent.tool
def calculate_fibonacci(ctx: RunContext[ComputationDeps], n: int) -> str:
    """Calculate Fibonacci number synchronously.
    
    CPU-bound operations like this are fine as sync functions.
    They'll run in a thread pool and won't block the event loop.
    """
    log.info("calculating_fibonacci", n=n)
    
    if n > ctx.deps.max_iterations:
        return f"Calculation too large (max: {ctx.deps.max_iterations})"
    
    def fib(num: int) -> int:
        if num <= 1:
            return num
        return fib(num - 1) + fib(num - 2)
    
    result = fib(n)
    return f"Fibonacci({n}) = {result}"


@compute_agent.tool
def format_number(ctx: RunContext[ComputationDeps], number: float) -> str:
    """Format a number with specified precision."""
    log.info("formatting_number", number=number)
    return f"{number:.{ctx.deps.precision}f}"


# ============================================================================
# Mixed: Sync System Prompt, Async Tools
# ============================================================================

@dataclass
class MixedDeps:
    """Dependencies that support both sync and async operations."""
    
    config: dict[str, str]  # In-memory config (sync access is fine)
    api_key: str  # For async API calls


mixed_agent = Agent[MixedDeps, str](
    "openai:gpt-4o-mini",
)


@mixed_agent.system_prompt
def get_system_prompt_sync(ctx: RunContext[MixedDeps]) -> str:
    """Synchronous system prompt that reads from in-memory config.
    
    Since we're just accessing a dict, sync is fine and more straightforward.
    """
    app_name = ctx.deps.config.get("app_name", "App")
    version = ctx.deps.config.get("version", "1.0")
    
    return f"You are {app_name} v{version}, a helpful assistant."


@mixed_agent.tool
async def fetch_user_data_async(ctx: RunContext[MixedDeps], user_id: int) -> str:
    """Async tool for I/O operations."""
    log.info("fetching_user_data", user_id=user_id)
    
    # Simulate async API call
    await asyncio.sleep(0.1)
    
    return f"User {user_id}: Premium member since 2024"


@mixed_agent.tool
def get_config_value(ctx: RunContext[MixedDeps], key: str) -> str:
    """Sync tool for accessing in-memory data."""
    log.info("getting_config", key=key)
    
    value = ctx.deps.config.get(key, "Not found")
    return f"Config {key}: {value}"


async def example_async_dependency():
    """Example: Using async dependencies for I/O."""
    print("=== Example 1: Async Dependencies (Recommended for I/O) ===\n")
    
    deps = AsyncAPIDeps(
        api_key="test_key",
        base_url="https://api.weather.example.com",
    )
    
    result = await async_agent.run(
        "What's the weather in San Francisco?",
        deps=deps,
    )
    
    print(f"User: What's the weather in San Francisco?")
    print(f"Agent: {result.output}\n")


async def example_sync_dependency():
    """Example: Using sync dependencies (less efficient for I/O)."""
    print("=== Example 2: Sync Dependencies (Works but less efficient) ===\n")
    
    deps = SyncAPIDeps(
        api_key="test_key",
        base_url="https://api.weather.example.com",
    )
    
    result = await sync_agent.run(
        "What's the weather in New York?",
        deps=deps,
    )
    
    print(f"User: What's the weather in New York?")
    print(f"Agent: {result.output}\n")


async def example_cpu_bound():
    """Example: CPU-bound operations work well with sync."""
    print("=== Example 3: CPU-Bound Operations (Sync is fine) ===\n")
    
    deps = ComputationDeps(
        max_iterations=20,
        precision=2,
    )
    
    result = await compute_agent.run(
        "Calculate the 10th Fibonacci number",
        deps=deps,
    )
    
    print(f"User: Calculate the 10th Fibonacci number")
    print(f"Agent: {result.output}\n")


async def example_mixed():
    """Example: Mixing sync and async is perfectly fine."""
    print("=== Example 4: Mixed Sync/Async (Best of both) ===\n")
    
    deps = MixedDeps(
        config={
            "app_name": "WeatherBot",
            "version": "2.0",
            "region": "US-West",
        },
        api_key="test_key",
    )
    
    result = await mixed_agent.run(
        "What's my subscription status and what's your version?",
        deps=deps,
    )
    
    print(f"User: What's my subscription status and what's your version?")
    print(f"Agent: {result.output}\n")


async def example_performance_comparison():
    """Demonstrate performance difference (async is better for I/O)."""
    print("=== Example 5: Performance Comparison ===\n")
    
    # Note: In real scenarios with actual I/O, async would be significantly faster
    # when making multiple concurrent calls
    
    print("Making 3 weather queries...")
    
    # Async version
    start_async = time.time()
    async_deps = AsyncAPIDeps(api_key="test", base_url="https://api.example.com")
    
    # These could potentially run concurrently internally
    await async_agent.run("Weather in London?", deps=async_deps)
    await async_agent.run("Weather in Paris?", deps=async_deps)
    await async_agent.run("Weather in Tokyo?", deps=async_deps)
    
    async_time = time.time() - start_async
    print(f"✓ Async version: {async_time:.2f}s")
    
    # Sync version
    start_sync = time.time()
    sync_deps = SyncAPIDeps(api_key="test", base_url="https://api.example.com")
    
    await sync_agent.run("Weather in London?", deps=sync_deps)
    await sync_agent.run("Weather in Paris?", deps=sync_deps)
    await sync_agent.run("Weather in Tokyo?", deps=sync_deps)
    
    sync_time = time.time() - start_sync
    print(f"✓ Sync version: {sync_time:.2f}s\n")


async def main():
    """Run all sync vs async examples."""
    print("\n" + "=" * 80)
    print("SYNCHRONOUS VS ASYNCHRONOUS DEPENDENCIES")
    print("=" * 80 + "\n")
    
    print("Guidelines:")
    print("- Use ASYNC for: HTTP requests, database queries, file I/O")
    print("- Use SYNC for: CPU-bound tasks, in-memory data, legacy libraries")
    print("- You can MIX both in the same agent!\n")
    
    await example_async_dependency()
    await example_sync_dependency()
    await example_cpu_bound()
    await example_mixed()
    await example_performance_comparison()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- Async is preferred for I/O operations (more efficient)")
    print("- Sync works fine for CPU-bound tasks")
    print("- PydanticAI runs sync functions in a thread pool (non-blocking)")
    print("- You can mix sync and async in the same agent")
    print("- Choose based on what your dependencies do, not agent.run() method")
    print("\nCheck Logfire to see execution traces!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
