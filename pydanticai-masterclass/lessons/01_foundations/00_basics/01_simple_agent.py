"""Lesson 00.1: Simple Agent - Basic agent creation and execution.

This example demonstrates:
- Creating a basic agent with a system prompt
- Running agents asynchronously
- Handling agent results
- Using Pydantic Settings for configuration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import settings
import logfire
from pydantic_ai import Agent

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()

# Create a simple agent with instructions
simple_agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt="You are a helpful assistant that provides concise, accurate answers.",
)


async def example_basic():
    """Basic asynchronous agent execution."""
    print("=== Basic Agent Execution ===\n")
    
    result = await simple_agent.run("What is the capital of France?")
    
    print(f"Question: What is the capital of France?")
    print(f"Answer: {result.output}\n")
    
    # Access additional result metadata
    print(f"Messages in conversation: {len(result.all_messages())}")
    print(f"Usage: {result.usage()}")
    print()
    
    # Another example
    result = await simple_agent.run("Explain quantum computing in one sentence.")
    
    print(f"Question: Explain quantum computing in one sentence.")
    print(f"Answer: {result.output}\n")


async def example_multiple_queries():
    """Run multiple queries in parallel."""
    print("=== Parallel Execution ===\n")
    
    questions = [
        "What is the speed of light?",
        "Who invented the telephone?",
        "What year did World War II end?",
    ]
    
    # Run all queries concurrently
    results = await asyncio.gather(*[simple_agent.run(q) for q in questions])
    
    for question, result in zip(questions, results):
        print(f"Q: {question}")
        print(f"A: {result.output}\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("SIMPLE AGENT EXAMPLES")
    print("=" * 80 + "\n")
    
    await example_basic()
    print("\n" + "=" * 50 + "\n")
    await example_multiple_queries()
    
    print("=" * 80)
    print("Check Logfire dashboard to see execution traces!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
