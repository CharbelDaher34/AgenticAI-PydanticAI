# `pydantic_ai.capabilities`

### AbstractCapability

Bases: `ABC`, `Generic[AgentDepsT]`

Abstract base class for agent capabilities.

A capability is a reusable, composable unit of agent behavior that can provide instructions, model settings, tools, and request/response hooks.

Lifecycle: capabilities are passed to an Agent at construction time, where most `get_*` methods are called to collect static configuration (instructions, model settings, toolsets, builtin tools). The exception is get_wrapper_toolset, which is called per-run during toolset assembly. Then, on each model request during a run, the before_model_request and after_model_request hooks are called to allow dynamic adjustments.

See the [capabilities documentation](https://ai.pydantic.dev/api/capabilities/index.md) for built-in capabilities.

get_serialization_name and from_spec support YAML/JSON specs (via Agent.from_spec); they have sensible defaults and typically don't need to be overridden.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
@dataclass
class AbstractCapability(ABC, Generic[AgentDepsT]):
    """Abstract base class for agent capabilities.

    A capability is a reusable, composable unit of agent behavior that can provide
    instructions, model settings, tools, and request/response hooks.

    Lifecycle: capabilities are passed to an [`Agent`][pydantic_ai.Agent] at construction time, where
    most `get_*` methods are called to collect static configuration (instructions, model
    settings, toolsets, builtin tools). The exception is
    [`get_wrapper_toolset`][pydantic_ai.capabilities.AbstractCapability.get_wrapper_toolset],
    which is called per-run during toolset assembly. Then, on each model request during a
    run, the [`before_model_request`][pydantic_ai.capabilities.AbstractCapability.before_model_request]
    and [`after_model_request`][pydantic_ai.capabilities.AbstractCapability.after_model_request]
    hooks are called to allow dynamic adjustments.

    See the [capabilities documentation](capabilities.md) for built-in capabilities.

    [`get_serialization_name`][pydantic_ai.capabilities.AbstractCapability.get_serialization_name]
    and [`from_spec`][pydantic_ai.capabilities.AbstractCapability.from_spec] support
    YAML/JSON specs (via [`Agent.from_spec`][pydantic_ai.Agent.from_spec]); they have
    sensible defaults and typically don't need to be overridden.
    """

    @property
    def has_wrap_node_run(self) -> bool:
        """Whether this capability (or any sub-capability) overrides wrap_node_run."""
        return type(self).wrap_node_run is not AbstractCapability.wrap_node_run

    @classmethod
    def get_serialization_name(cls) -> str | None:
        """Return the name used for spec serialization (CamelCase class name by default).

        Return None to opt out of spec-based construction.
        """
        return cls.__name__

    @classmethod
    def from_spec(cls, *args: Any, **kwargs: Any) -> AbstractCapability[Any]:
        """Create from spec arguments. Default: `cls(*args, **kwargs)`.

        Override when `__init__` takes non-serializable types.
        """
        return cls(*args, **kwargs)

    async def for_run(self, ctx: RunContext[AgentDepsT]) -> AbstractCapability[AgentDepsT]:
        """Return the capability instance to use for this agent run.

        Called once per run, before `get_*()` re-extraction and before any hooks fire.
        Override to return a fresh instance for per-run state isolation.
        Default: return `self` (shared across runs).
        """
        return self

    def get_instructions(self) -> AgentInstructions[AgentDepsT] | None:
        """Return instructions to include in the system prompt, or None.

        This method is called once at agent construction time. To get dynamic
        per-request behavior, return a callable that receives
        [`RunContext`][pydantic_ai.tools.RunContext] or a
        [`TemplateStr`][pydantic_ai.TemplateStr] — not a dynamic string.
        """
        return None

    def get_model_settings(self) -> AgentModelSettings[AgentDepsT] | None:
        """Return model settings to merge into the agent's defaults, or None.

        This method is called once at agent construction time. Return a static
        `ModelSettings` dict when the settings don't change between requests.
        Return a callable that receives [`RunContext`][pydantic_ai.tools.RunContext]
        when settings need to vary per step (e.g. based on `ctx.run_step` or `ctx.deps`).

        When the callable is invoked, `ctx.model_settings` contains the merged
        result of all layers resolved before this capability (model defaults and
        agent-level settings). The returned dict is merged on top of that.
        """
        return None

    def get_toolset(self) -> AgentToolset[AgentDepsT] | None:
        """Return a toolset to register with the agent, or None."""
        return None

    def get_builtin_tools(self) -> Sequence[AgentBuiltinTool[AgentDepsT]]:
        """Return builtin tools to register with the agent."""
        return []

    def get_wrapper_toolset(self, toolset: AbstractToolset[AgentDepsT]) -> AbstractToolset[AgentDepsT] | None:
        """Wrap the agent's assembled toolset, or return None to leave it unchanged.

        Called per-run with the combined non-output toolset (after agent-level
        [`prepare_tools`][pydantic_ai.tools.ToolsPrepareFunc] wrapping).
        Output tools are added separately and are not included.

        Unlike the other `get_*` methods which are called once at agent construction,
        this is called each run (after [`for_run`][pydantic_ai.capabilities.AbstractCapability.for_run]).
        When multiple capabilities provide wrappers, each receives the already-wrapped
        toolset from earlier capabilities (first capability wraps innermost).

        Use this to apply cross-cutting toolset wrappers like
        [`PreparedToolset`][pydantic_ai.toolsets.PreparedToolset],
        [`FilteredToolset`][pydantic_ai.toolsets.FilteredToolset],
        or custom [`WrapperToolset`][pydantic_ai.toolsets.WrapperToolset] subclasses.
        """
        return None

    # --- Tool preparation hook ---

    async def prepare_tools(
        self,
        ctx: RunContext[AgentDepsT],
        tool_defs: list[ToolDefinition],
    ) -> list[ToolDefinition]:
        """Filter or modify tool definitions visible to the model for this step.

        The list contains all tool kinds (function, output, unapproved) distinguished
        by [`tool_def.kind`][pydantic_ai.tools.ToolDefinition.kind]. Return a filtered
        or modified list. Called after the agent-level
        [`prepare_tools`][pydantic_ai.tools.ToolsPrepareFunc] has already run.
        """
        return tool_defs

    # --- Run lifecycle hooks ---

    async def before_run(
        self,
        ctx: RunContext[AgentDepsT],
    ) -> None:
        """Called before the agent run starts. Observe-only; use wrap_run for modification."""

    async def after_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        result: AgentRunResult[Any],
    ) -> AgentRunResult[Any]:
        """Called after the agent run completes. Can modify the result."""
        return result

    async def wrap_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        handler: WrapRunHandler,
    ) -> AgentRunResult[Any]:
        """Wraps the entire agent run. `handler()` executes the run.

        If `handler()` raises and this method catches the exception and
        returns a result instead, the error is suppressed and the recovery
        result is used.

        If this method does not call `handler()` (short-circuit), the run
        is skipped and the returned result is used directly.

        Note: if the caller cancels the run (e.g. by breaking out of an
        `iter()` loop), this method receives an :class:`asyncio.CancelledError`.
        Implementations that hold resources should handle cleanup accordingly.
        """
        return await handler()

    async def on_run_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        error: BaseException,
    ) -> AgentRunResult[Any]:
        """Called when the agent run fails with an exception.

        This is the error counterpart to
        [`after_run`][pydantic_ai.capabilities.AbstractCapability.after_run]:
        while `after_run` is called on success, `on_run_error` is called on
        failure (after [`wrap_run`][pydantic_ai.capabilities.AbstractCapability.wrap_run]
        has had its chance to recover).

        **Raise** the original `error` (or a different exception) to propagate it.
        **Return** an [`AgentRunResult`][pydantic_ai.run.AgentRunResult] to suppress
        the error and recover the run.

        Not called for `GeneratorExit` or `KeyboardInterrupt`.
        """
        raise error

    # --- Node run lifecycle hooks ---

    async def before_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
    ) -> AgentNode[AgentDepsT]:
        """Called before each graph node executes. Can observe or replace the node."""
        return node

    async def after_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
        result: NodeResult[AgentDepsT],
    ) -> NodeResult[AgentDepsT]:
        """Called after each graph node succeeds. Can modify the result (next node or `End`)."""
        return result

    async def wrap_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
        handler: WrapNodeRunHandler[AgentDepsT],
    ) -> NodeResult[AgentDepsT]:
        """Wraps execution of each agent graph node (run step).

        Called for every node in the agent graph (`UserPromptNode`,
        `ModelRequestNode`, `CallToolsNode`).  `handler(node)` executes
        the node and returns the next node (or `End`).

        Override to inspect or modify nodes before execution, inspect or modify
        the returned next node, call `handler` multiple times (retry), or
        return a different node to redirect graph progression.

        Note: this hook fires when using [`agent.run()`][pydantic_ai.Agent.run],
        [`agent.run_stream()`][pydantic_ai.Agent.run_stream], and when manually driving
        an [`agent.iter()`][pydantic_ai.Agent.iter] run with
        [`next()`][pydantic_ai.result.AgentRun.next], but it does **not** fire when
        iterating over the run with bare `async for` (which yields stream events, not
        node results).

        When using `agent.run()` with `event_stream_handler`, the handler wraps both
        streaming and graph advancement (i.e. the model call happens inside the wrapper).
        When using `agent.run_stream()`, the handler wraps only graph advancement — streaming
        happens before the wrapper because `run_stream()` must yield the stream to the caller
        while the stream context is still open, which cannot happen from inside a callback.
        """
        return await handler(node)

    async def on_node_run_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
        error: Exception,
    ) -> NodeResult[AgentDepsT]:
        """Called when a graph node fails with an exception.

        This is the error counterpart to
        [`after_node_run`][pydantic_ai.capabilities.AbstractCapability.after_node_run].

        **Raise** the original `error` (or a different exception) to propagate it.
        **Return** a next node or `End` to recover and continue the graph.

        Useful for recovering from
        [`UnexpectedModelBehavior`][pydantic_ai.exceptions.UnexpectedModelBehavior]
        by redirecting to a different node (e.g. retry with different model settings).
        """
        raise error

    # --- Event stream hook ---

    async def wrap_run_event_stream(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        stream: AsyncIterable[AgentStreamEvent],
    ) -> AsyncIterable[AgentStreamEvent]:
        """Wraps the event stream for a streamed node. Can observe or transform events."""
        async for event in stream:
            yield event

    # --- Model request lifecycle hooks ---

    async def before_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        request_context: ModelRequestContext,
    ) -> ModelRequestContext:
        """Called before each model request. Can modify messages, settings, and parameters."""
        return request_context

    async def after_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        response: ModelResponse,
    ) -> ModelResponse:
        """Called after each model response. Can modify the response before further processing.

        Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to reject the response and
        ask the model to try again. The original response is still appended to message history
        so the model can see what it said. Retries count against `max_result_retries`.
        """
        return response

    async def wrap_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        handler: WrapModelRequestHandler,
    ) -> ModelResponse:
        """Wraps the model request. handler() calls the model.

        Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to skip `on_model_request_error`
        and directly retry the model request with a retry prompt. If the handler was called,
        the model response is preserved in history for context (same as `after_model_request`).
        """
        return await handler(request_context)

    async def on_model_request_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        error: Exception,
    ) -> ModelResponse:
        """Called when a model request fails with an exception.

        This is the error counterpart to
        [`after_model_request`][pydantic_ai.capabilities.AbstractCapability.after_model_request].

        **Raise** the original `error` (or a different exception) to propagate it.
        **Return** a [`ModelResponse`][pydantic_ai.messages.ModelResponse] to suppress
        the error and use the response as if the model call succeeded.
        **Raise** [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to retry the model request
        with a retry prompt instead of recovering or propagating.

        Not called for [`SkipModelRequest`][pydantic_ai.exceptions.SkipModelRequest]
        or [`ModelRetry`][pydantic_ai.exceptions.ModelRetry].
        """
        raise error

    # --- Tool validate lifecycle hooks ---

    async def before_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: RawToolArgs,
    ) -> RawToolArgs:
        """Modify raw args before validation.

        Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to skip validation and
        ask the model to redo the tool call.
        """
        return args

    async def after_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
    ) -> ValidatedToolArgs:
        """Modify validated args. Called only on successful validation.

        Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to reject the validated args
        and ask the model to redo the tool call.
        """
        return args

    async def wrap_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: RawToolArgs,
        handler: WrapToolValidateHandler,
    ) -> ValidatedToolArgs:
        """Wraps tool argument validation. handler() runs the validation."""
        return await handler(args)

    async def on_tool_validate_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: RawToolArgs,
        error: ValidationError | ModelRetry,
    ) -> ValidatedToolArgs:
        """Called when tool argument validation fails.

        This is the error counterpart to
        [`after_tool_validate`][pydantic_ai.capabilities.AbstractCapability.after_tool_validate].
        Fires for [`ValidationError`][pydantic.ValidationError] (schema mismatch) and
        [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] (custom validator rejection).

        **Raise** the original `error` (or a different exception) to propagate it.
        **Return** validated args to suppress the error and continue as if validation passed.

        Not called for [`SkipToolValidation`][pydantic_ai.exceptions.SkipToolValidation].
        """
        raise error

    # --- Tool execute lifecycle hooks ---

    async def before_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
    ) -> ValidatedToolArgs:
        """Modify validated args before execution.

        Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to skip execution and
        ask the model to redo the tool call.
        """
        return args

    async def after_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
        result: Any,
    ) -> Any:
        """Modify result after execution.

        Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to reject the tool result
        and ask the model to redo the tool call.
        """
        return result

    async def wrap_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
        handler: WrapToolExecuteHandler,
    ) -> Any:
        """Wraps tool execution. handler() runs the tool."""
        return await handler(args)

    async def on_tool_execute_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
        error: Exception,
    ) -> Any:
        """Called when tool execution fails with an exception.

        This is the error counterpart to
        [`after_tool_execute`][pydantic_ai.capabilities.AbstractCapability.after_tool_execute].

        **Raise** the original `error` (or a different exception) to propagate it.
        **Return** any value to suppress the error and use it as the tool result.
        **Raise** [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to ask the model to
        redo the tool call instead of recovering or propagating.

        Not called for control flow exceptions
        ([`SkipToolExecution`][pydantic_ai.exceptions.SkipToolExecution],
        [`CallDeferred`][pydantic_ai.exceptions.CallDeferred],
        [`ApprovalRequired`][pydantic_ai.exceptions.ApprovalRequired])
        or retry signals ([`ToolRetryError`][pydantic_ai.exceptions.ToolRetryError]
        from [`ModelRetry`][pydantic_ai.exceptions.ModelRetry]).
        Use [`wrap_tool_execute`][pydantic_ai.capabilities.AbstractCapability.wrap_tool_execute]
        to intercept retries.
        """
        raise error

    # --- Convenience methods ---

    def prefix_tools(self, prefix: str) -> PrefixTools[AgentDepsT]:
        """Returns a new capability that wraps this one and prefixes its tool names.

        Only this capability's tools are prefixed; other agent tools are unaffected.
        """
        from .prefix_tools import PrefixTools

        return PrefixTools(wrapped=self, prefix=prefix)
