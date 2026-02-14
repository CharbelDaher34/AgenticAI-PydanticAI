"""Lesson 00.2: Streaming Responses - Stream text output as it arrives.

This example demonstrates:
- Streaming text responses with run_stream()
- Handling stream events asynchronously
- Difference between streaming and non-streaming execution
- Structured streaming with output_type for validated data
"""

import asyncio
import os
import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Annotated
# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import settings
from common.logging import get_logger
import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.messages import PartDeltaEvent, AgentStreamEvent

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Get logger from centralized configuration
log = get_logger(__name__)

# Context variable for request ID
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Configure Logfire
logfire.configure(console=False)
logfire.instrument_pydantic_ai()

streaming_agent = Agent(
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a creative storyteller. "
        "Tell engaging short stories with vivid descriptions."
        " Your answers must be concise and short."
    ),
)


# Define structured output format for programming languages
class ProgrammingLanguage(BaseModel):
    """Information about a programming language."""
    
    name: str
    year_created: Annotated[int, Field(description="Year the language was first released", ge=1950)]
    paradigm: Annotated[str, Field(description="Primary programming paradigm (e.g., OOP, Functional, Procedural)")]
    use_case: Annotated[str | None, Field(default=None, description="Common use case or domain")] = None
    popularity: Annotated[str | None, Field(default=None, description="Popularity level: High, Medium, or Low")] = None


# Create agent with structured output type
structured_agent = Agent(
    "openai:gpt-4o-mini",
    output_type=list[ProgrammingLanguage],
    system_prompt="You are a knowledgeable programming expert. Provide accurate information about programming languages.",
)


async def example_async_streaming():
    """Basic asynchronous streaming example."""
    print("=== Basic Streaming ===")
    
    # Set request ID for tracking
    request_id = "req_stream_001"
    token = request_id_var.set(request_id)
    log.bind_contextvars(request_id=request_id)
    
    try:
        prompt = "Tell me a very short story about a robot learning to paint."
        print(f"Prompt: {prompt}\n")
        print("Response: ", end="", flush=True)
        
        log.info("starting_streaming_query", prompt_topic="robot_story")
        
        chunk_count = 0
        # Use run_stream_events() to iterate over stream events including deltas
        async for event in streaming_agent.run_stream_events(prompt):
            if isinstance(event, PartDeltaEvent):
                print(event.delta.content_delta, end="", flush=True)
                chunk_count += 1
        
        log.info("streaming_completed", chunks_received=chunk_count)
        print("\n\n")
        
        # Another example
        prompt = "Write a haiku about artificial intelligence."
        print(f"Prompt: {prompt}\n")
        print("Response:\n", end="", flush=True)
        
        log.info("starting_haiku_query", prompt_topic="ai_haiku")
        chunk_count = 0
        
        async for event in streaming_agent.run_stream_events(prompt):
            if isinstance(event, PartDeltaEvent):
                print(event.delta.content_delta, end="", flush=True)
                chunk_count += 1
        
        log.info("haiku_completed", chunks_received=chunk_count)
        print("\n")
    finally:
        request_id_var.reset(token)
        log.clear_contextvars()


async def example_streaming_with_result():
    """Get both streamed output and final result."""
    print("=== Streaming with Final Result ===\n")
    
    # Set request ID for tracking
    request_id = "req_stream_result_001"
    token = request_id_var.set(request_id)
    log.bind_contextvars(request_id=request_id)
    
    try:
        prompt = "Explain photosynthesis in 2 sentences."
        print(f"Prompt: {prompt}\n")
        print("Streaming: ", end="", flush=True)
        
        log.info("starting_streaming_with_result", prompt_topic="photosynthesis")
        
        result = None
        chunk_count = 0
        async for event in streaming_agent.run_stream_events(prompt):
            if isinstance(event, PartDeltaEvent):
                print(event.delta.content_delta, end="", flush=True)
                chunk_count += 1
            elif hasattr(event, 'result'):
                # This is the final AgentRunResultEvent
                result = event.result
        
        print("\n")
        if result:
            log.info(
                "streaming_with_result_completed",
                chunks_received=chunk_count,
                output_length=len(result.output),
                message_count=len(result.all_messages()),
            )
            print(f"\nComplete response: {result.output}")
            print(f"Total messages: {len(result.all_messages())}")
            print(f"Usage: {result.usage()}")
    finally:
        request_id_var.reset(token)
        log.clear_contextvars()


async def example_structured_streaming():
    """Stream structured data with output validation."""
    print("=== Structured Streaming ===\n")
    
    # Set request ID for tracking
    request_id = "req_structured_stream_001"
    token = request_id_var.set(request_id)
    log.bind_contextvars(request_id=request_id)
    
    try:
        prompt = "Generate information about 4 popular programming languages."
        print(f"Prompt: {prompt}\n")
        print("Streaming structured data...\n")
        
        log.info("starting_structured_streaming", prompt_topic="programming_languages", requested_count=4)
        
        update_count = 0
        final_languages = None
        previous_count = 0
        
        # Use run_stream() for structured output streaming
        async with structured_agent.run_stream(prompt) as result:
            print("Receiving languages as they complete:\n")
            print("=" * 80)
            
            # Stream and print each new language as it arrives
            async for languages in result.stream_output(debounce_by=0.01):
                update_count += 1
                
                # Check if we have new languages
                current_count = len(languages)
                if current_count > previous_count:
                    # Print only the newly added languages
                    for idx in range(previous_count, current_count):
                        lang = languages[idx]
                        print(f"\n✓ Language {idx + 1}: {lang.name}")
                        print(f"  Year: {lang.year_created}")
                        print(f"  Paradigm: {lang.paradigm}")
                        if lang.use_case:
                            print(f"  Use Case: {lang.use_case}")
                        if lang.popularity:
                            print(f"  Popularity: {lang.popularity}")
                        print()
                        
                        # Add delay to simulate/visualize progressive arrival
                        await asyncio.sleep(1)
                    
                    previous_count = current_count
                
                final_languages = languages
            
            print("=" * 80)
        
        print("\n")
        
        if final_languages:
            log.info(
                "structured_streaming_completed",
                updates_received=update_count,
                languages_count=len(final_languages),
            )
            
            print(f"\n✅ Streaming complete! Received {len(final_languages)} programming languages.")
            print("All data has been validated and displayed above.\n")
        else:
            log.warning("structured_streaming_no_result")
            print("No data received.")
    
    except Exception as e:
        log.exception("structured_streaming_failed", error=str(e))
        raise
    finally:
        request_id_var.reset(token)
        log.clear_contextvars()


async def main():
    """Run all streaming examples."""
    print("\n" + "=" * 80)
    print("STREAMING EXAMPLES")
    print("=" * 80 + "\n")
    
    # await example_async_streaming()
    # print("\n" + "=" * 50 + "\n")
    # await example_streaming_with_result()
    print("\n" + "=" * 50 + "\n")
    await example_structured_streaming()
    
    print("\n" + "=" * 80)
    print("Check Logfire dashboard to see streaming traces!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
