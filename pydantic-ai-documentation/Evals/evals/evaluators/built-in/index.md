# Built-in Evaluators

Pydantic Evals provides several built-in evaluators for common evaluation tasks.

## Comparison Evaluators

### EqualsExpected

Check if the output exactly equals the expected output from the case.

```python
from pydantic_evals.evaluators import EqualsExpected

EqualsExpected()
```

**Parameters:** None

**Returns:** `bool` - `True` if `ctx.output == ctx.expected_output`

**Example:**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected

dataset = Dataset(
    cases=[
        Case(
            name='addition',
            inputs='2 + 2',
            expected_output='4',
        ),
    ],
    evaluators=[EqualsExpected()],
)
```

**Notes:**

- Skips evaluation if `expected_output` is `None` (returns empty dict `{}`)
- Uses Python's `==` operator, so works with any comparable types
- For structured data, considers nested equality

______________________________________________________________________

### Equals

Check if the output equals a specific value.

```python
from pydantic_evals.evaluators import Equals

Equals(value='expected_result')
```

**Parameters:**

- `value` (Any): The value to compare against
- `evaluation_name` (str | None): Custom name for this evaluation in reports

**Returns:** `bool` - `True` if `ctx.output == value`

**Example:**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Equals

# Check output is always "success"
dataset = Dataset(
    cases=[Case(inputs='test')],
    evaluators=[
        Equals(value='success', evaluation_name='is_success'),
    ],
)
```

**Use Cases:**

- Checking for sentinel values
- Validating consistent outputs
- Testing classification into specific categories

______________________________________________________________________

### Contains

Check if the output contains a specific value or substring.

```python
from pydantic_evals.evaluators import Contains

Contains(
    value='substring',
    case_sensitive=True,
    as_strings=False,
)
```

**Parameters:**

- `value` (Any): The value to search for
- `case_sensitive` (bool): Case-sensitive comparison for strings (default: `True`)
- `as_strings` (bool): Convert both values to strings before checking (default: `False`)
- `evaluation_name` (str | None): Custom name for this evaluation in reports

**Returns:** EvaluationReason - Pass/fail with explanation

**Behavior:**

For **strings**: checks substring containment

- `Contains(value='hello', case_sensitive=False)`
- Matches: "Hello World", "say hello", "HELLO"
- Doesn't match: "hi there"

For **lists/tuples**: checks membership

- `Contains(value='apple')`
- Matches: `['apple', 'banana']`, `('apple',)`
- Doesn't match: `['apples', 'orange']`

For **dicts**: checks key-value pairs

- `Contains(value={'name': 'Alice'})`
- Matches: `{'name': 'Alice', 'age': 30}`
- Doesn't match: `{'name': 'Bob'}`

**Example:**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains

dataset = Dataset(
    cases=[Case(inputs='test')],
    evaluators=[
        # Check for required keywords
        Contains(value='terms and conditions', case_sensitive=False),
        # Check for PII (fail if found)
        # Note: Use a custom evaluator that returns False when PII found
    ],
)
```

**Use Cases:**

- Required content verification
- Keyword detection
- PII/sensitive data detection
- Multi-value validation

______________________________________________________________________

## Type Validation

### IsInstance

Check if the output is an instance of a type with the given name.

```python
from pydantic_evals.evaluators import IsInstance

IsInstance(type_name='str')
```

**Parameters:**

- `type_name` (str): The type name to check (uses `__name__` or `__qualname__`)
- `evaluation_name` (str | None): Custom name for this evaluation in reports

**Returns:** EvaluationReason - Pass/fail with type information

**Example:**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance

dataset = Dataset(
    cases=[Case(inputs='test')],
    evaluators=[
        # Check output is always a string
        IsInstance(type_name='str'),
        # Check for Pydantic model
        IsInstance(type_name='MyModel'),
        # Check for dict
        IsInstance(type_name='dict'),
    ],
)
```

**Notes:**

- Matches against both `__name__` and `__qualname__` of the type
- Works with built-in types (`str`, `int`, `dict`, `list`, etc.)
- Works with custom classes and Pydantic models
- Checks the entire MRO (Method Resolution Order) for inheritance

**Use Cases:**

- Format validation
- Structured output verification
- Type consistency checks