```

#### has_wrap_node_run

```python
has_wrap_node_run: bool
```

Whether this capability (or any sub-capability) overrides wrap_node_run.

#### get_serialization_name

```python
get_serialization_name() -> str | None
```

Return the name used for spec serialization (CamelCase class name by default).

Return None to opt out of spec-based construction.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
@classmethod
def get_serialization_name(cls) -> str | None:
    """Return the name used for spec serialization (CamelCase class name by default).

    Return None to opt out of spec-based construction.
    """
    return cls.__name__
```

#### from_spec

```python
from_spec(
    *args: Any, **kwargs: Any
) -> AbstractCapability[Any]
```

Create from spec arguments. Default: `cls(*args, **kwargs)`.

Override when `__init__` takes non-serializable types.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
@classmethod
def from_spec(cls, *args: Any, **kwargs: Any) -> AbstractCapability[Any]:
    """Create from spec arguments. Default: `cls(*args, **kwargs)`.

    Override when `__init__` takes non-serializable types.
    """
    return cls(*args, **kwargs)
```

#### for_run

```python
for_run(
    ctx: RunContext[AgentDepsT],
) -> AbstractCapability[AgentDepsT]
```

Return the capability instance to use for this agent run.

Called once per run, before `get_*()` re-extraction and before any hooks fire. Override to return a fresh instance for per-run state isolation. Default: return `self` (shared across runs).

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def for_run(self, ctx: RunContext[AgentDepsT]) -> AbstractCapability[AgentDepsT]:
    """Return the capability instance to use for this agent run.

    Called once per run, before `get_*()` re-extraction and before any hooks fire.
    Override to return a fresh instance for per-run state isolation.
    Default: return `self` (shared across runs).
    """
    return self
```

#### get_instructions

```python
get_instructions() -> AgentInstructions[AgentDepsT] | None
```

Return instructions to include in the system prompt, or None.

This method is called once at agent construction time. To get dynamic per-request behavior, return a callable that receives RunContext or a TemplateStr — not a dynamic string.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
def get_instructions(self) -> AgentInstructions[AgentDepsT] | None:
    """Return instructions to include in the system prompt, or None.

    This method is called once at agent construction time. To get dynamic
    per-request behavior, return a callable that receives
    [`RunContext`][pydantic_ai.tools.RunContext] or a
    [`TemplateStr`][pydantic_ai.TemplateStr] — not a dynamic string.
    """
    return None
```

#### get_model_settings

```python
get_model_settings() -> (
    AgentModelSettings[AgentDepsT] | None
)
```

Return model settings to merge into the agent's defaults, or None.

This method is called once at agent construction time. Return a static `ModelSettings` dict when the settings don't change between requests. Return a callable that receives RunContext when settings need to vary per step (e.g. based on `ctx.run_step` or `ctx.deps`).

When the callable is invoked, `ctx.model_settings` contains the merged result of all layers resolved before this capability (model defaults and agent-level settings). The returned dict is merged on top of that.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
def get_model_settings(self) -> AgentModelSettings[AgentDepsT] | None:
    """Return model settings to merge into the agent's defaults, or None.

    This method is called once at agent construction time. Return a static
    `ModelSettings` dict when the settings don't change between requests.
    Return a callable that receives [`RunContext`][pydantic_ai.tools.RunContext]
    when settings need to vary per step (e.g. based on `ctx.run_step` or `ctx.deps`).

    When the callable is invoked, `ctx.model_settings` contains the merged
    result of all layers resolved before this capability (model defaults and
    agent-level settings). The returned dict is merged on top of that.
    """
    return None
```

#### get_toolset

```python
get_toolset() -> AgentToolset[AgentDepsT] | None
```

Return a toolset to register with the agent, or None.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
def get_toolset(self) -> AgentToolset[AgentDepsT] | None:
    """Return a toolset to register with the agent, or None."""
    return None
```

#### get_builtin_tools

```python
get_builtin_tools() -> (
    Sequence[AgentBuiltinTool[AgentDepsT]]
)
```

Return builtin tools to register with the agent.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
def get_builtin_tools(self) -> Sequence[AgentBuiltinTool[AgentDepsT]]:
    """Return builtin tools to register with the agent."""
    return []
```

#### get_wrapper_toolset

```python
get_wrapper_toolset(
    toolset: AbstractToolset[AgentDepsT],
) -> AbstractToolset[AgentDepsT] | None
```

Wrap the agent's assembled toolset, or return None to leave it unchanged.

Called per-run with the combined non-output toolset (after agent-level prepare_tools wrapping). Output tools are added separately and are not included.

Unlike the other `get_*` methods which are called once at agent construction, this is called each run (after for_run). When multiple capabilities provide wrappers, each receives the already-wrapped toolset from earlier capabilities (first capability wraps innermost).

Use this to apply cross-cutting toolset wrappers like PreparedToolset, FilteredToolset, or custom WrapperToolset subclasses.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
def get_wrapper_toolset(self, toolset: AbstractToolset[AgentDepsT]) -> AbstractToolset[AgentDepsT] | None:
    """Wrap the agent's assembled toolset, or return None to leave it unchanged.

    Called per-run with the combined non-output toolset (after agent-level
    [`prepare_tools`][pydantic_ai.tools.ToolsPrepareFunc] wrapping).
    Output tools are added separately and are not included.

    Unlike the other `get_*` methods which are called once at agent construction,
    this is called each run (after [`for_run`][pydantic_ai.capabilities.AbstractCapability.for_run]).
    When multiple capabilities provide wrappers, each receives the already-wrapped
    toolset from earlier capabilities (first capability wraps innermost).

    Use this to apply cross-cutting toolset wrappers like
    [`PreparedToolset`][pydantic_ai.toolsets.PreparedToolset],
    [`FilteredToolset`][pydantic_ai.toolsets.FilteredToolset],
    or custom [`WrapperToolset`][pydantic_ai.toolsets.WrapperToolset] subclasses.
    """
    return None
```

#### prepare_tools

```python
prepare_tools(
    ctx: RunContext[AgentDepsT],
    tool_defs: list[ToolDefinition],
) -> list[ToolDefinition]
```

Filter or modify tool definitions visible to the model for this step.

The list contains all tool kinds (function, output, unapproved) distinguished by tool_def.kind. Return a filtered or modified list. Called after the agent-level prepare_tools has already run.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def prepare_tools(
    self,
    ctx: RunContext[AgentDepsT],
    tool_defs: list[ToolDefinition],
) -> list[ToolDefinition]:
    """Filter or modify tool definitions visible to the model for this step.

    The list contains all tool kinds (function, output, unapproved) distinguished
    by [`tool_def.kind`][pydantic_ai.tools.ToolDefinition.kind]. Return a filtered
    or modified list. Called after the agent-level
    [`prepare_tools`][pydantic_ai.tools.ToolsPrepareFunc] has already run.
    """
    return tool_defs
```

#### before_run

```python
before_run(ctx: RunContext[AgentDepsT]) -> None
```

Called before the agent run starts. Observe-only; use wrap_run for modification.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def before_run(
    self,
    ctx: RunContext[AgentDepsT],
) -> None:
    """Called before the agent run starts. Observe-only; use wrap_run for modification."""
```

#### after_run

```python
after_run(
    ctx: RunContext[AgentDepsT],
    *,
    result: AgentRunResult[Any]
) -> AgentRunResult[Any]
```

Called after the agent run completes. Can modify the result.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def after_run(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    result: AgentRunResult[Any],
) -> AgentRunResult[Any]:
    """Called after the agent run completes. Can modify the result."""
    return result
```

#### wrap_run

```python
wrap_run(
    ctx: RunContext[AgentDepsT], *, handler: WrapRunHandler
) -> AgentRunResult[Any]
```

Wraps the entire agent run. `handler()` executes the run.

If `handler()` raises and this method catches the exception and returns a result instead, the error is suppressed and the recovery result is used.

If this method does not call `handler()` (short-circuit), the run is skipped and the returned result is used directly.

Note: if the caller cancels the run (e.g. by breaking out of an `iter()` loop), this method receives an :class:`asyncio.CancelledError`. Implementations that hold resources should handle cleanup accordingly.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def wrap_run(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    handler: WrapRunHandler,
) -> AgentRunResult[Any]:
    """Wraps the entire agent run. `handler()` executes the run.

    If `handler()` raises and this method catches the exception and
    returns a result instead, the error is suppressed and the recovery
    result is used.

    If this method does not call `handler()` (short-circuit), the run
    is skipped and the returned result is used directly.

    Note: if the caller cancels the run (e.g. by breaking out of an
    `iter()` loop), this method receives an :class:`asyncio.CancelledError`.
    Implementations that hold resources should handle cleanup accordingly.
    """
    return await handler()
```

#### on_run_error

```python
on_run_error(
    ctx: RunContext[AgentDepsT], *, error: BaseException
) -> AgentRunResult[Any]
```

Called when the agent run fails with an exception.

This is the error counterpart to after_run: while `after_run` is called on success, `on_run_error` is called on failure (after wrap_run has had its chance to recover).

**Raise** the original `error` (or a different exception) to propagate it. **Return** an AgentRunResult to suppress the error and recover the run.

Not called for `GeneratorExit` or `KeyboardInterrupt`.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def on_run_error(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    error: BaseException,
) -> AgentRunResult[Any]:
    """Called when the agent run fails with an exception.

    This is the error counterpart to
    [`after_run`][pydantic_ai.capabilities.AbstractCapability.after_run]:
    while `after_run` is called on success, `on_run_error` is called on
    failure (after [`wrap_run`][pydantic_ai.capabilities.AbstractCapability.wrap_run]
    has had its chance to recover).

    **Raise** the original `error` (or a different exception) to propagate it.
    **Return** an [`AgentRunResult`][pydantic_ai.run.AgentRunResult] to suppress
    the error and recover the run.

    Not called for `GeneratorExit` or `KeyboardInterrupt`.
    """
    raise error
```

#### before_node_run

```python
before_node_run(
    ctx: RunContext[AgentDepsT],
    *,
    node: AgentNode[AgentDepsT]
) -> AgentNode[AgentDepsT]
```

