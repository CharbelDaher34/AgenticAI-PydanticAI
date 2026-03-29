# Agent Specs

Agent specs let you define agents declaratively in YAML or JSON — [model](https://ai.pydantic.dev/models/overview/index.md), [instructions](https://ai.pydantic.dev/agent/#instructions), [capabilities](https://ai.pydantic.dev/capabilities/index.md), and all. One line to load, no Python agent construction code required.

This is useful for:

- Separating agent configuration from application code
- Letting non-developers (prompt engineers, domain experts) configure agents
- Storing agent definitions alongside other config files
- Sharing agent configurations across teams or projects

## Defining a spec

A spec file defines the agent's configuration in YAML or JSON:

agent.yaml

```yaml
model: anthropic:claude-opus-4-6
instructions: You are a helpful research assistant.
model_settings:
  max_tokens: 8192
capabilities:
  - WebSearch
  - Thinking:
      effort: high
```

## Loading specs

Agent.from_file loads a spec from a YAML or JSON file and constructs an agent:

from_file_example.py

```python
from pydantic_ai import Agent

agent = Agent.from_file('agent.yaml')
```

Agent.from_spec accepts a dict or AgentSpec instance and supports additional keyword arguments that supplement or override the spec:

from_spec_example.py

```python
from dataclasses import dataclass

from pydantic_ai import Agent


@dataclass
class UserContext:
    user_name: str


agent = Agent.from_spec(
    {
        'model': 'anthropic:claude-opus-4-6',
        'instructions': 'You are helping {{user_name}}.',
        'capabilities': ['WebSearch'],
    },
    deps_type=UserContext,
)
```

Keyword arguments interact with spec fields as follows:

- **Scalar fields** (`model`, `name`, `retries`, `end_strategy`, etc.) — the keyword argument overrides the spec value when provided.
- **`instructions`** — merged: spec instructions come first, then keyword argument instructions.
- **`capabilities`** — merged: spec capabilities come first, then keyword argument capabilities.
- **`model_settings`** — merged additively: keyword argument settings override matching spec settings.
- **`output_type`** — takes precedence over `output_schema` from the spec.

When `deps_type` is passed, [template strings](#template-strings) in the spec's `instructions`, `description`, and capability arguments are compiled and validated against the deps type at construction time.

For more control over spec loading, use AgentSpec.from_file to load the spec separately before passing it to `Agent.from_spec`.

## Template strings

TemplateStr provides Handlebars-style templates (`{{variable}}`) that are rendered against the agent's [dependencies](https://ai.pydantic.dev/dependencies/index.md) at runtime. In spec files, strings containing `{{` are automatically converted to template strings:

```yaml
instructions: "You are assisting {{name}}, who is a {{role}}."
```

Template variables are resolved from the fields of the `deps` object. When a `deps_type` (or [`deps_schema`](#deps_schema)) is provided, template variable names are validated at construction time.

In Python code, TemplateStr can be used explicitly, but a callable with RunContext is generally preferred for IDE autocomplete and type checking:

[Learn about Gateway](https://ai.pydantic.dev/gateway) template_instructions.py

```python
from dataclasses import dataclass

from pydantic_ai import Agent, TemplateStr


@dataclass
class UserProfile:
    name: str
    role: str


agent = Agent(
    'gateway/openai:gpt-5.2',
    deps_type=UserProfile,
    instructions=TemplateStr('You are assisting {{name}}, who is a {{role}}.'),
)
result = agent.run_sync('hello', deps=UserProfile(name='Alice', role='engineer'))
print(result.output)
#> Hello! How can I help you today?
```

template_instructions.py

```python
from dataclasses import dataclass

from pydantic_ai import Agent, TemplateStr


@dataclass
class UserProfile:
    name: str
    role: str


agent = Agent(
    'openai:gpt-5.2',
    deps_type=UserProfile,
    instructions=TemplateStr('You are assisting {{name}}, who is a {{role}}.'),
)
result = agent.run_sync('hello', deps=UserProfile(name='Alice', role='engineer'))
print(result.output)
#> Hello! How can I help you today?
```

## Capability spec syntax

Capabilities in specs support three forms:

- `'MyCapability'` — no arguments, calls `MyCapability.from_spec()`
- `{'MyCapability': value}` — single positional argument, calls `MyCapability.from_spec(value)`
- `{'MyCapability': {key: value, ...}}` — keyword arguments, calls `MyCapability.from_spec(**kwargs)`

## Custom capabilities in specs

See [Publishing capabilities](https://ai.pydantic.dev/capabilities/#publishing-capabilities) for how to make custom capabilities work with agent specs.

## `AgentSpec` reference

The AgentSpec model represents the full spec structure:

| Field            | Type                       | Description                                                                                                |
| ---------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `model`          | `str`                      | [Model](https://ai.pydantic.dev/models/overview/index.md) name (required)                                  |
| `name`           | `str \| None`              | Agent name                                                                                                 |
| `description`    | `str \| None`              | Agent description (supports [templates](#template-strings))                                                |
| `instructions`   | `str \| list[str] \| None` | [Instructions](https://ai.pydantic.dev/agent/#instructions) (supports [templates](#template-strings))      |
| `model_settings` | `dict \| None`             | [Model settings](https://ai.pydantic.dev/agent/#model-run-settings)                                        |
| `capabilities`   | `list`                     | [Capabilities](https://ai.pydantic.dev/capabilities/index.md) (see [spec syntax](#capability-spec-syntax)) |
| `deps_schema`    | `dict \| None`             | JSON Schema for [template string](#template-strings) validation (see below)                                |
| `output_schema`  | `dict \| None`             | JSON Schema for [structured output](https://ai.pydantic.dev/output/index.md) (see below)                   |
| `retries`        | `int`                      | Default [tool retries](https://ai.pydantic.dev/retries/index.md) (default: `1`)                            |
| `output_retries` | `int \| None`              | [Output](https://ai.pydantic.dev/output/index.md) validation retries                                       |
| `end_strategy`   | `EndStrategy`              | When to stop (`'early'` or `'exhaustive'`)                                                                 |
| `tool_timeout`   | `float \| None`            | Default [tool](https://ai.pydantic.dev/tools/index.md) timeout in seconds                                  |
| `instrument`     | `bool \| None`             | Enable [Logfire](https://ai.pydantic.dev/logfire/index.md) instrumentation                                 |
| `metadata`       | `dict \| None`             | Agent [metadata](https://ai.pydantic.dev/agent/#run-metadata)                                              |

### `deps_schema`

When loading a spec file without a Python `deps_type`, `deps_schema` provides a JSON Schema that validates [template string](#template-strings) variable names at construction time. It does **not** validate the actual deps object at runtime — it only ensures that template variables like `{{user_name}}` correspond to properties defined in the schema.

### `output_schema`

When provided (and no `output_type` keyword argument is passed to `from_spec`), `output_schema` defines the structure the model should produce as its final output. Under the hood, it creates a StructuredDict output type: the JSON Schema is sent to the model API so the model knows what structure to produce, and the response is returned as a `dict[str, Any]`.

Note

The model's response is not validated against the schema's `properties` or `required` fields — it is accepted as a plain dict. The schema serves as an instruction to the model, not a runtime validation constraint.

agent_with_schema.yaml

```yaml
model: anthropic:claude-opus-4-6
deps_schema:
  type: object
  properties:
    user_name:
      type: string
  required: [user_name]
output_schema:
  type: object
  properties:
    answer:
      type: string
    confidence:
      type: number
  required: [answer, confidence]
instructions: "You are helping {{user_name}}. Always include a confidence score."
capabilities:
  - WebSearch
```

## Saving specs

AgentSpec.to_file saves a spec to YAML or JSON and optionally generates a companion JSON Schema file for editor autocompletion:

save_spec_example.py

```python
from pydantic_ai import AgentSpec

spec = AgentSpec(
    model='anthropic:claude-opus-4-6',
    instructions='You are a helpful assistant.',
    capabilities=['WebSearch'],
)
spec.to_file('agent.yaml')
# Also generates ./agent_schema.json for editor autocompletion
```

The generated JSON Schema file enables autocompletion and validation in editors that support the [YAML Language Server](https://github.com/redhat-developer/yaml-language-server) protocol. Pass `schema_path=None` to skip schema generation.
