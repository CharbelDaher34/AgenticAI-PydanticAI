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
from contextvars import ContextVar
from pathlib import Path

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import settings
from common.logging import get_logger
import logfire
from pydantic_ai import Agent

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Get logger from centralized configuration
log = get_logger(__name__)

# Context variable for request ID
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()

# Create a simple agent with instructions
simple_agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt="You are a helpful assistant that provides concise, accurate answers. Your answers must be small.",
)


async def example_basic():
    """Basic asynchronous agent execution."""
    print("=== Basic Agent Execution ===\n")
    
    # Set request ID for tracking
    request_id = "req_basic_001"
    token = request_id_var.set(request_id)
    log.bind_contextvars(request_id=request_id)
    
    try:
        log.info("starting_basic_query", question="capital_of_france")
        
        result = await simple_agent.run("What is the capital of France?")
        
        log.info(
            "agent_completed",
            output_length=len(result.output),
            message_count=len(result.all_messages()),
        )
        
        print(f"Question: What is the capital of France?")
        print(f"Answer: {result.output}\n")
        
        # Access additional result metadata
        print(f"Messages in conversation: {len(result.all_messages())}")
        print(f"Usage: {result.usage()}")
        print()
        
        # Another example
        log.info("starting_quantum_query", question="quantum_computing")
        result = await simple_agent.run("Explain quantum computing in one sentence.")
        log.info("quantum_query_completed", output_length=len(result.output))
        
        print(f"Question: Explain quantum computing in one sentence.")
        print(f"Answer: {result.output}\n")
    finally:
        request_id_var.reset(token)
        log.clear_contextvars()


async def example_multiple_queries():
    """Run multiple queries in parallel."""
    print("=== Parallel Execution ===\n")
    
    # Set request ID for tracking
    request_id = "req_parallel_001"
    token = request_id_var.set(request_id)
    log.bind_contextvars(request_id=request_id)
    
    try:
        questions = [
            "What is the speed of light?",
            "Who invented the telephone?",
            "What year did World War II end?",
        ]
        
        log.info("starting_parallel_queries", count=len(questions))
        
        # Run all queries concurrently
        results = await asyncio.gather(*[simple_agent.run(q) for q in questions])
        
        log.info("parallel_queries_completed", total=len(results))
        
        for question, result in zip(questions, results):
            print(f"Q: {question}")
            print(f"A: {result.output}\n")
    finally:
        request_id_var.reset(token)
        log.clear_contextvars()


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