Called before each graph node executes. Can observe or replace the node.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def before_node_run(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    node: AgentNode[AgentDepsT],
) -> AgentNode[AgentDepsT]:
    """Called before each graph node executes. Can observe or replace the node."""
    return node
```

#### after_node_run

```python
after_node_run(
    ctx: RunContext[AgentDepsT],
    *,
    node: AgentNode[AgentDepsT],
    result: NodeResult[AgentDepsT]
) -> NodeResult[AgentDepsT]
```

Called after each graph node succeeds. Can modify the result (next node or `End`).

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def after_node_run(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    node: AgentNode[AgentDepsT],
    result: NodeResult[AgentDepsT],
) -> NodeResult[AgentDepsT]:
    """Called after each graph node succeeds. Can modify the result (next node or `End`)."""
    return result
```

#### wrap_node_run

```python
wrap_node_run(
    ctx: RunContext[AgentDepsT],
    *,
    node: AgentNode[AgentDepsT],
    handler: WrapNodeRunHandler[AgentDepsT]
) -> NodeResult[AgentDepsT]
```

Wraps execution of each agent graph node (run step).

Called for every node in the agent graph (`UserPromptNode`, `ModelRequestNode`, `CallToolsNode`). `handler(node)` executes the node and returns the next node (or `End`).

Override to inspect or modify nodes before execution, inspect or modify the returned next node, call `handler` multiple times (retry), or return a different node to redirect graph progression.

Note: this hook fires when using agent.run(), agent.run_stream(), and when manually driving an agent.iter() run with next(), but it does **not** fire when iterating over the run with bare `async for` (which yields stream events, not node results).

When using `agent.run()` with `event_stream_handler`, the handler wraps both streaming and graph advancement (i.e. the model call happens inside the wrapper). When using `agent.run_stream()`, the handler wraps only graph advancement — streaming happens before the wrapper because `run_stream()` must yield the stream to the caller while the stream context is still open, which cannot happen from inside a callback.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def wrap_node_run(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    node: AgentNode[AgentDepsT],
    handler: WrapNodeRunHandler[AgentDepsT],
) -> NodeResult[AgentDepsT]:
    """Wraps execution of each agent graph node (run step).

    Called for every node in the agent graph (`UserPromptNode`,
    `ModelRequestNode`, `CallToolsNode`).  `handler(node)` executes
    the node and returns the next node (or `End`).

    Override to inspect or modify nodes before execution, inspect or modify
    the returned next node, call `handler` multiple times (retry), or
    return a different node to redirect graph progression.

    Note: this hook fires when using [`agent.run()`][pydantic_ai.Agent.run],
    [`agent.run_stream()`][pydantic_ai.Agent.run_stream], and when manually driving
    an [`agent.iter()`][pydantic_ai.Agent.iter] run with
    [`next()`][pydantic_ai.result.AgentRun.next], but it does **not** fire when
    iterating over the run with bare `async for` (which yields stream events, not
    node results).

    When using `agent.run()` with `event_stream_handler`, the handler wraps both
    streaming and graph advancement (i.e. the model call happens inside the wrapper).
    When using `agent.run_stream()`, the handler wraps only graph advancement — streaming
    happens before the wrapper because `run_stream()` must yield the stream to the caller
    while the stream context is still open, which cannot happen from inside a callback.
    """
    return await handler(node)
```

#### on_node_run_error

```python
on_node_run_error(
    ctx: RunContext[AgentDepsT],
    *,
    node: AgentNode[AgentDepsT],
    error: Exception
) -> NodeResult[AgentDepsT]
```

Called when a graph node fails with an exception.

This is the error counterpart to after_node_run.

**Raise** the original `error` (or a different exception) to propagate it. **Return** a next node or `End` to recover and continue the graph.

Useful for recovering from UnexpectedModelBehavior by redirecting to a different node (e.g. retry with different model settings).

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def on_node_run_error(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    node: AgentNode[AgentDepsT],
    error: Exception,
) -> NodeResult[AgentDepsT]:
    """Called when a graph node fails with an exception.

    This is the error counterpart to
    [`after_node_run`][pydantic_ai.capabilities.AbstractCapability.after_node_run].

    **Raise** the original `error` (or a different exception) to propagate it.
    **Return** a next node or `End` to recover and continue the graph.

    Useful for recovering from
    [`UnexpectedModelBehavior`][pydantic_ai.exceptions.UnexpectedModelBehavior]
    by redirecting to a different node (e.g. retry with different model settings).
    """
    raise error
```

#### wrap_run_event_stream

```python
wrap_run_event_stream(
    ctx: RunContext[AgentDepsT],
    *,
    stream: AsyncIterable[AgentStreamEvent]
) -> AsyncIterable[AgentStreamEvent]
```

Wraps the event stream for a streamed node. Can observe or transform events.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def wrap_run_event_stream(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    stream: AsyncIterable[AgentStreamEvent],
) -> AsyncIterable[AgentStreamEvent]:
    """Wraps the event stream for a streamed node. Can observe or transform events."""
    async for event in stream:
        yield event
```

#### before_model_request

```python
before_model_request(
    ctx: RunContext[AgentDepsT],
    request_context: ModelRequestContext,
) -> ModelRequestContext
```

Called before each model request. Can modify messages, settings, and parameters.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def before_model_request(
    self,
    ctx: RunContext[AgentDepsT],
    request_context: ModelRequestContext,
) -> ModelRequestContext:
    """Called before each model request. Can modify messages, settings, and parameters."""
    return request_context
```

#### after_model_request

```python
after_model_request(
    ctx: RunContext[AgentDepsT],
    *,
    request_context: ModelRequestContext,
    response: ModelResponse
) -> ModelResponse
```

Called after each model response. Can modify the response before further processing.

Raise ModelRetry to reject the response and ask the model to try again. The original response is still appended to message history so the model can see what it said. Retries count against `max_result_retries`.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def after_model_request(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    request_context: ModelRequestContext,
    response: ModelResponse,
) -> ModelResponse:
    """Called after each model response. Can modify the response before further processing.

    Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to reject the response and
    ask the model to try again. The original response is still appended to message history
    so the model can see what it said. Retries count against `max_result_retries`.
    """
    return response
```

#### wrap_model_request

```python
wrap_model_request(
    ctx: RunContext[AgentDepsT],
    *,
    request_context: ModelRequestContext,
    handler: WrapModelRequestHandler
) -> ModelResponse
```

Wraps the model request. handler() calls the model.

Raise ModelRetry to skip `on_model_request_error` and directly retry the model request with a retry prompt. If the handler was called, the model response is preserved in history for context (same as `after_model_request`).

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def wrap_model_request(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    request_context: ModelRequestContext,
    handler: WrapModelRequestHandler,
) -> ModelResponse:
    """Wraps the model request. handler() calls the model.

    Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to skip `on_model_request_error`
    and directly retry the model request with a retry prompt. If the handler was called,
    the model response is preserved in history for context (same as `after_model_request`).
    """
    return await handler(request_context)
```

#### on_model_request_error

```python
on_model_request_error(
    ctx: RunContext[AgentDepsT],
    *,
    request_context: ModelRequestContext,
    error: Exception
) -> ModelResponse
```

Called when a model request fails with an exception.

This is the error counterpart to after_model_request.

**Raise** the original `error` (or a different exception) to propagate it. **Return** a ModelResponse to suppress the error and use the response as if the model call succeeded. **Raise** ModelRetry to retry the model request with a retry prompt instead of recovering or propagating.

Not called for SkipModelRequest or ModelRetry.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def on_model_request_error(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    request_context: ModelRequestContext,
    error: Exception,
) -> ModelResponse:
    """Called when a model request fails with an exception.

    This is the error counterpart to
    [`after_model_request`][pydantic_ai.capabilities.AbstractCapability.after_model_request].

    **Raise** the original `error` (or a different exception) to propagate it.
    **Return** a [`ModelResponse`][pydantic_ai.messages.ModelResponse] to suppress
    the error and use the response as if the model call succeeded.
    **Raise** [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to retry the model request
    with a retry prompt instead of recovering or propagating.

    Not called for [`SkipModelRequest`][pydantic_ai.exceptions.SkipModelRequest]
    or [`ModelRetry`][pydantic_ai.exceptions.ModelRetry].
    """
    raise error
```

#### before_tool_validate

```python
before_tool_validate(
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: RawToolArgs
) -> RawToolArgs
```

Modify raw args before validation.

Raise ModelRetry to skip validation and ask the model to redo the tool call.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def before_tool_validate(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: RawToolArgs,
) -> RawToolArgs:
    """Modify raw args before validation.

    Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to skip validation and
    ask the model to redo the tool call.
    """
    return args
```

#### after_tool_validate

```python
after_tool_validate(
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs
) -> ValidatedToolArgs
```

Modify validated args. Called only on successful validation.

Raise ModelRetry to reject the validated args and ask the model to redo the tool call.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def after_tool_validate(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs,
) -> ValidatedToolArgs:
    """Modify validated args. Called only on successful validation.

    Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to reject the validated args
    and ask the model to redo the tool call.
    """
    return args
```

#### wrap_tool_validate

```python
wrap_tool_validate(
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: RawToolArgs,
    handler: WrapToolValidateHandler
) -> ValidatedToolArgs
```

Wraps tool argument validation. handler() runs the validation.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def wrap_tool_validate(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: RawToolArgs,
    handler: WrapToolValidateHandler,
) -> ValidatedToolArgs:
    """Wraps tool argument validation. handler() runs the validation."""
    return await handler(args)
```

#### on_tool_validate_error

```python
on_tool_validate_error(
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: RawToolArgs,
    error: ValidationError | ModelRetry
) -> ValidatedToolArgs
```

Called when tool argument validation fails.

This is the error counterpart to after_tool_validate. Fires for ValidationError (schema mismatch) and ModelRetry (custom validator rejection).

**Raise** the original `error` (or a different exception) to propagate it. **Return** validated args to suppress the error and continue as if validation passed.

Not called for SkipToolValidation.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def on_tool_validate_error(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: RawToolArgs,
    error: ValidationError | ModelRetry,
) -> ValidatedToolArgs:
    """Called when tool argument validation fails.

    This is the error counterpart to
    [`after_tool_validate`][pydantic_ai.capabilities.AbstractCapability.after_tool_validate].
    Fires for [`ValidationError`][pydantic.ValidationError] (schema mismatch) and
    [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] (custom validator rejection).

    **Raise** the original `error` (or a different exception) to propagate it.
    **Return** validated args to suppress the error and continue as if validation passed.

    Not called for [`SkipToolValidation`][pydantic_ai.exceptions.SkipToolValidation].
    """
    raise error
```

#### before_tool_execute

```python
before_tool_execute(
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs
) -> ValidatedToolArgs
```

Modify validated args before execution.

Raise ModelRetry to skip execution and ask the model to redo the tool call.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def before_tool_execute(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs,
) -> ValidatedToolArgs:
    """Modify validated args before execution.

    Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to skip execution and
    ask the model to redo the tool call.
    """
    return args
```

#### after_tool_execute

```python
after_tool_execute(
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs,
    result: Any
) -> Any
```

Modify result after execution.

Raise ModelRetry to reject the tool result and ask the model to redo the tool call.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def after_tool_execute(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs,
    result: Any,
) -> Any:
    """Modify result after execution.

    Raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to reject the tool result
    and ask the model to redo the tool call.
    """
    return result
```

#### wrap_tool_execute

```python
wrap_tool_execute(
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs,
    handler: WrapToolExecuteHandler
) -> Any
```

Wraps tool execution. handler() runs the tool.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def wrap_tool_execute(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs,
    handler: WrapToolExecuteHandler,
) -> Any:
    """Wraps tool execution. handler() runs the tool."""
    return await handler(args)
```

#### on_tool_execute_error

```python
on_tool_execute_error(
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs,
    error: Exception
) -> Any
```

Called when tool execution fails with an exception.

This is the error counterpart to after_tool_execute.

**Raise** the original `error` (or a different exception) to propagate it. **Return** any value to suppress the error and use it as the tool result. **Raise** ModelRetry to ask the model to redo the tool call instead of recovering or propagating.

Not called for control flow exceptions (SkipToolExecution, CallDeferred, ApprovalRequired) or retry signals (ToolRetryError from ModelRetry). Use wrap_tool_execute to intercept retries.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
async def on_tool_execute_error(
    self,
    ctx: RunContext[AgentDepsT],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: ValidatedToolArgs,
    error: Exception,
) -> Any:
    """Called when tool execution fails with an exception.

    This is the error counterpart to
    [`after_tool_execute`][pydantic_ai.capabilities.AbstractCapability.after_tool_execute].

    **Raise** the original `error` (or a different exception) to propagate it.
    **Return** any value to suppress the error and use it as the tool result.
    **Raise** [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] to ask the model to
    redo the tool call instead of recovering or propagating.

    Not called for control flow exceptions
    ([`SkipToolExecution`][pydantic_ai.exceptions.SkipToolExecution],
    [`CallDeferred`][pydantic_ai.exceptions.CallDeferred],
    [`ApprovalRequired`][pydantic_ai.exceptions.ApprovalRequired])
    or retry signals ([`ToolRetryError`][pydantic_ai.exceptions.ToolRetryError]
    from [`ModelRetry`][pydantic_ai.exceptions.ModelRetry]).
    Use [`wrap_tool_execute`][pydantic_ai.capabilities.AbstractCapability.wrap_tool_execute]
    to intercept retries.
    """
    raise error
