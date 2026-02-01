"""Lesson 00.3: Logfire Integration - Complete observability for agents.

This example demonstrates:
- Setting up Logfire for agent tracing
- Instrumenting PydanticAI agents
- Instrumenting HTTPX for HTTP request tracing
- Viewing traces in Logfire
- Structured logging with contextvars

Prerequisites:
    uv add "pydantic-ai[logfire]"
    uv run logfire auth
    uv run logfire projects use
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
request_id_var = ContextVar("request_id", default=None)

# Configure Logfire
logfire.configure()  # Uses .logfire/ directory for configuration
logfire.instrument_pydantic_ai()  # Instrument all PydanticAI agents
logfire.instrument_httpx(capture_all=True)  # Capture HTTP requests/responses

# Create agent with Logfire tracking
agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt="You are a helpful AI assistant with expertise in various topics. Your answers must be clear and concise and short.",
)


async def example_basic_tracing():
    """Basic agent execution with Logfire tracing."""
    print("=== Basic Tracing ===")
    print("Check Logfire dashboard for trace visualization\n")
    
    log.info("starting_basic_example")
    
    result = await agent.run("What is the capital of Japan?")
    
    log.info(
        "agent_completed",
        output_length=len(result.output),
        message_count=len(result.all_messages()),
        result_output=result.output[:50],  # Log first 50 chars
    )
    
    print(f"Answer: {result.output}\n")


async def example_streaming_with_tracing():
    """Streaming with Logfire tracing."""
    print("=== Streaming with Tracing ===")
    print("Check Logfire dashboard to see streaming events\n")
    
    log.info("starting_streaming_example")
    
    prompt = "Explain machine learning in 2 sentences."
    print(f"Prompt: {prompt}\n")
    print("Response: ", end="", flush=True)
    
    from pydantic_ai.messages import PartDeltaEvent
    complete_text = ""
    chunk_count = 0
    async for event in agent.run_stream_events(prompt):
        if isinstance(event, PartDeltaEvent):
            print(event.delta.content_delta, end="", flush=True)
            chunk_count += 1
            complete_text += event.delta.content_delta
    print("\n")
    log.info(
        "streaming_completed",
        chunks_received=chunk_count,
        total_length=len(complete_text),
    )


async def example_with_context():
    """Using contextvars for request tracking."""
    print("=== Context-Based Tracing ===")
    print("Check Logfire to see request_id in all related logs\n")
    
    # Simulate a request with ID
    request_id = "req_12345"
    token = request_id_var.set(request_id)
    log.bind_contextvars(request_id=request_id)
    
    try:
        log.info("user_request_received", query="astronomy question")
        
        result = await agent.run("What is a black hole?")
        
        log.info(
            "user_request_completed",
            success=True,
            response_length=len(result.output),
        )
        
        print(f"Request ID: {request_id}")
        print(f"Answer: {result.output}\n")
        
    finally:
        request_id_var.reset(token)
        log.clear_contextvars()


async def example_error_tracing():
    """Trace error scenarios."""
    print("=== Error Tracing ===")
    print("Check Logfire to see error traces\n")
    
    log.info("attempting_complex_query")
    
    try:
        # This might fail or produce unexpected results
        result = await agent.run(
            "Calculate the square root of -1 and explain the result."
        )
        
        log.info("complex_query_succeeded", output=result.output[:100])
        print(f"Answer: {result.output}\n")
        
    except Exception as e:
        log.exception("complex_query_failed", error=str(e))
        raise


async def example_parallel_with_tracing():
    """Trace multiple concurrent agent runs."""
    print("=== Parallel Execution Tracing ===")
    print("Check Logfire to see parallel traces\n")
    
    questions = [
        "What is photosynthesis?",
        "What is gravity?",
        "What is DNA?",
    ]
    
    log.info("starting_parallel_queries", count=len(questions))
    
    async def run_query(question: str) -> str:
        """Run a single query with logging."""
        log.info("query_started", question=question)
        result = await agent.run(question)
        log.info("query_completed", question=question, length=len(result.output))
        return result.output
    
    results = await asyncio.gather(*[run_query(q) for q in questions])
    
    log.info("parallel_queries_completed", total=len(results))
    
    for question, answer in zip(questions, results):
        print(f"Q: {question}")
        print(f"A: {answer}\n")


async def main():
    """Run all examples with Logfire tracing."""
    print("\n" + "=" * 80)
    print("LOGFIRE TRACING EXAMPLES")
    print("=" * 80 + "\n")
    print("View all traces at: https://logfire.pydantic.dev\n")
    
    # await example_basic_tracing()
    # await example_streaming_with_tracing()
    await example_with_context()
    # await example_error_tracing()
    # await example_parallel_with_tracing()
    
    print("\n" + "=" * 80)
    print("All examples completed! Check your Logfire dashboard.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
