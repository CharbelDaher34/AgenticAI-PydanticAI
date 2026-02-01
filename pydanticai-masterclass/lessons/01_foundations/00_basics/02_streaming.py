"""Lesson 00.2: Streaming Responses - Stream text output as it arrives.

This example demonstrates:
- Streaming text responses with run_stream()
- Handling stream events asynchronously
- Difference between streaming and non-streaming execution
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
from pydantic_ai.messages import PartDeltaEvent, AgentStreamEvent

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()

streaming_agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a creative storyteller. "
        "Tell engaging short stories with vivid descriptions."
        " Your answers must be concise and short."
    ),
)


async def example_async_streaming():
    """Basic asynchronous streaming example."""
    print("=== Basic Streaming ===")
    
    prompt = "Tell me a very short story about a robot learning to paint."
    print(f"Prompt: {prompt}\n")
    print("Response: ", end="", flush=True)
    
    # Use run_stream_events() to iterate over stream events including deltas
    async for event in streaming_agent.run_stream_events(prompt):
        if isinstance(event, PartDeltaEvent):
            print(event.delta.content_delta, end="", flush=True)
    
    print("\n\n")
    
    # Another example
    prompt = "Write a haiku about artificial intelligence."
    print(f"Prompt: {prompt}\n")
    print("Response:\n", end="", flush=True)
    
    async for event in streaming_agent.run_stream_events(prompt):
        if isinstance(event, PartDeltaEvent):
            print(event.delta.content_delta, end="", flush=True)
    
    print("\n")


async def example_streaming_with_result():
    """Get both streamed output and final result."""
    print("=== Streaming with Final Result ===\n")
    
    prompt = "Explain photosynthesis in 2 sentences."
    print(f"Prompt: {prompt}\n")
    print("Streaming: ", end="", flush=True)
    
    result = None
    async for event in streaming_agent.run_stream_events(prompt):
        if isinstance(event, PartDeltaEvent):
            print(event.delta.content_delta, end="", flush=True)
        elif hasattr(event, 'result'):
            # This is the final AgentRunResultEvent
            result = event.result
    
    print("\n")
    if result:
        print(f"\nComplete response: {result.output}")
        print(f"Total messages: {len(result.all_messages())}")
        print(f"Usage: {result.usage()}")


async def main():
    """Run all streaming examples."""
    print("\n" + "=" * 80)
    print("STREAMING EXAMPLES")
    print("=" * 80 + "\n")
    
    await example_async_streaming()
    await example_streaming_with_result()
    
    print("=" * 80)
    print("Check Logfire dashboard to see streaming traces!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