```

#### prefix_tools

```python
prefix_tools(prefix: str) -> PrefixTools[AgentDepsT]
```

Returns a new capability that wraps this one and prefixes its tool names.

Only this capability's tools are prefixed; other agent tools are unaffected.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/abstract.py`

```python
def prefix_tools(self, prefix: str) -> PrefixTools[AgentDepsT]:
    """Returns a new capability that wraps this one and prefixes its tool names.

    Only this capability's tools are prefixed; other agent tools are unaffected.
    """
    from .prefix_tools import PrefixTools

    return PrefixTools(wrapped=self, prefix=prefix)
```

### AgentNode

```python
AgentNode: TypeAlias = (
    "_agent_graph.AgentNode[AgentDepsT, Any]"
)
```

Type alias for an agent graph node (`UserPromptNode`, `ModelRequestNode`, `CallToolsNode`).

### NodeResult

```python
NodeResult: TypeAlias = (
    "_agent_graph.AgentNode[AgentDepsT, Any] | End[FinalResult[Any]]"
)
```

Type alias for the result of executing an agent graph node: either the next node or `End`.

### RawToolArgs

```python
RawToolArgs: TypeAlias = 'str | dict[str, Any]'
```

Type alias for raw (pre-validation) tool arguments.

### ValidatedToolArgs

```python
ValidatedToolArgs: TypeAlias = 'dict[str, Any]'
```

Type alias for validated tool arguments.

### WrapModelRequestHandler

```python
WrapModelRequestHandler: TypeAlias = (
    "Callable[[ModelRequestContext], Awaitable[ModelResponse]]"
)
```

Handler type for wrap_model_request.

### WrapNodeRunHandler

```python
WrapNodeRunHandler: TypeAlias = (
    "Callable[[_agent_graph.AgentNode[AgentDepsT, Any]], Awaitable[_agent_graph.AgentNode[AgentDepsT, Any] | End[FinalResult[Any]]]]"
)
```

Handler type for wrap_node_run.

### WrapRunHandler

```python
WrapRunHandler: TypeAlias = (
    "Callable[[], Awaitable[AgentRunResult[Any]]]"
)
```

Handler type for wrap_run.

### WrapToolExecuteHandler

```python
WrapToolExecuteHandler: TypeAlias = (
    "Callable[[dict[str, Any]], Awaitable[Any]]"
)
```

Handler type for wrap_tool_execute.

### WrapToolValidateHandler

```python
WrapToolValidateHandler: TypeAlias = (
    "Callable[[str | dict[str, Any]], Awaitable[dict[str, Any]]]"
)
```

Handler type for wrap_tool_validate.

### BuiltinOrLocalTool

Bases: `AbstractCapability[AgentDepsT]`

Capability that pairs a provider builtin tool with a local fallback.

When the model supports the builtin natively, the local fallback is removed. When the model doesn't support the builtin, it is removed and the local tool stays.

Can be used directly:

```python
from pydantic_ai.capabilities import BuiltinOrLocalTool

cap = BuiltinOrLocalTool(builtin=WebSearchTool(), local=my_search_func)
```

Or subclassed to set defaults by overriding `_default_builtin`, `_default_local`, and `_requires_builtin`. The built-in WebSearch, WebFetch, and ImageGeneration capabilities are all subclasses.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/builtin_or_local.py`

````python
@dataclass
class BuiltinOrLocalTool(AbstractCapability[AgentDepsT]):
    """Capability that pairs a provider builtin tool with a local fallback.

    When the model supports the builtin natively, the local fallback is removed.
    When the model doesn't support the builtin, it is removed and the local tool stays.

    Can be used directly:

    ```python {test="skip" lint="skip"}
    from pydantic_ai.capabilities import BuiltinOrLocalTool

    cap = BuiltinOrLocalTool(builtin=WebSearchTool(), local=my_search_func)
    ```

    Or subclassed to set defaults by overriding `_default_builtin`, `_default_local`,
    and `_requires_builtin`.
    The built-in [`WebSearch`][pydantic_ai.capabilities.WebSearch],
    [`WebFetch`][pydantic_ai.capabilities.WebFetch], and
    [`ImageGeneration`][pydantic_ai.capabilities.ImageGeneration] capabilities
    are all subclasses.
    """

    builtin: AgentBuiltinTool[AgentDepsT] | bool = True
    """Configure the provider builtin tool.

    - `True` (default): use the default builtin tool configuration (subclasses only).
    - `False`: disable the builtin; always use the local tool.
    - An `AbstractBuiltinTool` instance: use this specific configuration.
    - A callable (`BuiltinToolFunc`): dynamically create the builtin per-run via `RunContext`.
    """

    local: Tool[AgentDepsT] | Callable[..., Any] | AbstractToolset[AgentDepsT] | Literal[False] | None = None
    """Configure the local fallback tool.

    - `None` (default): auto-detect a local fallback via `_default_local`.
    - `False`: disable the local fallback; only use the builtin.
    - A `Tool` or `AbstractToolset` instance: use this specific local tool.
    - A bare callable: automatically wrapped in a `Tool`.
    """

    def __post_init__(self) -> None:
        if self.builtin is False and self.local is False:
            raise UserError(f'{type(self).__name__}: both builtin and local cannot be False')

        # Resolve builtin=True → default instance (subclass hook)
        if self.builtin is True:
            default = self._default_builtin()
            if default is None:
                raise UserError(
                    f'{type(self).__name__}: builtin=True requires a subclass that overrides '
                    f'_default_builtin(), or pass an AbstractBuiltinTool instance directly'
                )
            self.builtin = default

        # Resolve local: None → default, callable → Tool
        if self.local is None:
            self.local = self._default_local()
        elif callable(self.local) and not isinstance(self.local, (Tool, AbstractToolset)):
            self.local = Tool(self.local)

        # Catch contradictory config: builtin disabled but constraint fields require it
        if self.builtin is False and self._requires_builtin():
            raise UserError(f'{type(self).__name__}: constraint fields require the builtin tool, but builtin=False')

    # --- Subclass hooks (not abstract — direct use is supported) ---

    def _default_builtin(self) -> AbstractBuiltinTool | None:
        """Create the default builtin tool instance.

        Override in subclasses. Returns None by default (direct use requires
        passing an explicit `AbstractBuiltinTool` instance as `builtin`).
        """
        return None

    def _builtin_unique_id(self) -> str:
        """The unique_id used for `prefer_builtin` on local tool definitions.

        By default, derived from the builtin tool's `unique_id` property.
        Override in subclasses for custom behavior.
        """
        builtin = self.builtin
        if isinstance(builtin, AbstractBuiltinTool):
            return builtin.unique_id
        raise UserError(
            f'{type(self).__name__}: cannot derive builtin_unique_id — override _builtin_unique_id() in your subclass'
        )

    def _default_local(self) -> Tool[AgentDepsT] | AbstractToolset[AgentDepsT] | None:
        """Auto-detect a local fallback. Override in subclasses that have one."""
        return None

    def _requires_builtin(self) -> bool:
        """Return True if capability-level constraint fields require the builtin.

        When True, the local fallback is suppressed. If the model doesn't support
        the builtin, `UserError` is raised — preventing silent constraint violation.

        Override in subclasses that expose builtin-only constraint fields
        (e.g. `allowed_domains`, `blocked_domains`).
        """
        return False

    # --- Shared logic ---

    def get_builtin_tools(self) -> Sequence[AgentBuiltinTool[AgentDepsT]]:
        if self.builtin is False:
            return []
        # After __post_init__, builtin=True is resolved to an AbstractBuiltinTool instance
        assert not isinstance(self.builtin, bool)
        return [self.builtin]

    def get_toolset(self) -> AbstractToolset[AgentDepsT] | None:
        local = self.local
        if local is None or local is False or self._requires_builtin():
            return None

        # local is Tool | AbstractToolset after __post_init__ resolution
        toolset: AbstractToolset[AgentDepsT] = local if isinstance(local, AbstractToolset) else FunctionToolset([local])  # pyright: ignore[reportUnknownVariableType]

        if self.builtin is not False:
            uid = self._builtin_unique_id()

            async def _add_prefer_builtin(
                ctx: RunContext[AgentDepsT], tool_defs: list[ToolDefinition]
            ) -> list[ToolDefinition]:
                return [replace(d, prefer_builtin=uid) for d in tool_defs]

            return PreparedToolset(wrapped=toolset, prepare_func=_add_prefer_builtin)
        return toolset
````

#### builtin

```python
builtin: AgentBuiltinTool[AgentDepsT] | bool = True
```

Configure the provider builtin tool.

- `True` (default): use the default builtin tool configuration (subclasses only).
- `False`: disable the builtin; always use the local tool.
- An `AbstractBuiltinTool` instance: use this specific configuration.
- A callable (`BuiltinToolFunc`): dynamically create the builtin per-run via `RunContext`.

#### local

```python
local: (
    Tool[AgentDepsT]
    | Callable[..., Any]
    | AbstractToolset[AgentDepsT]
    | Literal[False]
    | None
) = None
```

Configure the local fallback tool.

- `None` (default): auto-detect a local fallback via `_default_local`.
- `False`: disable the local fallback; only use the builtin.
- A `Tool` or `AbstractToolset` instance: use this specific local tool.
- A bare callable: automatically wrapped in a `Tool`.

### BuiltinTool

Bases: `AbstractCapability[AgentDepsT]`

A capability that registers a builtin tool with the agent.

Wraps a single AgentBuiltinTool — either a static AbstractBuiltinTool instance or a callable that dynamically produces one.

When `builtin_tools` is passed to Agent.__init__, each item is automatically wrapped in a `BuiltinTool` capability.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/builtin_tool.py`

```python
@dataclass
class BuiltinTool(AbstractCapability[AgentDepsT]):
    """A capability that registers a builtin tool with the agent.

    Wraps a single [`AgentBuiltinTool`][pydantic_ai.tools.AgentBuiltinTool] — either a static
    [`AbstractBuiltinTool`][pydantic_ai.builtin_tools.AbstractBuiltinTool] instance or a callable
    that dynamically produces one.

    When `builtin_tools` is passed to [`Agent.__init__`][pydantic_ai.Agent.__init__], each item is
    automatically wrapped in a `BuiltinTool` capability.
    """

    tool: AgentBuiltinTool[AgentDepsT]

    def get_builtin_tools(self) -> Sequence[AgentBuiltinTool[AgentDepsT]]:
        return [self.tool]

    @classmethod
    def from_spec(cls, tool: AbstractBuiltinTool | None = None, **kwargs: Any) -> BuiltinTool[Any]:
        """Create from spec.

        Supports two YAML forms:

        - Flat: `{BuiltinTool: {kind: web_search, search_context_size: high}}`
        - Explicit: `{BuiltinTool: {tool: {kind: web_search}}}`
        """
        if tool is not None:
            validated = _BUILTIN_TOOL_ADAPTER.validate_python(tool)
        elif kwargs:
            validated = _BUILTIN_TOOL_ADAPTER.validate_python(kwargs)
        else:
            raise TypeError(
                '`BuiltinTool.from_spec()` requires either a `tool` argument or keyword arguments'
                ' specifying the builtin tool type (e.g. `kind="web_search"`)'
            )
        return cls(tool=validated)
```

#### from_spec

```python
from_spec(
    tool: AbstractBuiltinTool | None = None, **kwargs: Any
) -> BuiltinTool[Any]
```

Create from spec.

Supports two YAML forms:

- Flat: `{BuiltinTool: {kind: web_search, search_context_size: high}}`
- Explicit: `{BuiltinTool: {tool: {kind: web_search}}}`

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/builtin_tool.py`

```python
@classmethod
def from_spec(cls, tool: AbstractBuiltinTool | None = None, **kwargs: Any) -> BuiltinTool[Any]:
    """Create from spec.

    Supports two YAML forms:

    - Flat: `{BuiltinTool: {kind: web_search, search_context_size: high}}`
    - Explicit: `{BuiltinTool: {tool: {kind: web_search}}}`
    """
    if tool is not None:
        validated = _BUILTIN_TOOL_ADAPTER.validate_python(tool)
    elif kwargs:
        validated = _BUILTIN_TOOL_ADAPTER.validate_python(kwargs)
    else:
        raise TypeError(
            '`BuiltinTool.from_spec()` requires either a `tool` argument or keyword arguments'
            ' specifying the builtin tool type (e.g. `kind="web_search"`)'
        )
    return cls(tool=validated)
