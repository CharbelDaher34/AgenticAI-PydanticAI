# Extensibility

Pydantic AI is designed to be extended. [Capabilities](https://ai.pydantic.dev/capabilities/index.md) are the primary extension point — they bundle tools, lifecycle hooks, instructions, and model settings into reusable units that can be shared across agents, packaged as libraries, and loaded from [spec files](https://ai.pydantic.dev/agent-spec/index.md).

Beyond capabilities, Pydantic AI provides several other extension mechanisms for specialized needs.

## Capabilities

Capabilities are the recommended way to extend Pydantic AI. They are useful for:

- **Teams** building reusable internal agent components (guardrails, audit logging, authentication)
- **Package authors** shipping extensions that work across models and agents
- **Community contributors** sharing solutions to common problems

See [Capabilities](https://ai.pydantic.dev/capabilities/index.md) for using and building capabilities, and [Hooks](https://ai.pydantic.dev/hooks/index.md) for the lightweight decorator-based approach.

## Publishing capability packages

To make a capability installable and usable in [agent specs](https://ai.pydantic.dev/agent-spec/index.md):

1. **Implement get_serialization_name()** — defaults to the class name. Return `None` to opt out of spec support.
1. **Implement from_spec()** — defaults to `cls(*args, **kwargs)`. Override when your constructor takes non-serializable types.
1. **Package naming** — use the `pydantic-ai-` prefix (e.g. `pydantic-ai-guardrails`) so users can find your package.
1. **Registration** — users pass custom capability types via `custom_capability_types` on Agent.from_spec or Agent.from_file.

```python
from pydantic_ai import Agent

from my_package import MyCapability

agent = Agent.from_file('agent.yaml', custom_capability_types=[MyCapability])
```

See [Custom capabilities in specs](https://ai.pydantic.dev/agent-spec/#custom-capabilities-in-specs) for implementation details.

## Third-party ecosystem

### Capabilities

[Capabilities](https://ai.pydantic.dev/capabilities/index.md) are the recommended extension mechanism for packages that need to bundle tools with hooks, instructions, or model settings. See [Third-party capabilities](https://ai.pydantic.dev/capabilities/#third-party-capabilities) for community packages.

### Toolsets

Many third-party extensions are available as [toolsets](https://ai.pydantic.dev/toolsets/index.md), which can also be wrapped as [capabilities](https://ai.pydantic.dev/capabilities/index.md) to take advantage of hooks, instructions, and model settings. See [Third-party toolsets](https://ai.pydantic.dev/toolsets/#third-party-toolsets) for the full list.

## Other extension points

### Custom toolsets

For specialized tool execution needs (custom transport, tool filtering, execution wrapping), implement AbstractToolset or subclass WrapperToolset:

- AbstractToolset — full control over tool definitions and execution
- WrapperToolset — delegates to a wrapped toolset, override specific methods

See [Building a Custom Toolset](https://ai.pydantic.dev/toolsets/#building-a-custom-toolset) for details.

Tip

If your toolset also needs to provide instructions, model settings, or hooks, consider building a [custom capability](https://ai.pydantic.dev/capabilities/#building-custom-capabilities) instead.

### Custom models

For connecting to model providers not yet supported by Pydantic AI, implement Model:

- Model — the base interface for model implementations
- WrapperModel — delegates to a wrapped model, useful for adding instrumentation or transformations

See [Custom Models](https://ai.pydantic.dev/models/overview/#custom-models) for details.

### Custom agents

For custom agent behavior, subclass AbstractAgent or WrapperAgent:

- AbstractAgent — the base interface for agent implementations, providing `run`, `run_sync`, and `run_stream`
- WrapperAgent — delegates to a wrapped agent, useful for adding pre/post-processing or context management
