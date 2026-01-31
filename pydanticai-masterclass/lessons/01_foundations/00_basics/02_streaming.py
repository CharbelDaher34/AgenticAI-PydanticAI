"""Lesson 00.2: Streaming Responses - Stream text output as it arrives.

This example demonstrates:
- Streaming text responses with run_stream()
- Handling stream events asynchronously
- Difference between streaming and non-streaming execution
- Multiple parallel streams
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

streaming_agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a creative storyteller. "
        "Tell engaging short stories with vivid descriptions."
    ),
)


async def example_async_streaming():
    """Basic asynchronous streaming example."""
    print("=== Basic Streaming ===")
    
    prompt = "Tell me a very short story about a robot learning to paint."
    print(f"Prompt: {prompt}\n")
    print("Response: ", end="", flush=True)
    
    async with streaming_agent.run_stream(prompt) as stream:
        # Stream text chunks as they arrive
        async for chunk in stream.stream_text():
            print(chunk, end="", flush=True)
    
    print("\n\n")
    
    # Another example
    prompt = "Write a haiku about artificial intelligence."
    print(f"Prompt: {prompt}\n")
    print("Response:\n", end="", flush=True)
    
    async with streaming_agent.run_stream(prompt) as stream:
        # Stream text chunks as they arrive
        async for chunk in stream.stream_text():
            print(chunk, end="", flush=True)
    
    print("\n")


async def example_streaming_with_result():
    """Get both streamed output and final result."""
    print("=== Streaming with Final Result ===\n")
    
    prompt = "Explain photosynthesis in 2 sentences."
    print(f"Prompt: {prompt}\n")
    print("Streaming: ", end="", flush=True)
    
    # Store the last chunk which contains the complete text
    complete_text = ""
    async with streaming_agent.run_stream(prompt) as stream:
        # Stream the text
        async for chunk in stream.stream_text():
            print(chunk, end="", flush=True)
            complete_text = chunk  # Each chunk is the complete text so far
    
    print("\n")
    print(f"\nComplete response: {complete_text}")
    print(f"Total messages: {len(stream.all_messages())}")
    print(f"Usage: {stream.usage()}")


async def example_multiple_streams():
    """Stream multiple responses concurrently."""
    print("=== Multiple Concurrent Streams ===\n")
    
    prompts = [
        "Name 3 planets.",
        "Name 3 colors.",
        "Name 3 animals.",
    ]
    
    async def stream_response(prompt: str) -> str:
        """Helper to stream a single response."""
        output = []
        async with streaming_agent.run_stream(prompt) as stream:
            async for chunk in stream.stream_text():
                output.append(chunk)
        return "".join(output)
    
    # Run all streams concurrently
    results = await asyncio.gather(*[stream_response(p) for p in prompts])
    
    for prompt, result in zip(prompts, results):
        print(f"Q: {prompt}")
        print(f"A: {result}\n")


async def main():
    """Run all streaming examples."""
    print("\n" + "=" * 80)
    print("STREAMING EXAMPLES")
    print("=" * 80 + "\n")
    
    await example_async_streaming()
    await example_streaming_with_result()
    await example_multiple_streams()
    
    print("=" * 80)
    print("Check Logfire dashboard to see streaming traces!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
