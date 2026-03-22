"""
Test ``PydanticAIClient.stream(..., output_type=...)`` with structured output.

Requires ``OPENAI_API_KEY`` (or switch provider/model in ``main``).

Run from repo root::

    uv run python examples/thinking-traces/stream_output_type_example.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.pydantic_ai_client import (  # noqa: E402
    PydanticAIClient,
    TextDelta,
    ThinkingDelta,
    ToolCallTrace,
    ToolResultTrace,
)


class Location(BaseModel):
    """Structured answer the model must return via output tools."""

    city: str = Field(description="City name")
    country: str = Field(description="Country name")


async def stream_with_output_type() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY in the environment or .env file.")
        return

    client = PydanticAIClient(
        provider="anthropic",
        model_name="claude-sonnet-4-5",
        system_prompt="Answer accurately. When asked for a location, use the required structured format. Think",
    enable_thinking=True,
    thinking_budget=1024,
    max_tokens=10000,
    )

    user_prompt = "Where were the Summer Olympics held in 2012? Reply using the structured output only."

    print("--- Streaming with output_type=Location ---\n")
    text_chunks: list[str] = []

    async for event in client.stream(user_prompt, output_type=Location):
        if isinstance(event, TextDelta):
            text_chunks.append(event.content)
            print(event.content, end="", flush=True)
        elif isinstance(event, ThinkingDelta):
            print(f"\n[thinking] {event.content}", end="", flush=True)
        elif isinstance(event, ToolCallTrace):
            print(f"\n[tool call] {event.tool_name}({event.args})", flush=True)
        elif isinstance(event, ToolResultTrace):
            print(f"\n[tool result] {event.content!r}", flush=True)

 
    client.clear_history()
    result = await client.run(user_prompt, output_type=Location)
    print("run().output (typed):", result.output)
    assert isinstance(result.output, Location)
    assert "London" in result.output.city or "london" in result.output.city.lower()


def main() -> None:
    asyncio.run(stream_with_output_type())


if __name__ == "__main__":
    main()