______________________________________________________________________

## Performance Evaluation

### MaxDuration

Check if task execution time is under a maximum threshold.

```python
from datetime import timedelta

from pydantic_evals.evaluators import MaxDuration

MaxDuration(seconds=2.0)
# or
MaxDuration(seconds=timedelta(seconds=2))
```

**Parameters:**

- `seconds` (float | timedelta): Maximum allowed duration

**Returns:** `bool` - `True` if `ctx.duration <= seconds`

**Example:**

```python
from datetime import timedelta

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import MaxDuration

dataset = Dataset(
    cases=[Case(inputs='test')],
    evaluators=[
        # SLA: must respond in under 2 seconds
        MaxDuration(seconds=2.0),
        # Or using timedelta
        MaxDuration(seconds=timedelta(milliseconds=500)),
    ],
)
```

**Use Cases:**

- SLA compliance
- Performance regression testing
- Latency requirements
- Timeout validation

**See Also:** [Concurrency & Performance](https://ai.pydantic.dev/evals/how-to/concurrency/index.md)

______________________________________________________________________

## LLM-as-a-Judge

### LLMJudge

Use an LLM to evaluate subjective qualities based on a rubric.

```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(
    rubric='Response is accurate and helpful',
    model='openai:gpt-5.2',
    include_input=False,
    include_expected_output=False,
    model_settings=None,
    score=False,
    assertion={'include_reason': True},
)
```

**Parameters:**

- `rubric` (str): The evaluation criteria (required)
- `model` (Model | KnownModelName | None): Model to use (default: `'openai:gpt-5.2'`)
- `include_input` (bool): Include task inputs in the prompt (default: `False`)
- `include_expected_output` (bool): Include expected output in the prompt (default: `False`)
- `model_settings` (ModelSettings | None): Custom model settings
- `score` (OutputConfig | False): Configure score output (default: `False`)
- `assertion` (OutputConfig | False): Configure assertion output (default: includes reason)

**Returns:** Depends on `score` and `assertion` parameters (see below)

**Output Modes:**

By default, returns a **boolean assertion** with reason:

- `LLMJudge(rubric='Response is polite')`
- Returns: `{'LLMJudge_pass': EvaluationReason(value=True, reason='...')}`

Return a **score** (0.0 to 1.0) instead:

- `LLMJudge(rubric='Response quality', score={'include_reason': True}, assertion=False)`
- Returns: `{'LLMJudge_score': EvaluationReason(value=0.85, reason='...')}`

Return **both** score and assertion:

- `LLMJudge(rubric='Response quality', score={'include_reason': True}, assertion={'include_reason': True})`
- Returns: `{'LLMJudge_score': EvaluationReason(value=0.85, reason='...'), 'LLMJudge_pass': EvaluationReason(value=True, reason='...')}`

**Customize evaluation names:**

- `LLMJudge(rubric='Response is factually accurate', assertion={'evaluation_name': 'accuracy', 'include_reason': True})`
- Returns: `{'accuracy': EvaluationReason(value=True, reason='...')}`

**Example:**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    cases=[Case(inputs='test', expected_output='result')],
    evaluators=[
        # Basic accuracy check
        LLMJudge(
            rubric='Response is factually accurate',
            include_input=True,
        ),
        # Quality score with different model
        LLMJudge(
            rubric='Overall response quality',
            model='anthropic:claude-sonnet-4-6',
            score={'evaluation_name': 'quality', 'include_reason': False},
            assertion=False,
        ),
        # Check against expected output
        LLMJudge(
            rubric='Response matches the expected answer semantically',
            include_input=True,
            include_expected_output=True,
        ),
    ],
)
```

**See Also:** [LLM Judge Deep Dive](https://ai.pydantic.dev/evals/evaluators/llm-judge/index.md)

______________________________________________________________________

## Span-Based Evaluation

### HasMatchingSpan

Check if OpenTelemetry spans match a query (requires Logfire configuration).

```python
from pydantic_evals.evaluators import HasMatchingSpan

