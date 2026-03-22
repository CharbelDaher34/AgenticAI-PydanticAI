"""
PydanticAIClient — dynamic tools, swappable providers, full streaming traces.
Fixed: thinking traces now stream correctly via PartStartEvent tracking.

pip install pydantic-ai ddgs
"""
from dotenv import load_dotenv
load_dotenv()
import ast
import asyncio
import io
import operator as operator_mod
import textwrap
from collections.abc import AsyncGenerator, Callable
from datetime import datetime
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
from pydantic_ai.settings import ModelSettings
from ddgs import DDGS


# ── Default system instructions (app merges user-editable text from the UI) ─
DEFAULT_AGENT_SYSTEM_BASE = """You are a capable assistant. Use tools when they help.

Rules:
- Your final reply must fully answer the user: include every important fact, number, and conclusion—including everything you got from tools or reasoning. Do not omit requested details.
- After tool calls, synthesize tool outputs clearly in the answer text (do not assume the user only sees traces).
- In multi-turn chat, use earlier messages for context unless the user changes topic.
- Prefer concise wording, but never sacrifice completeness for brevity.
- Match the user's language when appropriate."""


def merge_system_prompt(user_extra: str) -> str:
    """Same merge as the web server: base + optional user text + today's date."""
    merged = DEFAULT_AGENT_SYSTEM_BASE.strip()
    extra = (user_extra or "").strip()
    if extra:
        merged = f"{merged}\n\n--- Additional instructions ---\n{extra}"
    if "Today's date:" not in merged:
        merged += f"\n\nToday's date: {datetime.now().strftime('%A, %B %d, %Y')}."
    return merged


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

TraceEvent = (
    ThinkingStart | ThinkingDelta | ThinkingEnd
    | TextDelta
    | ToolCallTrace | ToolResultTrace
)

# ── Providers ─────────────────────────────────────────────────────────────────