```

### CombinedCapability

Bases: `AbstractCapability[AgentDepsT]`

A capability that combines multiple capabilities.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/combined.py`

```python
@dataclass
class CombinedCapability(AbstractCapability[AgentDepsT]):
    """A capability that combines multiple capabilities."""

    capabilities: Sequence[AbstractCapability[AgentDepsT]]

    @property
    def has_wrap_node_run(self) -> bool:
        return any(c.has_wrap_node_run for c in self.capabilities)

    async def for_run(self, ctx: RunContext[AgentDepsT]) -> AbstractCapability[AgentDepsT]:
        new_caps = await asyncio.gather(*(c.for_run(ctx) for c in self.capabilities))
        if all(new is old for new, old in zip(new_caps, self.capabilities)):
            return self
        return replace(self, capabilities=list(new_caps))

    def get_instructions(self) -> AgentInstructions[AgentDepsT] | None:
        instructions: list[str | _system_prompt.SystemPromptFunc[AgentDepsT]] = []
        for capability in self.capabilities:
            instructions.extend(normalize_instructions(capability.get_instructions()))
        return instructions or None

    def get_model_settings(self) -> ModelSettings | Callable[[RunContext[AgentDepsT]], ModelSettings] | None:
        # Collect settings in order, preserving each capability's position in the merge chain.
        # Each entry is either a static dict or a dynamic callable.
        settings_chain: list[ModelSettings | Callable[[RunContext[AgentDepsT]], ModelSettings]] = []
        for capability in self.capabilities:
            cap_settings = capability.get_model_settings()
            if cap_settings is not None:
                settings_chain.append(cap_settings)
        if not settings_chain:
            return None
        if all(not callable(s) for s in settings_chain):
            # All static — merge eagerly
            merged: ModelSettings | None = None
            for s in settings_chain:
                merged = merge_model_settings(merged, s)  # type: ignore[arg-type]
            return merged

        def resolve(ctx: RunContext[AgentDepsT]) -> ModelSettings:
            merged: ModelSettings | None = None
            for entry in settings_chain:
                # Mutate ctx.model_settings so each dynamic entry sees the
                # accumulated settings from all prior layers.
                ctx.model_settings = merge_model_settings(ctx.model_settings, merged)
                resolved = entry(ctx) if callable(entry) else entry
                merged = merge_model_settings(merged, resolved)
            # Update ctx.model_settings to include the final entry's contribution
            ctx.model_settings = merge_model_settings(ctx.model_settings, merged)
            return merged if merged is not None else ModelSettings()

        return resolve

    def get_toolset(self) -> AgentToolset[AgentDepsT] | None:
        toolsets: list[AbstractToolset[AgentDepsT]] = []
        for capability in self.capabilities:
            toolset = capability.get_toolset()
            if toolset is None:
                pass
            elif isinstance(toolset, AbstractToolset):
                # Pyright can't narrow Callable type aliases out of unions after isinstance check
                toolsets.append(toolset)  # pyright: ignore[reportUnknownArgumentType]
            else:
                toolsets.append(DynamicToolset[AgentDepsT](toolset_func=toolset))
        return CombinedToolset(toolsets) if toolsets else None

    def get_builtin_tools(self) -> Sequence[AgentBuiltinTool[AgentDepsT]]:
        builtin_tools: list[AgentBuiltinTool[AgentDepsT]] = []
        for capability in self.capabilities:
            builtin_tools.extend(capability.get_builtin_tools() or [])
        return builtin_tools

    def get_wrapper_toolset(self, toolset: AbstractToolset[AgentDepsT]) -> AbstractToolset[AgentDepsT] | None:
        wrapped = toolset
        any_wrapped = False
        for capability in self.capabilities:
            result = capability.get_wrapper_toolset(wrapped)
            if result is not None:
                wrapped = result
                any_wrapped = True
        return wrapped if any_wrapped else None

    # --- Tool preparation hook ---

    async def prepare_tools(
        self,
        ctx: RunContext[AgentDepsT],
        tool_defs: list[ToolDefinition],
    ) -> list[ToolDefinition]:
        for capability in self.capabilities:
            tool_defs = await capability.prepare_tools(ctx, tool_defs)
        return tool_defs

    # --- Run lifecycle hooks ---

    async def before_run(
        self,
        ctx: RunContext[AgentDepsT],
    ) -> None:
        for capability in self.capabilities:
            await capability.before_run(ctx)

    async def after_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        result: AgentRunResult[Any],
    ) -> AgentRunResult[Any]:
        for capability in reversed(self.capabilities):
            result = await capability.after_run(ctx, result=result)
        return result

    async def wrap_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        handler: Callable[[], Awaitable[AgentRunResult[Any]]],
    ) -> AgentRunResult[Any]:
        chain = handler
        for cap in reversed(self.capabilities):
            chain = _make_run_wrap(cap, ctx, chain)
        return await chain()

    async def on_run_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        error: BaseException,
    ) -> AgentRunResult[Any]:
        for capability in reversed(self.capabilities):
            try:
                return await capability.on_run_error(ctx, error=error)
            except BaseException as new_error:
                error = new_error
        raise error

    # --- Node run lifecycle hooks ---

    async def before_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: _agent_graph.AgentNode[AgentDepsT, Any],
    ) -> _agent_graph.AgentNode[AgentDepsT, Any]:
        for capability in self.capabilities:
            node = await capability.before_node_run(ctx, node=node)
        return node

    async def after_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: _agent_graph.AgentNode[AgentDepsT, Any],
        result: _agent_graph.AgentNode[AgentDepsT, Any] | End[FinalResult[Any]],
    ) -> _agent_graph.AgentNode[AgentDepsT, Any] | End[FinalResult[Any]]:
        for capability in reversed(self.capabilities):
            result = await capability.after_node_run(ctx, node=node, result=result)
        return result

    async def wrap_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: _agent_graph.AgentNode[AgentDepsT, Any],
        handler: Callable[
            [_agent_graph.AgentNode[AgentDepsT, Any]],
            Awaitable[_agent_graph.AgentNode[AgentDepsT, Any] | End[FinalResult[Any]]],
        ],
    ) -> _agent_graph.AgentNode[AgentDepsT, Any] | End[FinalResult[Any]]:
        chain = handler
        for cap in reversed(self.capabilities):
            chain = _make_node_run_wrap(cap, ctx, chain)
        return await chain(node)

    async def on_node_run_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: _agent_graph.AgentNode[AgentDepsT, Any],
        error: Exception,
    ) -> _agent_graph.AgentNode[AgentDepsT, Any] | End[FinalResult[Any]]:
        for capability in reversed(self.capabilities):
            try:
                return await capability.on_node_run_error(ctx, node=node, error=error)
            except Exception as new_error:
                error = new_error
        raise error

    # --- Event stream hook ---

    async def wrap_run_event_stream(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        stream: AsyncIterable[AgentStreamEvent],
    ) -> AsyncIterable[AgentStreamEvent]:
        for cap in reversed(self.capabilities):
            stream = cap.wrap_run_event_stream(ctx, stream=stream)
        async for event in stream:
            yield event

    # --- Model request lifecycle hooks ---

    async def before_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        request_context: ModelRequestContext,
    ) -> ModelRequestContext:
        for capability in self.capabilities:
            request_context = await capability.before_model_request(ctx, request_context)
        return request_context

    async def after_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        response: ModelResponse,
    ) -> ModelResponse:
        for capability in reversed(self.capabilities):
            response = await capability.after_model_request(ctx, request_context=request_context, response=response)
        return response

    async def wrap_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        handler: Callable[[ModelRequestContext], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        chain = handler
        for cap in reversed(self.capabilities):
            chain = _make_model_request_wrap(cap, ctx, chain)
        return await chain(request_context)

    async def on_model_request_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        error: Exception,
    ) -> ModelResponse:
        for capability in reversed(self.capabilities):
            try:
                return await capability.on_model_request_error(ctx, request_context=request_context, error=error)
            except Exception as new_error:
                error = new_error
        raise error

    # --- Tool validate lifecycle hooks ---

    async def before_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: str | dict[str, Any],
    ) -> str | dict[str, Any]:
        for capability in self.capabilities:
            args = await capability.before_tool_validate(ctx, call=call, tool_def=tool_def, args=args)
        return args

    async def after_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        for capability in reversed(self.capabilities):
            args = await capability.after_tool_validate(ctx, call=call, tool_def=tool_def, args=args)
        return args

    async def wrap_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: str | dict[str, Any],
        handler: Callable[[str | dict[str, Any]], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        chain = handler
        for cap in reversed(self.capabilities):
            chain = _make_tool_validate_wrap(cap, ctx, call, tool_def, chain)
        return await chain(args)

    async def on_tool_validate_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: str | dict[str, Any],
        error: ValidationError | ModelRetry,
    ) -> dict[str, Any]:
        for capability in reversed(self.capabilities):
            try:
                return await capability.on_tool_validate_error(
                    ctx, call=call, tool_def=tool_def, args=args, error=error
                )
            except (ValidationError, ModelRetry) as new_error:
                error = new_error
            except (
                Exception
            ):  # pragma: no cover — defensive; on_tool_validate_error shouldn't raise non-validation errors
                raise
        raise error

    # --- Tool execute lifecycle hooks ---

    async def before_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        for capability in self.capabilities:
            args = await capability.before_tool_execute(ctx, call=call, tool_def=tool_def, args=args)
        return args

    async def after_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
        result: Any,
    ) -> Any:
        for capability in reversed(self.capabilities):
            result = await capability.after_tool_execute(ctx, call=call, tool_def=tool_def, args=args, result=result)
        return result

    async def wrap_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
        handler: Callable[[dict[str, Any]], Awaitable[Any]],
    ) -> Any:
        chain = handler
        for cap in reversed(self.capabilities):
            chain = _make_tool_execute_wrap(cap, ctx, call, tool_def, chain)
        return await chain(args)

    async def on_tool_execute_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
        error: Exception,
    ) -> Any:
        for capability in reversed(self.capabilities):
            try:
                return await capability.on_tool_execute_error(ctx, call=call, tool_def=tool_def, args=args, error=error)
            except Exception as new_error:
                error = new_error
        raise error
```

### HistoryProcessor

Bases: `AbstractCapability[AgentDepsT]`

A capability that processes message history before model requests.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/history_processor.py`

```python
@dataclass
class HistoryProcessor(AbstractCapability[AgentDepsT]):
    """A capability that processes message history before model requests."""

    processor: HistoryProcessorFunc[AgentDepsT]

    async def before_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        request_context: ModelRequestContext,
    ) -> ModelRequestContext:
        request_context.messages = await _run_history_processor(self.processor, ctx, request_context.messages)

        return request_context

    @classmethod
    def get_serialization_name(cls) -> str | None:
        return None  # Not spec-serializable (takes a callable)
```

### Hooks

Bases: `AbstractCapability[AgentDepsT]`

Register hook functions via decorators or constructor kwargs.

For extension developers building reusable capabilities, subclass :class:`AbstractCapability` directly. For application code that needs a few hooks without the ceremony of a subclass, use `Hooks`.

Example using decorators::

```text
hooks = Hooks()

@hooks.on.before_model_request
async def log_request(ctx, request_context):
    print(f'Request: {request_context}')
    return request_context

agent = Agent('openai:gpt-5', capabilities=[hooks])
```

Example using constructor kwargs::

```text
agent = Agent('openai:gpt-5', capabilities=[
    Hooks(before_model_request=log_request)
])
```

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/hooks.py`

