"""
PydanticAIClient — dynamic tools, swappable providers, full streaming traces.
Fixed: thinking traces now stream correctly via PartStartEvent tracking.

pip install pydantic-ai
"""
from dotenv import load_dotenv
load_dotenv()
import asyncio
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.models.groq import GroqModel, GroqModelSettings
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from pydantic_ai.models.xai import XaiModel, XaiModelSettings
from pydantic_ai.settings import ModelSettings


# ── Trace events ──────────────────────────────────────────────────────────────

@dataclass
class ThinkingStart:
    """Emitted when the model opens a new thinking block."""
    part_index: int

@dataclass
class ThinkingDelta:
    """A streamed chunk of internal reasoning."""
    content: str
    part_index: int

@dataclass
class ThinkingEnd:
    """Emitted when a thinking block is closed."""
    part_index: int

@dataclass
class TextDelta:
    """A streamed chunk of assistant text."""
    content: str

@dataclass
class ToolCallTrace:
    """Emitted just before a tool is executed."""
    tool_name: str
    args: Any
    tool_call_id: str

@dataclass
class ToolResultTrace:
    """Emitted after a tool returns."""
    tool_call_id: str
    content: Any

@dataclass
class FinalOutput:
    """The complete assembled answer."""
    content: str

TraceEvent = (
    ThinkingStart | ThinkingDelta | ThinkingEnd
    | TextDelta
    | ToolCallTrace | ToolResultTrace
    | FinalOutput
)

# ── Providers ─────────────────────────────────────────────────────────────────

Provider = Literal[
    "openai",           # OpenAIChatModel  (+ <think> tags support)
    "openai-responses", # OpenAIResponsesModel (native reasoning_effort)
    "anthropic",        # Extended thinking  (claude-sonnet-4-5 and older)
    "anthropic-adaptive", # Adaptive thinking (claude-opus-4-6 and newer)
    "google",
    "groq",
    "xai",
    "openrouter",
    "bedrock-anthropic",
    "bedrock-openai",
]