HasMatchingSpan(
    query={'name_contains': 'tool_call'},
    evaluation_name='called_tool',
)
```

**Parameters:**

- `query` (SpanQuery): Query to match against spans
- `evaluation_name` (str | None): Custom name for this evaluation in reports

**Returns:** `bool` - `True` if any span matches the query

**Example:**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import HasMatchingSpan

dataset = Dataset(
    cases=[Case(inputs='test')],
    evaluators=[
        # Check that a specific tool was called
        HasMatchingSpan(
            query={'name_contains': 'search_database'},
            evaluation_name='used_database',
        ),
        # Check for errors
        HasMatchingSpan(
            query={'has_attributes': {'error': True}},
            evaluation_name='had_errors',
        ),
        # Check duration constraints
        HasMatchingSpan(
            query={
                'name_equals': 'llm_call',
                'max_duration': 2.0,  # seconds
            },
            evaluation_name='llm_fast_enough',
        ),
    ],
)
```

**See Also:** [Span-Based Evaluation](https://ai.pydantic.dev/evals/evaluators/span-based/index.md)

______________________________________________________________________

## Built-in Report Evaluators

In addition to the case-level evaluators above, Pydantic Evals provides report evaluators that analyze entire experiment results. These are passed via the `report_evaluators` parameter on `Dataset`.

| Report Evaluator         | Purpose                         | Output            |
| ------------------------ | ------------------------------- | ----------------- |
| ConfusionMatrixEvaluator | Classification confusion matrix | `ConfusionMatrix` |
| PrecisionRecallEvaluator | PR curve with AUC               | `PrecisionRecall` |

**See:** [Report Evaluators](https://ai.pydantic.dev/evals/evaluators/report-evaluators/index.md) for full documentation, parameters, and examples, including how to write custom report evaluators that produce `ScalarResult` and `TableResult` analyses.

______________________________________________________________________

## Quick Reference Table

### Case-Level Evaluators

| Evaluator       | Purpose                   | Return Type           | Cost | Speed   |
| --------------- | ------------------------- | --------------------- | ---- | ------- |
| EqualsExpected  | Exact match with expected | `bool`                | Free | Instant |
| Equals          | Equals specific value     | `bool`                | Free | Instant |
| Contains        | Contains value/substring  | `bool` + reason       | Free | Instant |
| IsInstance      | Type validation           | `bool` + reason       | Free | Instant |
| MaxDuration     | Performance threshold     | `bool`                | Free | Instant |
| LLMJudge        | Subjective quality        | `bool` and/or `float` | $$   | Slow    |
| HasMatchingSpan | Behavioral check          | `bool`                | Free | Fast    |

### Report-Level Evaluators

| Evaluator                | Purpose               | Output Type       | Cost | Speed   |
| ------------------------ | --------------------- | ----------------- | ---- | ------- |
| ConfusionMatrixEvaluator | Classification matrix | `ConfusionMatrix` | Free | Instant |
| PrecisionRecallEvaluator | PR curve with AUC     | `PrecisionRecall` | Free | Instant |

## Combining Evaluators

Best practice is to combine fast deterministic checks with slower LLM evaluations:

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import (
    Contains,
    IsInstance,
    LLMJudge,
    MaxDuration,
)

dataset = Dataset(
    cases=[Case(inputs='test')],
    evaluators=[
        # Fast checks first (fail fast)
        IsInstance(type_name='str'),
        Contains(value='required_field'),
        MaxDuration(seconds=2.0),
        # Expensive LLM checks last
        LLMJudge(rubric='Response is helpful and accurate'),
    ],
)
```

This approach:

1. Catches format/structure issues immediately
1. Validates required content quickly
1. Only runs expensive LLM evaluation if basic checks pass
1. Provides comprehensive quality assessment

## Next Steps

- **[LLM Judge](https://ai.pydantic.dev/evals/evaluators/llm-judge/index.md)** - Deep dive on LLM-as-a-Judge evaluation
- **[Custom Evaluators](https://ai.pydantic.dev/evals/evaluators/custom/index.md)** - Write your own evaluation logic
- **[Report Evaluators](https://ai.pydantic.dev/evals/evaluators/report-evaluators/index.md)** - Experiment-wide analyses (confusion matrices, PR curves, etc.)
- **[Span-Based Evaluation](https://ai.pydantic.dev/evals/evaluators/span-based/index.md)** - Using OpenTelemetry spans for behavioral checks