```python
class Hooks(AbstractCapability[AgentDepsT]):
    """Register hook functions via decorators or constructor kwargs.

    For extension developers building reusable capabilities, subclass
    :class:`AbstractCapability` directly. For application code that needs
    a few hooks without the ceremony of a subclass, use `Hooks`.

    Example using decorators::

        hooks = Hooks()

        @hooks.on.before_model_request
        async def log_request(ctx, request_context):
            print(f'Request: {request_context}')
            return request_context

        agent = Agent('openai:gpt-5', capabilities=[hooks])

    Example using constructor kwargs::

        agent = Agent('openai:gpt-5', capabilities=[
            Hooks(before_model_request=log_request)
        ])
    """

    _registry: dict[str, list[_HookEntry[Any]]]

    def __init__(
        self,
        *,
        # Run lifecycle
        before_run: BeforeRunHookFunc | None = None,
        after_run: AfterRunHookFunc | None = None,
        run: WrapRunHookFunc | None = None,
        run_error: OnRunErrorHookFunc | None = None,
        # Node lifecycle
        before_node_run: BeforeNodeRunHookFunc | None = None,
        after_node_run: AfterNodeRunHookFunc | None = None,
        node_run: WrapNodeRunHookFunc | None = None,
        node_run_error: OnNodeRunErrorHookFunc | None = None,
        # Event stream
        run_event_stream: WrapRunEventStreamHookFunc | None = None,
        event: OnEventHookFunc | None = None,
        # Model request
        before_model_request: BeforeModelRequestHookFunc | None = None,
        after_model_request: AfterModelRequestHookFunc | None = None,
        model_request: WrapModelRequestHookFunc | None = None,
        model_request_error: OnModelRequestErrorHookFunc | None = None,
        # Tool preparation
        prepare_tools: PrepareToolsHookFunc | None = None,
        # Tool validation
        before_tool_validate: BeforeToolValidateHookFunc | None = None,
        after_tool_validate: AfterToolValidateHookFunc | None = None,
        tool_validate: WrapToolValidateHookFunc | None = None,
        tool_validate_error: OnToolValidateErrorHookFunc | None = None,
        # Tool execution
        before_tool_execute: BeforeToolExecuteHookFunc | None = None,
        after_tool_execute: AfterToolExecuteHookFunc | None = None,
        tool_execute: WrapToolExecuteHookFunc | None = None,
        tool_execute_error: OnToolExecuteErrorHookFunc | None = None,
    ):
        self._registry = {}
        # Map constructor kwarg names to internal registry keys (AbstractCapability method names)
        _kwargs: dict[str, Any] = {
            'before_run': before_run,
            'after_run': after_run,
            'wrap_run': run,
            'on_run_error': run_error,
            'before_node_run': before_node_run,
            'after_node_run': after_node_run,
            'wrap_node_run': node_run,
            'on_node_run_error': node_run_error,
            'wrap_run_event_stream': run_event_stream,
            '_on_event': event,
            'before_model_request': before_model_request,
            'after_model_request': after_model_request,
            'wrap_model_request': model_request,
            'on_model_request_error': model_request_error,
            'prepare_tools': prepare_tools,
            'before_tool_validate': before_tool_validate,
            'after_tool_validate': after_tool_validate,
            'wrap_tool_validate': tool_validate,
            'on_tool_validate_error': tool_validate_error,
            'before_tool_execute': before_tool_execute,
            'after_tool_execute': after_tool_execute,
            'wrap_tool_execute': tool_execute,
            'on_tool_execute_error': tool_execute_error,
        }
        for key, func in _kwargs.items():
            if func is not None:
                self._registry.setdefault(key, []).append(_HookEntry(func))

    @cached_property
    def on(self) -> _HookRegistration[AgentDepsT]:
        """Decorator namespace for registering hook functions."""
        return _HookRegistration(self)

    def _get(self, key: str) -> list[_HookEntry[Any]]:
        return self._registry.get(key, [])

    @property
    def has_wrap_node_run(self) -> bool:
        return bool(self._get('wrap_node_run'))

    @classmethod
    def get_serialization_name(cls) -> str | None:
        return None

    def __repr__(self) -> str:
        registered = {k: len(v) for k, v in self._registry.items() if v}
        return f'Hooks({registered})'

    # --- AbstractCapability method overrides ---
    # These dispatch to registered hook functions in self._registry.

    async def before_run(self, ctx: RunContext[AgentDepsT]) -> None:
        for entry in self._get('before_run'):
            await _call_entry(entry, 'before_run', ctx)

    async def after_run(self, ctx: RunContext[AgentDepsT], *, result: AgentRunResult[Any]) -> AgentRunResult[Any]:
        for entry in self._get('after_run'):
            result = await _call_entry(entry, 'after_run', ctx, result=result)
        return result

    async def wrap_run(self, ctx: RunContext[AgentDepsT], *, handler: WrapRunHandler) -> AgentRunResult[Any]:
        entries = self._get('wrap_run')
        if not entries:
            return await handler()
        chain: Callable[..., Any] = handler
        for entry in reversed(entries):
            chain = _make_wrap_link(entry, 'wrap_run', ctx, {}, chain, None)
        return await chain()

    async def on_run_error(self, ctx: RunContext[AgentDepsT], *, error: BaseException) -> AgentRunResult[Any]:
        for entry in self._get('on_run_error'):
            try:
                return await _call_entry(entry, 'on_run_error', ctx, error=error)
            except BaseException as new_error:
                error = new_error
        raise error

    async def before_node_run(
        self, ctx: RunContext[AgentDepsT], *, node: AgentNode[AgentDepsT]
    ) -> AgentNode[AgentDepsT]:
        for entry in self._get('before_node_run'):
            node = await _call_entry(entry, 'before_node_run', ctx, node=node)
        return node

    async def after_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
        result: NodeResult[AgentDepsT],
    ) -> NodeResult[AgentDepsT]:
        for entry in self._get('after_node_run'):
            result = await _call_entry(entry, 'after_node_run', ctx, node=node, result=result)
        return result

    async def wrap_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
        handler: WrapNodeRunHandler[AgentDepsT],
    ) -> NodeResult[AgentDepsT]:
        entries = self._get('wrap_node_run')
        if not entries:
            return await handler(node)
        chain: Callable[..., Any] = handler
        for entry in reversed(entries):
            chain = _make_wrap_link(entry, 'wrap_node_run', ctx, {}, chain, 'node')
        return await chain(node)

    async def on_node_run_error(
        self, ctx: RunContext[AgentDepsT], *, node: AgentNode[AgentDepsT], error: Exception
    ) -> NodeResult[AgentDepsT]:
        for entry in self._get('on_node_run_error'):
            try:
                return await _call_entry(entry, 'on_node_run_error', ctx, node=node, error=error)
            except Exception as new_error:
                error = new_error
        raise error

    async def wrap_run_event_stream(
        self, ctx: RunContext[AgentDepsT], *, stream: AsyncIterable[AgentStreamEvent]
    ) -> AsyncIterable[AgentStreamEvent]:
        # First, wrap with per-event callbacks (innermost)
        event_entries = self._get('_on_event')
        if event_entries:
            stream = _event_callback_stream(ctx, stream, event_entries)
        # Then chain explicit stream wrappers (outermost)
        for entry in reversed(self._get('wrap_run_event_stream')):
            stream = entry.func(ctx, stream=stream)
        async for event in stream:
            yield event

    async def before_model_request(
        self, ctx: RunContext[AgentDepsT], request_context: ModelRequestContext
    ) -> ModelRequestContext:
        for entry in self._get('before_model_request'):
            request_context = await _call_entry(entry, 'before_model_request', ctx, request_context)
        return request_context

    async def after_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        response: ModelResponse,
    ) -> ModelResponse:
        for entry in self._get('after_model_request'):
            response = await _call_entry(
                entry, 'after_model_request', ctx, request_context=request_context, response=response
            )
        return response

    async def wrap_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        handler: WrapModelRequestHandler,
    ) -> ModelResponse:
        entries = self._get('wrap_model_request')
        if not entries:
            return await handler(request_context)
        chain: Callable[..., Any] = handler
        for entry in reversed(entries):
            chain = _make_wrap_link(entry, 'wrap_model_request', ctx, {}, chain, 'request_context')
        return await chain(request_context)

    async def on_model_request_error(
        self, ctx: RunContext[AgentDepsT], *, request_context: ModelRequestContext, error: Exception
    ) -> ModelResponse:
        for entry in self._get('on_model_request_error'):
            try:
                return await _call_entry(
                    entry, 'on_model_request_error', ctx, request_context=request_context, error=error
                )
            except Exception as new_error:
                error = new_error
        raise error

    async def prepare_tools(self, ctx: RunContext[AgentDepsT], tool_defs: list[ToolDefinition]) -> list[ToolDefinition]:
        for entry in self._get('prepare_tools'):
            tool_defs = await _call_entry(entry, 'prepare_tools', ctx, tool_defs)
        return tool_defs

    async def before_tool_validate(
        self, ctx: RunContext[AgentDepsT], *, call: ToolCallPart, tool_def: ToolDefinition, args: RawToolArgs
    ) -> RawToolArgs:
        for entry in _filter_tool_entries(self._get('before_tool_validate'), call=call):
            args = await _call_entry(entry, 'before_tool_validate', ctx, call=call, tool_def=tool_def, args=args)
        return args

    async def after_tool_validate(
        self, ctx: RunContext[AgentDepsT], *, call: ToolCallPart, tool_def: ToolDefinition, args: ValidatedToolArgs
    ) -> ValidatedToolArgs:
        for entry in _filter_tool_entries(self._get('after_tool_validate'), call=call):
            args = await _call_entry(entry, 'after_tool_validate', ctx, call=call, tool_def=tool_def, args=args)
        return args

    async def wrap_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: RawToolArgs,
        handler: WrapToolValidateHandler,
    ) -> ValidatedToolArgs:
        entries = _filter_tool_entries(self._get('wrap_tool_validate'), call=call)
        if not entries:
            return await handler(args)
        chain: Callable[..., Any] = handler
        for entry in reversed(entries):
            chain = _make_wrap_link(
                entry, 'wrap_tool_validate', ctx, {'call': call, 'tool_def': tool_def}, chain, 'args'
            )
        return await chain(args)

    async def on_tool_validate_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: RawToolArgs,
        error: ValidationError | ModelRetry,
    ) -> ValidatedToolArgs:
        for entry in _filter_tool_entries(self._get('on_tool_validate_error'), call=call):
            try:
                return await _call_entry(
                    entry, 'on_tool_validate_error', ctx, call=call, tool_def=tool_def, args=args, error=error
                )
            except (ValidationError, ModelRetry) as new_error:
                error = new_error
        raise error

    async def before_tool_execute(
        self, ctx: RunContext[AgentDepsT], *, call: ToolCallPart, tool_def: ToolDefinition, args: ValidatedToolArgs
    ) -> ValidatedToolArgs:
        for entry in _filter_tool_entries(self._get('before_tool_execute'), call=call):
            args = await _call_entry(entry, 'before_tool_execute', ctx, call=call, tool_def=tool_def, args=args)
        return args

    async def after_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
        result: Any,
    ) -> Any:
        for entry in _filter_tool_entries(self._get('after_tool_execute'), call=call):
            result = await _call_entry(
                entry, 'after_tool_execute', ctx, call=call, tool_def=tool_def, args=args, result=result
            )
        return result

    async def wrap_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
        handler: WrapToolExecuteHandler,
    ) -> Any:
        entries = _filter_tool_entries(self._get('wrap_tool_execute'), call=call)
        if not entries:
            return await handler(args)
        chain: Callable[..., Any] = handler
        for entry in reversed(entries):
            chain = _make_wrap_link(
                entry, 'wrap_tool_execute', ctx, {'call': call, 'tool_def': tool_def}, chain, 'args'
            )
        return await chain(args)

    async def on_tool_execute_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
        error: Exception,
    ) -> Any:
        for entry in _filter_tool_entries(self._get('on_tool_execute_error'), call=call):
            try:
                return await _call_entry(
                    entry, 'on_tool_execute_error', ctx, call=call, tool_def=tool_def, args=args, error=error
                )
            except Exception as new_error:
                error = new_error
        raise error
```

#### on

```python
on: _HookRegistration[AgentDepsT]
```

Decorator namespace for registering hook functions.

### HookTimeoutError

Bases: `TimeoutError`

Raised when a hook function exceeds its configured timeout.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/hooks.py`

```python
class HookTimeoutError(TimeoutError):
    """Raised when a hook function exceeds its configured timeout."""

    def __init__(self, hook_name: str, func_name: str, timeout: float):
        self.hook_name = hook_name
        self.func_name = func_name
        self.timeout = timeout
        super().__init__(f'Hook {hook_name!r} function {func_name!r} timed out after {timeout}s')
```

### ImageGeneration

Bases: `BuiltinOrLocalTool[AgentDepsT]`

Image generation capability.

Uses the model's builtin image generation when available. No default local fallback — provide a custom `local` tool if needed.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/image_generation.py`

```python
@dataclass(init=False)
class ImageGeneration(BuiltinOrLocalTool[AgentDepsT]):
    """Image generation capability.

    Uses the model's builtin image generation when available. No default local
    fallback — provide a custom `local` tool if needed.
    """

    def __init__(
        self,
        *,
        builtin: ImageGenerationTool
        | Callable[[RunContext[AgentDepsT]], Awaitable[ImageGenerationTool | None] | ImageGenerationTool | None]
        | bool = True,
        local: Tool[AgentDepsT] | Callable[..., Any] | Literal[False] | None = None,
    ) -> None:
        self.builtin = builtin
        self.local = local
        self.__post_init__()

    def _default_builtin(self) -> ImageGenerationTool:
        return ImageGenerationTool()

    def _builtin_unique_id(self) -> str:
        return ImageGenerationTool.kind
```