Provider = Literal[
    "openai",           # OpenAIChatModel  (+ <think> tags support)
    "openai-responses", # OpenAIResponsesModel (native reasoning_effort)
    "anthropic",        # Extended thinking  (claude-sonnet-4-5 and older)
    "anthropic-adaptive", # Adaptive thinking (claude-opus-4-6 and newer)
    "google",
    "groq",
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
                                    # Emit any initial text already on the part
                                    initial = getattr(event.part, "content", None) or ""
                                    if initial:
                                        yield TextDelta(content=initial)

                            elif isinstance(event, PartDeltaEvent):
                                idx = event.index
                                delta = event.delta

                                # ── Thinking chunk ─────────────────────────
                                if isinstance(delta, ThinkingPartDelta):
                                    # Guard: emit ThinkingStart if PartStartEvent was missed
                                    if idx not in thinking_open:
                                        thinking_open[idx] = True
                                        yield ThinkingStart(part_index=idx)
                                    chunk = delta.content_delta
                                    if chunk is None:
                                        chunk = ""
                                    yield ThinkingDelta(
                                        content=chunk,
                                        part_index=idx,
                                    )

                                # ── Text chunk ─────────────────────────────
                                elif isinstance(delta, TextPartDelta):
                                    # Close any open thinking blocks before text
                                    for tidx in list(thinking_open):
                                        yield ThinkingEnd(part_index=tidx)
                                        del thinking_open[tidx]
                                    chunk = delta.content_delta
                                    if chunk is None:
                                        chunk = ""
                                    yield TextDelta(content=chunk)

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
                    pass

            if self._keep_history:
                # Snapshot inside the context: after pydantic-ai 1.x, `run.result` may be None
                # after __aexit__, but `AgentRun.all_messages()` still reflects the full turn.
                self._history = list(run.all_messages())

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

        chunks: list[str] = []
        async for event in self.stream(user_prompt, deps=deps):
            if isinstance(event, TextDelta):
                chunks.append(event.content)

            if not print_traces:
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

        if print_traces:
            print()
        return "".join(chunks)


# ── Default demo tools (async + small delays so traces show real work) ───────

_MATH_BINOPS: dict[type, Any] = {
    ast.Add: operator_mod.add,
    ast.Sub: operator_mod.sub,
    ast.Mult: operator_mod.mul,
    ast.Div: operator_mod.truediv,
    ast.FloorDiv: operator_mod.floordiv,
    ast.Mod: operator_mod.mod,
    ast.Pow: operator_mod.pow,
}
_MATH_UNARY: dict[type, Any] = {
    ast.UAdd: operator_mod.pos,
    ast.USub: operator_mod.neg,
}


def _eval_math_ast(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _eval_math_ast(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("only numeric constants are allowed")
        return node.value
    if isinstance(node, ast.UnaryOp):
        op_t = type(node.op)
        if op_t not in _MATH_UNARY:
            raise ValueError("unsupported unary operator")
        return _MATH_UNARY[op_t](_eval_math_ast(node.operand))
    if isinstance(node, ast.BinOp):
        op_t = type(node.op)
        if op_t not in _MATH_BINOPS:
            raise ValueError("unsupported binary operator")
        return _MATH_BINOPS[op_t](_eval_math_ast(node.left), _eval_math_ast(node.right))
    raise ValueError("unsupported expression (use numbers and + - * / // % ** only)")


async def search_web(query: str) -> str:
    """Search the web via DuckDuckGo text search (titles, href, body)."""
    await asyncio.sleep(1.0)

    def _ddg_text_fetch() -> list[dict[str, Any]]:
        search_query = query.strip()
        with DDGS() as ddgs:
            rows = ddgs.text(
                search_query,
                region="wt-wt",
                safesearch="moderate",
                max_results=1,
            )
        return list(rows) if rows else []

    try:
        results = await asyncio.to_thread(_ddg_text_fetch)
    except Exception as exc:
        return f"Search failed: {type(exc).__name__}: {exc}"
    if not results:
        return "No results found; try different keywords."
    lines: list[str] = []
    for idx, row in enumerate(results):
        title = str(row.get("title", ""))
        href = str(row.get("href", ""))
        body = str(row.get("body", ""))
        lines.append(f"Result {idx + 1}: {title}")
        lines.append(f"  URL: {href}")
        lines.append(f"  Body: {body}")
    return chr(10).join(lines)[:6000]


async def execute_python(code: str) -> str:
    """Run Python in a restricted environment (math + builtins; use print() for output)."""
    await asyncio.sleep(1.0)
    output_buf = io.StringIO()

    def safe_print(*args: Any, **kwargs: Any) -> None:
        kwargs.pop("file", None)
        print(*args, file=output_buf, **kwargs)

    safe_builtins: dict[str, Any] = {
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "chr": chr,
        "dict": dict,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "format": format,
        "int": int,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "pow": pow,
        "print": safe_print,
        "range": range,
        "repr": repr,
        "reversed": reversed,
        "round": round,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        "True": True,
        "False": False,
        "None": None,
    }
    import math

    namespace: dict[str, Any] = {"__builtins__": safe_builtins, "math": math}
    try:
        exec(textwrap.dedent(code), namespace, namespace)
    except Exception as exc:
        return f"Error: {type(exc).__name__}: {exc}"
    text_out = output_buf.getvalue().strip()
    if text_out:
        return text_out[:8000]
    return "(no printed output; use print(...) to show results)"


async def evaluate_math(expression: str) -> str:
    """Evaluate a single arithmetic expression (numbers, + - * / // % **, parentheses)."""
    await asyncio.sleep(0.65)
    expr = expression.strip()
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        return f"Syntax error: {exc}"
    try:
        value = _eval_math_ast(tree)
        return repr(value)
    except Exception as exc:
        return f"Error: {type(exc).__name__}: {exc}"


async def main():
    # ── Client — Anthropic with extended thinking ─────────────────────────────
    # claude-sonnet-4-5 natively emits ThinkingPartDelta events, so we get
    # ThinkingStart / ThinkingDelta / ThinkingEnd in the trace stream.
    client = PydanticAIClient(
        provider="anthropic",
        model_name="claude-sonnet-4-5",
        enable_thinking=True,
        thinking_budget=8000,
        max_tokens=32000,
        system_prompt=merge_system_prompt(
            "Use search_web for external facts, evaluate_math for arithmetic, "
            "execute_python for code (math available; use print). Wait for tool results."
        ),
    )
    client.add_tool(search_web)
    client.add_tool(execute_python)
    client.add_tool(evaluate_math)

    await client.run(
        "When was Python 3.0 first released? Use search_web. "
        "Then use evaluate_math to compute (42 ** 2 - 100) / 11. "
        "Then use execute_python to print 2**n for n from 0 through 6, one per line."
        "when you finish these tasks, think about food that matches today's date and search the web for recipe on how to do it"
    )


if __name__ == "__main__":
    asyncio.run(main())