def _build_model_and_settings(
    provider: Provider,
    model_name: str,
    enable_thinking: bool,
    thinking_budget: int,
    temperature: float | None,
    max_tokens: int | None,
) -> tuple[Any, ModelSettings | None]:
    base: dict[str, Any] = {}
    if temperature is not None:
        base["temperature"] = temperature
    if max_tokens is not None:
        base["max_tokens"] = max_tokens

    match provider:

        # ── OpenAI chat (uses <think> tag detection) ──────────────────────────
        case "openai":
            return OpenAIChatModel(model_name), ModelSettings(**base) if base else None

        # ── OpenAI Responses API (native reasoning) ───────────────────────────
        case "openai-responses":
            model = OpenAIResponsesModel(model_name)
            settings = OpenAIResponsesModelSettings(
                openai_reasoning_effort="high" if enable_thinking else "low",
                openai_reasoning_summary="detailed",
                **base,
            )
            return model, settings

        # ── Anthropic: extended thinking (claude-sonnet-4-5 and older) ────────
        case "anthropic":
            model = AnthropicModel(model_name)
            think: dict[str, Any] = (
                {"anthropic_thinking": {"type": "enabled", "budget_tokens": thinking_budget}}
                if enable_thinking else {}
            )
            settings = AnthropicModelSettings(**base, **think) if (base or think) else None
            return model, settings

        # ── Anthropic: adaptive thinking (claude-opus-4-6+) ───────────────────
        case "anthropic-adaptive":
            model = AnthropicModel(model_name)
            think = (
                {"anthropic_thinking": {"type": "adaptive"}, "anthropic_effort": "high"}
                if enable_thinking else {}
            )
            settings = AnthropicModelSettings(**base, **think) if (base or think) else None
            return model, settings

        # ── Google ────────────────────────────────────────────────────────────
        case "google":
            model = GoogleModel(model_name)
            think = (
                {"google_thinking_config": {"include_thoughts": True}}
                if enable_thinking else {}
            )
            settings = GoogleModelSettings(**base, **think) if (base or think) else None
            return model, settings

        # ── Groq ──────────────────────────────────────────────────────────────
        case "groq":
            model = GroqModel(model_name)
            think = (
                {"groq_reasoning_format": "parsed"}  # structured ThinkingPart
                if enable_thinking else {}
            )
            settings = GroqModelSettings(**base, **think) if (base or think) else None
            return model, settings

        # ── xAI ───────────────────────────────────────────────────────────────
        case "xai":
            model = XaiModel(model_name)
            think = (
                {"xai_include_encrypted_content": True}  # preserve thinking in history
                if enable_thinking else {}
            )
            settings = XaiModelSettings(**base, **think) if (base or think) else None
            return model, settings

        # ── OpenRouter ────────────────────────────────────────────────────────
        case "openrouter":
            model = OpenRouterModel(model_name)
            think = (
                {"openrouter_reasoning": {"effort": "high"}}
                if enable_thinking else {}
            )
            settings = OpenRouterModelSettings(**base, **think) if (base or think) else None
            return model, settings

        # ── AWS Bedrock (Claude) ───────────────────────────────────────────────
        case "bedrock-anthropic":
            model = BedrockConverseModel(model_name)
            think = (
                {"bedrock_additional_model_requests_fields": {
                    "thinking": {"type": "enabled", "budget_tokens": thinking_budget}
                }} if enable_thinking else {}
            )
            settings = BedrockModelSettings(**base, **think) if (base or think) else None
            return model, settings

        # ── AWS Bedrock (OpenAI-compatible) ───────────────────────────────────
        case "bedrock-openai":
            model = BedrockConverseModel(model_name)
            think = (
                {"bedrock_additional_model_requests_fields": {"reasoning_effort": "high"}}
                if enable_thinking else {}
            )
            settings = BedrockModelSettings(**base, **think) if (base or think) else None
            return model, settings

        case _:
            raise ValueError(f"Unknown provider: {provider!r}")


# ── Client ────────────────────────────────────────────────────────────────────