### MCP

Bases: `BuiltinOrLocalTool[AgentDepsT]`

MCP server capability.

Uses the model's builtin MCP server support when available, connecting directly via HTTP when it isn't.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/mcp.py`

```python
@dataclass(init=False)
class MCP(BuiltinOrLocalTool[AgentDepsT]):
    """MCP server capability.

    Uses the model's builtin MCP server support when available, connecting
    directly via HTTP when it isn't.
    """

    url: str
    """The URL of the MCP server."""

    id: str | None
    """Unique identifier for the MCP server. Defaults to a slug derived from the URL."""

    authorization_token: str | None
    """Authorization header value for MCP server requests. Passed to both builtin and local."""

    headers: dict[str, str] | None
    """HTTP headers for MCP server requests. Passed to both builtin and local."""

    allowed_tools: list[str] | None
    """Filter to only these tools. Applied to both builtin and local."""

    description: str | None
    """Description of the MCP server. Builtin-only; ignored by local tools."""

    def __init__(
        self,
        url: str,
        *,
        builtin: MCPServerTool
        | Callable[[RunContext[AgentDepsT]], Awaitable[MCPServerTool | None] | MCPServerTool | None]
        | bool = True,
        local: MCPServer | FastMCPToolset[AgentDepsT] | Callable[..., Any] | Literal[False] | None = None,
        id: str | None = None,
        authorization_token: str | None = None,
        headers: dict[str, str] | None = None,
        allowed_tools: list[str] | None = None,
        description: str | None = None,
    ) -> None:
        self.url = url
        self.builtin = builtin
        self.local = local
        self.id = id
        self.authorization_token = authorization_token
        self.headers = headers
        self.allowed_tools = allowed_tools
        self.description = description
        self.__post_init__()

    @cached_property
    def _resolved_id(self) -> str:
        if self.id:
            return self.id
        # Include hostname to avoid collisions (e.g. two /sse URLs on different hosts)
        parsed = urlparse(self.url)
        path = parsed.path.rstrip('/')
        slug = path.split('/')[-1] if path else ''
        host = parsed.hostname or ''
        return f'{host}-{slug}' if slug else host or self.url

    def _default_builtin(self) -> MCPServerTool:
        return MCPServerTool(
            id=self._resolved_id,
            url=self.url,
            authorization_token=self.authorization_token,
            headers=self.headers,
            allowed_tools=self.allowed_tools,
            description=self.description,
        )

    def _builtin_unique_id(self) -> str:
        return f'mcp_server:{self._resolved_id}'

    def _default_local(self) -> Tool[AgentDepsT] | AbstractToolset[AgentDepsT] | None:
        # Merge authorization_token into headers for local connection
        local_headers = dict(self.headers or {})
        if self.authorization_token:
            local_headers['Authorization'] = self.authorization_token

        # Transport detection matching _mcp_server_discriminator() in pydantic_ai.mcp
        if self.url.endswith('/sse'):
            from pydantic_ai.mcp import MCPServerSSE

            return MCPServerSSE(self.url, headers=local_headers or None)

        from pydantic_ai.mcp import MCPServerStreamableHTTP

        return MCPServerStreamableHTTP(self.url, headers=local_headers or None)

    def get_toolset(self) -> AbstractToolset[AgentDepsT] | None:
        toolset = super().get_toolset()
        if toolset is not None and self.allowed_tools is not None:
            allowed = set(self.allowed_tools)
            return toolset.filtered(lambda _ctx, tool_def: tool_def.name in allowed)
        return toolset
```

#### url

```python
url: str = url
```

The URL of the MCP server.

#### id

```python
id: str | None = id
```

Unique identifier for the MCP server. Defaults to a slug derived from the URL.

#### authorization_token

```python
authorization_token: str | None = authorization_token
```

Authorization header value for MCP server requests. Passed to both builtin and local.

#### headers

```python
headers: dict[str, str] | None = headers
```

HTTP headers for MCP server requests. Passed to both builtin and local.

#### allowed_tools

```python
allowed_tools: list[str] | None = allowed_tools
```

Filter to only these tools. Applied to both builtin and local.

#### description

```python
description: str | None = description
```

Description of the MCP server. Builtin-only; ignored by local tools.

### PrefixTools

Bases: `WrapperCapability[AgentDepsT]`

A capability that wraps another capability and prefixes its tool names.

Only the wrapped capability's tools are prefixed; other agent tools are unaffected.

```python
from pydantic_ai import Agent
from pydantic_ai.capabilities import PrefixTools, Toolset
from pydantic_ai.toolsets import FunctionToolset

toolset = FunctionToolset()

agent = Agent(
    'openai:gpt-5',
    capabilities=[
        PrefixTools(
            wrapped=Toolset(toolset),
            prefix='ns',
        ),
    ],
)
```

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/prefix_tools.py`

````python
@dataclass
class PrefixTools(WrapperCapability[AgentDepsT]):
    """A capability that wraps another capability and prefixes its tool names.

    Only the wrapped capability's tools are prefixed; other agent tools are unaffected.

    ```python
    from pydantic_ai import Agent
    from pydantic_ai.capabilities import PrefixTools, Toolset
    from pydantic_ai.toolsets import FunctionToolset

    toolset = FunctionToolset()

    agent = Agent(
        'openai:gpt-5',
        capabilities=[
            PrefixTools(
                wrapped=Toolset(toolset),
                prefix='ns',
            ),
        ],
    )
    ```
    """

    prefix: str

    @classmethod
    def get_serialization_name(cls) -> str | None:
        return 'PrefixTools'

    @classmethod
    def from_spec(cls, *, prefix: str, capability: CapabilitySpec) -> PrefixTools[Any]:
        """Create from spec with a nested capability specification.

        Args:
            prefix: The prefix to add to tool names (e.g. `'mcp'` turns `'search'` into `'mcp_search'`).
            capability: A capability spec (same format as entries in the `capabilities` list).
        """
        from pydantic_ai.agent.spec import load_capability_from_nested_spec

        wrapped = load_capability_from_nested_spec(capability)
        return cls(wrapped=wrapped, prefix=prefix)

    def get_toolset(self) -> AgentToolset[AgentDepsT] | None:
        toolset = super().get_toolset()
        if toolset is None:
            return None
        if isinstance(toolset, AbstractToolset):
            # Pyright can't narrow Callable type aliases out of unions after isinstance check
            return PrefixedToolset(toolset, prefix=self.prefix)  # pyright: ignore[reportUnknownArgumentType]
        # ToolsetFunc callable — wrap in DynamicToolset so PrefixedToolset can delegate
        return PrefixedToolset(DynamicToolset[AgentDepsT](toolset_func=toolset), prefix=self.prefix)
````

#### from_spec

```python
from_spec(
    *, prefix: str, capability: CapabilitySpec
) -> PrefixTools[Any]
```

Create from spec with a nested capability specification.

Parameters:

| Name         | Type             | Description                                                                    | Default    |
| ------------ | ---------------- | ------------------------------------------------------------------------------ | ---------- |
| `prefix`     | `str`            | The prefix to add to tool names (e.g. 'mcp' turns 'search' into 'mcp_search'). | *required* |
| `capability` | `CapabilitySpec` | A capability spec (same format as entries in the capabilities list).           | *required* |

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/prefix_tools.py`

```python
@classmethod
def from_spec(cls, *, prefix: str, capability: CapabilitySpec) -> PrefixTools[Any]:
    """Create from spec with a nested capability specification.

    Args:
        prefix: The prefix to add to tool names (e.g. `'mcp'` turns `'search'` into `'mcp_search'`).
        capability: A capability spec (same format as entries in the `capabilities` list).
    """
    from pydantic_ai.agent.spec import load_capability_from_nested_spec

    wrapped = load_capability_from_nested_spec(capability)
    return cls(wrapped=wrapped, prefix=prefix)
```

### PrepareTools

Bases: `AbstractCapability[AgentDepsT]`

Capability that filters or modifies tool definitions using a callable.

Wraps a ToolsPrepareFunc as a capability, allowing it to be composed with other capabilities via the capability system.

```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import PrepareTools
from pydantic_ai.tools import ToolDefinition


async def hide_admin_tools(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition] | None:
    return [td for td in tool_defs if not td.name.startswith('admin_')]

agent = Agent('openai:gpt-5', capabilities=[PrepareTools(hide_admin_tools)])
```

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/prepare_tools.py`

````python
@dataclass
class PrepareTools(AbstractCapability[AgentDepsT]):
    """Capability that filters or modifies tool definitions using a callable.

    Wraps a [`ToolsPrepareFunc`][pydantic_ai.tools.ToolsPrepareFunc] as a capability,
    allowing it to be composed with other capabilities via the capability system.

    ```python
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.capabilities import PrepareTools
    from pydantic_ai.tools import ToolDefinition


    async def hide_admin_tools(
        ctx: RunContext[None], tool_defs: list[ToolDefinition]
    ) -> list[ToolDefinition] | None:
        return [td for td in tool_defs if not td.name.startswith('admin_')]

    agent = Agent('openai:gpt-5', capabilities=[PrepareTools(hide_admin_tools)])
    ```
    """

    prepare_func: ToolsPrepareFunc[AgentDepsT]

    @classmethod
    def get_serialization_name(cls) -> str | None:
        return None  # Not spec-serializable (takes a callable)

    def get_wrapper_toolset(self, toolset: AbstractToolset[AgentDepsT]) -> AbstractToolset[AgentDepsT]:
        return PreparedToolset(toolset, self.prepare_func)
````

### Thinking

Bases: `AbstractCapability[Any]`

Enables and configures model thinking/reasoning.

Uses the unified `thinking` setting in ModelSettings to work portably across providers. Provider-specific thinking settings (e.g., `anthropic_thinking`, `openai_reasoning_effort`) take precedence when both are set.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/thinking.py`

```python
@dataclass
class Thinking(AbstractCapability[Any]):
    """Enables and configures model thinking/reasoning.

    Uses the unified `thinking` setting in
    [`ModelSettings`][pydantic_ai.settings.ModelSettings] to work portably across providers.
    Provider-specific thinking settings (e.g., `anthropic_thinking`,
    `openai_reasoning_effort`) take precedence when both are set.
    """

    effort: ThinkingLevel = True
    """The thinking effort level.

    - `True`: Enable thinking with the provider's default effort.
    - `False`: Disable thinking (silently ignored on always-on models).
    - `'minimal'`/`'low'`/`'medium'`/`'high'`/`'xhigh'`: Enable thinking at a specific effort level.
    """

    def get_model_settings(self) -> ModelSettings | None:
        return ModelSettings(thinking=self.effort)
```

#### effort

```python
effort: ThinkingLevel = True
```

The thinking effort level.

- `True`: Enable thinking with the provider's default effort.
- `False`: Disable thinking (silently ignored on always-on models).
- `'minimal'`/`'low'`/`'medium'`/`'high'`/`'xhigh'`: Enable thinking at a specific effort level.

### Toolset

Bases: `AbstractCapability[AgentDepsT]`

A capability that provides a toolset.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/toolset.py`

```python
@dataclass
class Toolset(AbstractCapability[AgentDepsT]):
    """A capability that provides a toolset."""

    toolset: AgentToolset[AgentDepsT]

    @classmethod
    def get_serialization_name(cls) -> str | None:
        return None  # Not spec-serializable (takes a callable)

    def get_toolset(self) -> AgentToolset[AgentDepsT] | None:
        return self.toolset
```

### WebFetch

Bases: `BuiltinOrLocalTool[AgentDepsT]`

URL fetching capability.

Uses the model's builtin URL fetching when available. No default local fallback — provide a custom `local` tool if needed.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/web_fetch.py`

```python
@dataclass(init=False)
class WebFetch(BuiltinOrLocalTool[AgentDepsT]):
    """URL fetching capability.

    Uses the model's builtin URL fetching when available. No default local
    fallback — provide a custom `local` tool if needed.
    """

    allowed_domains: list[str] | None
    """Only fetch from these domains. Requires builtin support."""

    blocked_domains: list[str] | None
    """Never fetch from these domains. Requires builtin support."""

    max_uses: int | None
    """Maximum number of fetches per run. Requires builtin support."""

    enable_citations: bool | None
    """Enable citations for fetched content. Builtin-only; ignored by local tools."""

    max_content_tokens: int | None
    """Maximum content length in tokens. Builtin-only; ignored by local tools."""

    def __init__(
        self,
        *,
        builtin: WebFetchTool
        | Callable[[RunContext[AgentDepsT]], Awaitable[WebFetchTool | None] | WebFetchTool | None]
        | bool = True,
        local: Tool[AgentDepsT] | Callable[..., Any] | Literal[False] | None = None,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
        max_uses: int | None = None,
        enable_citations: bool | None = None,
        max_content_tokens: int | None = None,
    ) -> None:
        self.builtin = builtin
        self.local = local
        self.allowed_domains = allowed_domains
        self.blocked_domains = blocked_domains
        self.max_uses = max_uses
        self.enable_citations = enable_citations
        self.max_content_tokens = max_content_tokens
        self.__post_init__()

    def _default_builtin(self) -> WebFetchTool:
        kwargs: dict[str, Any] = {}
        if self.allowed_domains is not None:
            kwargs['allowed_domains'] = self.allowed_domains
        if self.blocked_domains is not None:
            kwargs['blocked_domains'] = self.blocked_domains
        if self.max_uses is not None:
            kwargs['max_uses'] = self.max_uses
        if self.enable_citations is not None:
            kwargs['enable_citations'] = self.enable_citations
        if self.max_content_tokens is not None:
            kwargs['max_content_tokens'] = self.max_content_tokens
        return WebFetchTool(**kwargs)

    def _builtin_unique_id(self) -> str:
        return WebFetchTool.kind

    def _requires_builtin(self) -> bool:
        return self.allowed_domains is not None or self.blocked_domains is not None or self.max_uses is not None
```

#### allowed_domains

```python
allowed_domains: list[str] | None = allowed_domains
```

Only fetch from these domains. Requires builtin support.

#### blocked_domains

```python
blocked_domains: list[str] | None = blocked_domains
```

Never fetch from these domains. Requires builtin support.

#### max_uses

```python
max_uses: int | None = max_uses
```

Maximum number of fetches per run. Requires builtin support.

#### enable_citations

```python
enable_citations: bool | None = enable_citations
```

Enable citations for fetched content. Builtin-only; ignored by local tools.

#### max_content_tokens

```python
max_content_tokens: int | None = max_content_tokens
```

Maximum content length in tokens. Builtin-only; ignored by local tools.

### WebSearch

Bases: `BuiltinOrLocalTool[AgentDepsT]`

Web search capability.

Uses the model's builtin web search when available, falling back to a local function tool (DuckDuckGo by default) when it isn't.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/web_search.py`

```python
@dataclass(init=False)
class WebSearch(BuiltinOrLocalTool[AgentDepsT]):
    """Web search capability.

    Uses the model's builtin web search when available, falling back to a local
    function tool (DuckDuckGo by default) when it isn't.
    """

    search_context_size: Literal['low', 'medium', 'high'] | None
    """Controls how much context is retrieved from the web. Builtin-only; ignored by local tools."""

    user_location: WebSearchUserLocation | None
    """Localize search results based on user location. Builtin-only; ignored by local tools."""

    blocked_domains: list[str] | None
    """Domains to exclude from results. Requires builtin support."""

    allowed_domains: list[str] | None
    """Only include results from these domains. Requires builtin support."""

    max_uses: int | None
    """Maximum number of web searches per run. Requires builtin support."""

    def __init__(
        self,
        *,
        builtin: WebSearchTool
        | Callable[[RunContext[AgentDepsT]], Awaitable[WebSearchTool | None] | WebSearchTool | None]
        | bool = True,
        local: Tool[AgentDepsT] | Callable[..., Any] | Literal[False] | None = None,
        search_context_size: Literal['low', 'medium', 'high'] | None = None,
        user_location: WebSearchUserLocation | None = None,
        blocked_domains: list[str] | None = None,
        allowed_domains: list[str] | None = None,
        max_uses: int | None = None,
    ) -> None:
        self.builtin = builtin
        self.local = local
        self.search_context_size = search_context_size
        self.user_location = user_location
        self.blocked_domains = blocked_domains
        self.allowed_domains = allowed_domains
        self.max_uses = max_uses
        self.__post_init__()

    def _default_builtin(self) -> WebSearchTool:
        kwargs: dict[str, Any] = {}
        if self.search_context_size is not None:
            kwargs['search_context_size'] = self.search_context_size
        if self.user_location is not None:
            kwargs['user_location'] = self.user_location
        if self.blocked_domains is not None:
            kwargs['blocked_domains'] = self.blocked_domains
        if self.allowed_domains is not None:
            kwargs['allowed_domains'] = self.allowed_domains
        if self.max_uses is not None:
            kwargs['max_uses'] = self.max_uses
        return WebSearchTool(**kwargs)

    def _builtin_unique_id(self) -> str:
        return WebSearchTool.kind

    def _default_local(self) -> Tool[AgentDepsT] | AbstractToolset[AgentDepsT] | None:
        try:
            from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

            return duckduckgo_search_tool()
        except ImportError:
            return None

    def _requires_builtin(self) -> bool:
        return self.blocked_domains is not None or self.allowed_domains is not None or self.max_uses is not None
```

#### search_context_size

```python
search_context_size: (
    Literal["low", "medium", "high"] | None
) = search_context_size
```

Controls how much context is retrieved from the web. Builtin-only; ignored by local tools.

#### user_location

```python
user_location: WebSearchUserLocation | None = user_location
```

Localize search results based on user location. Builtin-only; ignored by local tools.

#### blocked_domains

```python
blocked_domains: list[str] | None = blocked_domains
```

Domains to exclude from results. Requires builtin support.

#### allowed_domains

```python
allowed_domains: list[str] | None = allowed_domains
```

Only include results from these domains. Requires builtin support.

#### max_uses

```python
max_uses: int | None = max_uses
```

Maximum number of web searches per run. Requires builtin support.

### WrapperCapability

Bases: `AbstractCapability[AgentDepsT]`

A capability that wraps another capability and delegates all methods.

Analogous to WrapperToolset for toolsets. Subclass and override specific methods to modify behavior while delegating the rest.

Source code in `pydantic_ai_slim/pydantic_ai/capabilities/wrapper.py`

```python
@dataclass
class WrapperCapability(AbstractCapability[AgentDepsT]):
    """A capability that wraps another capability and delegates all methods.

    Analogous to [`WrapperToolset`][pydantic_ai.toolsets.WrapperToolset] for toolsets.
    Subclass and override specific methods to modify behavior while delegating the rest.
    """

    wrapped: AbstractCapability[AgentDepsT]

    @classmethod
    def get_serialization_name(cls) -> str | None:
        return None

    @property
    def has_wrap_node_run(self) -> bool:
        return type(self).wrap_node_run is not WrapperCapability.wrap_node_run or self.wrapped.has_wrap_node_run

    async def for_run(self, ctx: RunContext[AgentDepsT]) -> AbstractCapability[AgentDepsT]:
        new_wrapped = await self.wrapped.for_run(ctx)
        if new_wrapped is self.wrapped:
            return self
        return replace(self, wrapped=new_wrapped)

    # --- Get methods ---

    def get_instructions(self) -> AgentInstructions[AgentDepsT] | None:
        return self.wrapped.get_instructions()

    def get_model_settings(self) -> AgentModelSettings[AgentDepsT] | None:
        return self.wrapped.get_model_settings()

    def get_toolset(self) -> AgentToolset[AgentDepsT] | None:
        return self.wrapped.get_toolset()

    def get_builtin_tools(self) -> Sequence[AgentBuiltinTool[AgentDepsT]]:
        return self.wrapped.get_builtin_tools()

    def get_wrapper_toolset(self, toolset: AbstractToolset[AgentDepsT]) -> AbstractToolset[AgentDepsT] | None:
        return self.wrapped.get_wrapper_toolset(toolset)

    async def prepare_tools(
        self,
        ctx: RunContext[AgentDepsT],
        tool_defs: list[ToolDefinition],
    ) -> list[ToolDefinition]:
        return await self.wrapped.prepare_tools(ctx, tool_defs)

    # --- Run lifecycle hooks ---

    async def before_run(self, ctx: RunContext[AgentDepsT]) -> None:
        await self.wrapped.before_run(ctx)

    async def after_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        result: AgentRunResult[Any],
    ) -> AgentRunResult[Any]:
        return await self.wrapped.after_run(ctx, result=result)

    async def wrap_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        handler: WrapRunHandler,
    ) -> AgentRunResult[Any]:
        return await self.wrapped.wrap_run(ctx, handler=handler)

    async def on_run_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        error: BaseException,
    ) -> AgentRunResult[Any]:
        return await self.wrapped.on_run_error(ctx, error=error)

    # --- Node run lifecycle hooks ---

    async def before_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
    ) -> AgentNode[AgentDepsT]:
        return await self.wrapped.before_node_run(ctx, node=node)

    async def after_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
        result: NodeResult[AgentDepsT],
    ) -> NodeResult[AgentDepsT]:
        return await self.wrapped.after_node_run(ctx, node=node, result=result)

    async def wrap_node_run(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
        handler: WrapNodeRunHandler[AgentDepsT],
    ) -> NodeResult[AgentDepsT]:
        return await self.wrapped.wrap_node_run(ctx, node=node, handler=handler)

    async def on_node_run_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        node: AgentNode[AgentDepsT],
        error: Exception,
    ) -> NodeResult[AgentDepsT]:
        return await self.wrapped.on_node_run_error(ctx, node=node, error=error)

    # --- Event stream hook ---

    async def wrap_run_event_stream(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        stream: AsyncIterable[AgentStreamEvent],
    ) -> AsyncIterable[AgentStreamEvent]:
        async for event in self.wrapped.wrap_run_event_stream(ctx, stream=stream):
            yield event

    # --- Model request lifecycle hooks ---

    async def before_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        request_context: ModelRequestContext,
    ) -> ModelRequestContext:
        return await self.wrapped.before_model_request(ctx, request_context)

    async def after_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        response: ModelResponse,
    ) -> ModelResponse:
        return await self.wrapped.after_model_request(ctx, request_context=request_context, response=response)

    async def wrap_model_request(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        handler: WrapModelRequestHandler,
    ) -> ModelResponse:
        return await self.wrapped.wrap_model_request(ctx, request_context=request_context, handler=handler)

    async def on_model_request_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        request_context: ModelRequestContext,
        error: Exception,
    ) -> ModelResponse:
        return await self.wrapped.on_model_request_error(ctx, request_context=request_context, error=error)

    # --- Tool validate lifecycle hooks ---

    async def before_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: RawToolArgs,
    ) -> RawToolArgs:
        return await self.wrapped.before_tool_validate(ctx, call=call, tool_def=tool_def, args=args)

    async def after_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
    ) -> ValidatedToolArgs:
        return await self.wrapped.after_tool_validate(ctx, call=call, tool_def=tool_def, args=args)

    async def wrap_tool_validate(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: RawToolArgs,
        handler: WrapToolValidateHandler,
    ) -> ValidatedToolArgs:
        return await self.wrapped.wrap_tool_validate(ctx, call=call, tool_def=tool_def, args=args, handler=handler)

    async def on_tool_validate_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: RawToolArgs,
        error: ValidationError | ModelRetry,
    ) -> ValidatedToolArgs:
        return await self.wrapped.on_tool_validate_error(ctx, call=call, tool_def=tool_def, args=args, error=error)

    # --- Tool execute lifecycle hooks ---

    async def before_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
    ) -> ValidatedToolArgs:
        return await self.wrapped.before_tool_execute(ctx, call=call, tool_def=tool_def, args=args)

    async def after_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
        result: Any,
    ) -> Any:
        return await self.wrapped.after_tool_execute(ctx, call=call, tool_def=tool_def, args=args, result=result)

    async def wrap_tool_execute(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
        handler: WrapToolExecuteHandler,
    ) -> Any:
        return await self.wrapped.wrap_tool_execute(ctx, call=call, tool_def=tool_def, args=args, handler=handler)

    async def on_tool_execute_error(
        self,
        ctx: RunContext[AgentDepsT],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: ValidatedToolArgs,
        error: Exception,
    ) -> Any:
        return await self.wrapped.on_tool_execute_error(ctx, call=call, tool_def=tool_def, args=args, error=error)
```

### CAPABILITY_TYPES

```python
CAPABILITY_TYPES: dict[
    str, type[AbstractCapability[Any]]
] = {
    name: cls
    for cls in (
        BuiltinTool,
        HistoryProcessor,
        ImageGeneration,
        MCP,
        PrefixTools,
        PrepareTools,
        Thinking,
        Toolset,
        WebFetch,
        WebSearch,
    )
    if (name := (get_serialization_name())) is not None
}
```

Registry of all capability types that have a serialization name, mapping name to class.