class PydanticAIClient:
    """
    Managed PydanticAI agent with:
    - Runtime add / remove tools
    - Hot-swappable provider + model
    - Streamed thinking traces (ThinkingStart / ThinkingDelta / ThinkingEnd)
    - Streamed tool call + result traces
    - Streamed text deltas
    - Persistent multi-turn history
    """

    def __init__(
        self,
        provider: Provider = "openai",
        model_name: str = "gpt-4o",
        system_prompt: str = "You are a helpful assistant.",
        enable_thinking: bool = False,
        thinking_budget: int = 8_000,   # tokens; Anthropic / Bedrock
        temperature: float | None = None,
        max_tokens: int | None = None,
        keep_history: bool = True,
    ):
        self._provider = provider
        self._model_name = model_name
        self._system_prompt = system_prompt
        self._enable_thinking = enable_thinking
        self._thinking_budget = thinking_budget
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._keep_history = keep_history

        self._tool_registry: dict[str, Callable] = {}
        self._history: list = []
        self._agent: Agent | None = None
        self._model_settings: ModelSettings | None = None
        self._dirty = True

    # ── Tool management ───────────────────────────────────────────────────────

    def add_tool(self, fn: Callable, name: str | None = None) -> "PydanticAIClient":
        self._tool_registry[name or fn.__name__] = fn
        self._dirty = True
        return self

    def remove_tool(self, name: str) -> "PydanticAIClient":
        self._tool_registry.pop(name, None)
        self._dirty = True
        return self

    def list_tools(self) -> list[str]:
        return list(self._tool_registry.keys())

    # ── Provider switching ────────────────────────────────────────────────────

    def set_model(
        self,
        provider: Provider,
        model_name: str,
        enable_thinking: bool | None = None,
        thinking_budget: int | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> "PydanticAIClient":
        self._provider = provider
        self._model_name = model_name
        if enable_thinking is not None:
            self._enable_thinking = enable_thinking
        if thinking_budget is not None:
            self._thinking_budget = thinking_budget
        if temperature is not None:
            self._temperature = temperature
        if max_tokens is not None:
            self._max_tokens = max_tokens
        self._dirty = True
        return self

    def clear_history(self) -> "PydanticAIClient":
        self._history = []
        return self

    # ── Agent builder ─────────────────────────────────────────────────────────

    def _ensure_agent(self) -> Agent:
        if not self._dirty and self._agent is not None:
            return self._agent

        model, settings = _build_model_and_settings(
            self._provider,
            self._model_name,
            self._enable_thinking,
            self._thinking_budget,
            self._temperature,
            self._max_tokens,
        )
        self._agent = Agent(
            model,
            tools=list(self._tool_registry.values()),
            system_prompt=self._system_prompt,
            model_settings=settings,
        )
        self._model_settings = settings
        self._dirty = False
        return self._agent

    # ── Core streaming ────────────────────────────────────────────────────────

    async def stream(
        self,
        user_prompt: str,
        deps: Any = None,
    ) -> AsyncGenerator[TraceEvent, None]:
        """
        Yields a stream of TraceEvents for a single turn:

          ThinkingStart(part_index)            — a thinking block opened
          ThinkingDelta(content, part_index)   — chunk of reasoning text
          ThinkingEnd(part_index)              — thinking block closed
          TextDelta(content)                   — assistant text chunk
          ToolCallTrace(name, args, id)        — tool about to run
          ToolResultTrace(id, content)         — tool returned
          FinalOutput(content)                 — complete answer
        """
        agent = self._ensure_agent()

        run_kwargs: dict[str, Any] = {}
        if deps is not None:
            run_kwargs["deps"] = deps
        if self._keep_history and self._history:
            run_kwargs["message_history"] = self._history

        async with agent.iter(user_prompt, **run_kwargs) as run:
            async for node in run:

                # ── Model is generating tokens ─────────────────────────────
                if Agent.is_model_request_node(node):
                    async with node.stream(run.ctx) as model_stream:
                        # Track open thinking parts to emit Start/End markers
                        thinking_open: dict[int, bool] = {}

                        async for event in model_stream:

                            if isinstance(event, PartStartEvent):
                                idx = event.index
                                part_type = type(event.part).__name__
                                if "Thinking" in part_type:
                                    # Always emit ThinkingStart before any delta
                                    thinking_open[idx] = True
                                    yield ThinkingStart(part_index=idx)
                                else:
                                    # Non-thinking part started — close open thinking blocks
                                    for tidx in list(thinking_open):
                                        yield ThinkingEnd(part_index=tidx)
                                        del thinking_open[tidx]

                            elif isinstance(event, PartDeltaEvent):
                                idx = event.index
                                delta = event.delta

                                # ── Thinking chunk ─────────────────────────
                                if isinstance(delta, ThinkingPartDelta):
                                    # Guard: emit ThinkingStart if PartStartEvent was missed
                                    if idx not in thinking_open:
                                        thinking_open[idx] = True
                                        yield ThinkingStart(part_index=idx)
                                    yield ThinkingDelta(
                                        content=delta.content_delta,
                                        part_index=idx,
                                    )

                                # ── Text chunk ─────────────────────────────
                                elif isinstance(delta, TextPartDelta):
                                    # Close any open thinking blocks before text
                                    for tidx in list(thinking_open):
                                        yield ThinkingEnd(part_index=tidx)
                                        del thinking_open[tidx]
                                    yield TextDelta(content=delta.content_delta)

                                # ── Tool-arg delta (partial JSON) ──────────
                                elif isinstance(delta, ToolCallPartDelta):
                                    pass  # full args arrive in CallToolsNode

                            elif isinstance(event, FinalResultEvent):
                                # Close any remaining thinking blocks
                                for tidx in list(thinking_open):
                                    yield ThinkingEnd(part_index=tidx)
                                thinking_open.clear()
                                # !! Do NOT break here — let the loop drain
                                # remaining TextPartDeltas naturally

                # ── Tools are executing ────────────────────────────────────
                elif Agent.is_call_tools_node(node):
                    async with node.stream(run.ctx) as tool_stream:
                        async for event in tool_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                yield ToolCallTrace(
                                    tool_name=event.part.tool_name,
                                    args=event.part.args,
                                    tool_call_id=event.part.tool_call_id,
                                )
                            elif isinstance(event, FunctionToolResultEvent):
                                yield ToolResultTrace(
                                    tool_call_id=event.tool_call_id,
                                    content=event.result.content,
                                )

                # ── Done ───────────────────────────────────────────────────
                elif Agent.is_end_node(node):
                    final = run.result.output if run.result else ""
                    yield FinalOutput(content=str(final))

        if self._keep_history and run.result:
            self._history = run.result.all_messages()

    # ── Pretty-print helper ───────────────────────────────────────────────────

    async def run(
        self,
        user_prompt: str,
        deps: Any = None,
        print_traces: bool = True,
    ) -> str:
        GREY   = "\033[2m"
        YELLOW = "\033[33m"
        CYAN   = "\033[36m"
        DIM    = "\033[90m"
        RESET  = "\033[0m"

        output = ""
        async for event in self.stream(user_prompt, deps=deps):
            if not print_traces:
                if isinstance(event, FinalOutput):
                    output = event.content
                continue

            match event:
                case ThinkingStart(part_index=i):
                    print(f"\n{GREY}┌─ [thinking block {i}]{RESET}", flush=True)
                case ThinkingDelta(content=c, part_index=_):
                    print(f"{GREY}{c}{RESET}", end="", flush=True)
                case ThinkingEnd(part_index=i):
                    print(f"\n{GREY}└─ [/thinking block {i}]{RESET}\n", flush=True)
                case TextDelta(content=c):
                    print(c, end="", flush=True)
                case ToolCallTrace(tool_name=n, args=a, tool_call_id=i):
                    print(f"\n{YELLOW}⚙ tool→  {n}({a})  [id={i}]{RESET}")
                case ToolResultTrace(tool_call_id=i, content=c):
                    print(f"{CYAN}✔ ←tool  [{i}]  {c}{RESET}")
                case FinalOutput(content=c):
                    output = c
                    print()

        return output


async def main():
    # ── Tools ─────────────────────────────────────────────────────────────────
    def multiply(a: int, b: int) -> int:
        """Multiply two integers."""
        return a * b

    def divide(a: float, b: float) -> float:
        """Divide two numbers."""
        return a / b

    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    def subtract(a: int, b: int) -> int:
        """Subtract two integers."""
        return a - b

    # ── Client — Anthropic with extended thinking ─────────────────────────────
    # claude-sonnet-4-5 natively emits ThinkingPartDelta events, so we get
    # ThinkingStart / ThinkingDelta / ThinkingEnd in the trace stream.
    client = PydanticAIClient(
        provider="anthropic",
        model_name="claude-sonnet-4-5",
        enable_thinking=True,
        thinking_budget=1024,
        max_tokens=10000,
        system_prompt=(
            "You are a precise math tutor. "
            "Think step-by-step before answering. "
            "Use the provided tools for every arithmetic operation — "
            "never compute in your head."
        ),
    )
    client.add_tool(multiply)
    client.add_tool(divide)
    client.add_tool(add)
    client.add_tool(subtract)

    # A multi-step question that forces thinking + multiple tool calls
    await client.run(
        "What is (144 × 12) ÷ 2 + 10 − 5?  "
        "Show each step and verify the final answer."
    )


# asyncio.run(main())
