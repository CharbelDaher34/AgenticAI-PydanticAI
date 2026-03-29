# `pydantic_evals.evaluators`

### Contains

Bases: `Evaluator[object, object, object]`

Check if the output contains the expected output.

For strings, checks if expected_output is a substring of output. For lists/tuples, checks if expected_output is in output. For dicts, checks if all key-value pairs in expected_output are in output. For model-like types (BaseModel, dataclasses), converts to a dict and checks key-value pairs.

Note: case_sensitive only applies when both the value and output are strings.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class Contains(Evaluator[object, object, object]):
    """Check if the output contains the expected output.

    For strings, checks if expected_output is a substring of output.
    For lists/tuples, checks if expected_output is in output.
    For dicts, checks if all key-value pairs in expected_output are in output.
    For model-like types (BaseModel, dataclasses), converts to a dict and checks key-value pairs.

    Note: case_sensitive only applies when both the value and output are strings.
    """

    value: Any
    case_sensitive: bool = True
    as_strings: bool = False
    evaluation_name: str | None = field(default=None)

    def evaluate(
        self,
        ctx: EvaluatorContext[object, object, object],
    ) -> EvaluationReason:
        # Convert objects to strings if requested
        failure_reason: str | None = None
        as_strings = self.as_strings or (isinstance(self.value, str) and isinstance(ctx.output, str))
        if as_strings:
            output_str = str(ctx.output)
            expected_str = str(self.value)

            if not self.case_sensitive:
                output_str = output_str.lower()
                expected_str = expected_str.lower()

            failure_reason: str | None = None
            if expected_str not in output_str:
                output_trunc = _truncated_repr(output_str, max_length=100)
                expected_trunc = _truncated_repr(expected_str, max_length=100)
                failure_reason = f'Output string {output_trunc} does not contain expected string {expected_trunc}'
            return EvaluationReason(value=failure_reason is None, reason=failure_reason)

        try:
            # Handle different collection types
            output_type = type(ctx.output)
            output_is_model_like = is_model_like(output_type)
            if isinstance(ctx.output, dict) or output_is_model_like:
                if output_is_model_like:
                    adapter: TypeAdapter[Any] = TypeAdapter(output_type)
                    output_dict = adapter.dump_python(ctx.output)  # pyright: ignore[reportUnknownMemberType]
                else:
                    # Cast to Any to avoid type checking issues
                    output_dict = cast(dict[Any, Any], ctx.output)  # pyright: ignore[reportUnknownMemberType]

                if isinstance(self.value, dict):
                    # Cast to Any to avoid type checking issues
                    expected_dict = cast(dict[Any, Any], self.value)  # pyright: ignore[reportUnknownMemberType]
                    for k in expected_dict:
                        if k not in output_dict:
                            k_trunc = _truncated_repr(k, max_length=30)
                            failure_reason = f'Output does not contain expected key {k_trunc}'
                            break
                        elif output_dict[k] != expected_dict[k]:
                            k_trunc = _truncated_repr(k, max_length=30)
                            output_v_trunc = _truncated_repr(output_dict[k], max_length=100)
                            expected_v_trunc = _truncated_repr(expected_dict[k], max_length=100)
                            failure_reason = (
                                f'Output has different value for key {k_trunc}: {output_v_trunc} != {expected_v_trunc}'
                            )
                            break
                else:
                    if self.value not in output_dict:
                        output_trunc = _truncated_repr(output_dict, max_length=200)
                        failure_reason = f'Output {output_trunc} does not contain provided value as a key'
            elif self.value not in ctx.output:  # pyright: ignore[reportOperatorIssue]  # will be handled by except block
                output_trunc = _truncated_repr(ctx.output, max_length=200)
                failure_reason = f'Output {output_trunc} does not contain provided value'
        except (TypeError, ValueError) as e:
            failure_reason = f'Containment check failed: {e}'

        return EvaluationReason(value=failure_reason is None, reason=failure_reason)
```

### Equals

Bases: `Evaluator[object, object, object]`

Check if the output exactly equals the provided value.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class Equals(Evaluator[object, object, object]):
    """Check if the output exactly equals the provided value."""

    value: Any
    evaluation_name: str | None = field(default=None)

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool:
        return ctx.output == self.value
```

### EqualsExpected

Bases: `Evaluator[object, object, object]`

Check if the output exactly equals the expected output.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class EqualsExpected(Evaluator[object, object, object]):
    """Check if the output exactly equals the expected output."""

    evaluation_name: str | None = field(default=None)

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool | dict[str, bool]:
        if ctx.expected_output is None:
            return {}  # Only compare if expected output is provided
        return ctx.output == ctx.expected_output
```

### HasMatchingSpan

Bases: `Evaluator[object, object, object]`

Check if the span tree contains a span that matches the specified query.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class HasMatchingSpan(Evaluator[object, object, object]):
    """Check if the span tree contains a span that matches the specified query."""

    query: SpanQuery
    evaluation_name: str | None = field(default=None)

    def evaluate(
        self,
        ctx: EvaluatorContext[object, object, object],
    ) -> bool:
        return ctx.span_tree.any(self.query)
```

### IsInstance

Bases: `Evaluator[object, object, object]`

Check if the output is an instance of a type with the given name.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class IsInstance(Evaluator[object, object, object]):
    """Check if the output is an instance of a type with the given name."""

    type_name: str
    evaluation_name: str | None = field(default=None)

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> EvaluationReason:
        output = ctx.output
        for cls in type(output).__mro__:
            if cls.__name__ == self.type_name or cls.__qualname__ == self.type_name:
                return EvaluationReason(value=True)

        reason = f'output is of type {type(output).__name__}'
        if type(output).__qualname__ != type(output).__name__:
            reason += f' (qualname: {type(output).__qualname__})'
        return EvaluationReason(value=False, reason=reason)
```

### LLMJudge

Bases: `Evaluator[object, object, object]`

Judge whether the output of a language model meets the criteria of a provided rubric.

If you do not specify a model, it uses the default model for judging. This starts as 'openai:gpt-5.2', but can be overridden by calling set_default_judge_model.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class LLMJudge(Evaluator[object, object, object]):
    """Judge whether the output of a language model meets the criteria of a provided rubric.

    If you do not specify a model, it uses the default model for judging. This starts as 'openai:gpt-5.2', but can be
    overridden by calling [`set_default_judge_model`][pydantic_evals.evaluators.llm_as_a_judge.set_default_judge_model].
    """

    rubric: str
    model: models.Model | models.KnownModelName | str | None = None
    include_input: bool = False
    include_expected_output: bool = False
    model_settings: ModelSettings | None = None
    score: OutputConfig | Literal[False] = False
    assertion: OutputConfig | Literal[False] = field(default_factory=lambda: OutputConfig(include_reason=True))

    async def evaluate(
        self,
        ctx: EvaluatorContext[object, object, object],
    ) -> EvaluatorOutput:
        if self.include_input:
            if self.include_expected_output:
                from .llm_as_a_judge import judge_input_output_expected

                grading_output = await judge_input_output_expected(
                    ctx.inputs, ctx.output, ctx.expected_output, self.rubric, self.model, self.model_settings
                )
            else:
                from .llm_as_a_judge import judge_input_output

                grading_output = await judge_input_output(
                    ctx.inputs, ctx.output, self.rubric, self.model, self.model_settings
                )
        else:
            if self.include_expected_output:
                from .llm_as_a_judge import judge_output_expected

                grading_output = await judge_output_expected(
                    ctx.output, ctx.expected_output, self.rubric, self.model, self.model_settings
                )
            else:
                from .llm_as_a_judge import judge_output

                grading_output = await judge_output(ctx.output, self.rubric, self.model, self.model_settings)

        output: dict[str, EvaluationScalar | EvaluationReason] = {}
        include_both = self.score is not False and self.assertion is not False
        evaluation_name = self.get_default_evaluation_name()

        if self.score is not False:
            default_name = f'{evaluation_name}_score' if include_both else evaluation_name
            _update_combined_output(output, grading_output.score, grading_output.reason, self.score, default_name)

        if self.assertion is not False:
            default_name = f'{evaluation_name}_pass' if include_both else evaluation_name
            _update_combined_output(output, grading_output.pass_, grading_output.reason, self.assertion, default_name)

        return output

    def build_serialization_arguments(self):
        result = super().build_serialization_arguments()
        # always serialize the model as a string when present; use its name if it's a KnownModelName
        if (model := result.get('model')) and isinstance(model, models.Model):  # pragma: no branch
            result['model'] = model.model_id

        # Note: this may lead to confusion if you try to serialize-then-deserialize with a custom model.
        # I expect that is rare enough to be worth not solving yet, but common enough that we probably will want to
        # solve it eventually. I'm imagining some kind of model registry, but don't want to work out the details yet.
        return result
```

### MaxDuration

Bases: `Evaluator[object, object, object]`

Check if the execution time is under the specified maximum.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
@dataclass(repr=False)
class MaxDuration(Evaluator[object, object, object]):
    """Check if the execution time is under the specified maximum."""

    seconds: float | timedelta

    def evaluate(self, ctx: EvaluatorContext[object, object, object]) -> bool:
        duration = timedelta(seconds=ctx.duration)
        seconds = self.seconds
        if not isinstance(seconds, timedelta):
            seconds = timedelta(seconds=seconds)
        return duration <= seconds
```

### OutputConfig

Bases: `TypedDict`

Configuration for the score and assertion outputs of the LLMJudge evaluator.

Source code in `pydantic_evals/pydantic_evals/evaluators/common.py`

```python
class OutputConfig(TypedDict, total=False):
    """Configuration for the score and assertion outputs of the LLMJudge evaluator."""

    evaluation_name: str
    include_reason: bool
```

### EvaluatorContext

Bases: `Generic[InputsT, OutputT, MetadataT]`

Context for evaluating a task execution.

An instance of this class is the sole input to all Evaluators. It contains all the information needed to evaluate the task execution, including inputs, outputs, metadata, and telemetry data.

Evaluators use this context to access the task inputs, actual output, expected output, and other information when evaluating the result of the task execution.

Example:

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ExactMatch(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        # Use the context to access task inputs, outputs, and expected outputs
        return ctx.output == ctx.expected_output
```

Source code in `pydantic_evals/pydantic_evals/evaluators/context.py`

````python
@dataclass(kw_only=True)
class EvaluatorContext(Generic[InputsT, OutputT, MetadataT]):
    """Context for evaluating a task execution.

    An instance of this class is the sole input to all Evaluators. It contains all the information
    needed to evaluate the task execution, including inputs, outputs, metadata, and telemetry data.

    Evaluators use this context to access the task inputs, actual output, expected output, and other
    information when evaluating the result of the task execution.

    Example:
    ```python
    from dataclasses import dataclass

    from pydantic_evals.evaluators import Evaluator, EvaluatorContext


    @dataclass
    class ExactMatch(Evaluator):
        def evaluate(self, ctx: EvaluatorContext) -> bool:
            # Use the context to access task inputs, outputs, and expected outputs
            return ctx.output == ctx.expected_output
    ```
    """

    name: str | None
    """The name of the case."""
    inputs: InputsT
    """The inputs provided to the task for this case."""
    metadata: MetadataT | None
    """Metadata associated with the case, if provided. May be None if no metadata was specified."""
    expected_output: OutputT | None
    """The expected output for the case, if provided. May be None if no expected output was specified."""

    output: OutputT
    """The actual output produced by the task for this case."""
    duration: float
    """The duration of the task run for this case."""
    _span_tree: SpanTree | SpanTreeRecordingError = field(repr=False)
    """The span tree for the task run for this case.

    This will be `None` if `logfire.configure` has not been called.
    """

    attributes: dict[str, Any]
    """Attributes associated with the task run for this case.

    These can be set by calling `pydantic_evals.dataset.set_eval_attribute` in any code executed
    during the evaluation task."""
    metrics: dict[str, int | float]
    """Metrics associated with the task run for this case.

    These can be set by calling `pydantic_evals.dataset.increment_eval_metric` in any code executed
    during the evaluation task."""

    @property
    def span_tree(self) -> SpanTree:
        """Get the `SpanTree` for this task execution.

        The span tree is a graph where each node corresponds to an OpenTelemetry span recorded during the task
        execution, including timing information and any custom spans created during execution.

        Returns:
            The span tree for the task execution.

        Raises:
            SpanTreeRecordingError: If spans were not captured during execution of the task, e.g. due to not having
                the necessary dependencies installed.
        """
        if isinstance(self._span_tree, SpanTreeRecordingError):
            # In this case, there was a reason we couldn't record the SpanTree. We raise that now
            raise self._span_tree
        return self._span_tree
````

#### name

```python
name: str | None
```

The name of the case.

#### inputs

```python
inputs: InputsT
```

The inputs provided to the task for this case.

#### metadata

```python
metadata: MetadataT | None
```

Metadata associated with the case, if provided. May be None if no metadata was specified.

#### expected_output

```python
expected_output: OutputT | None
```

The expected output for the case, if provided. May be None if no expected output was specified.

#### output

```python
output: OutputT
```

The actual output produced by the task for this case.

#### duration

```python
duration: float
```

The duration of the task run for this case.

#### attributes

```python
attributes: dict[str, Any]
```

Attributes associated with the task run for this case.

These can be set by calling `pydantic_evals.dataset.set_eval_attribute` in any code executed during the evaluation task.

#### metrics

```python
metrics: dict[str, int | float]
```

Metrics associated with the task run for this case.

These can be set by calling `pydantic_evals.dataset.increment_eval_metric` in any code executed during the evaluation task.

#### span_tree

```python
span_tree: SpanTree
```

Get the `SpanTree` for this task execution.

The span tree is a graph where each node corresponds to an OpenTelemetry span recorded during the task execution, including timing information and any custom spans created during execution.

Returns:

| Type       | Description                           |
| ---------- | ------------------------------------- |
| `SpanTree` | The span tree for the task execution. |

Raises:

| Type                     | Description                                                                                                           |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `SpanTreeRecordingError` | If spans were not captured during execution of the task, e.g. due to not having the necessary dependencies installed. |

### EvaluationReason

The result of running an evaluator with an optional explanation.

Contains a scalar value and an optional "reason" explaining the value.

Parameters:

| Name     | Type               | Description                                                               | Default                                           |
| -------- | ------------------ | ------------------------------------------------------------------------- | ------------------------------------------------- |
| `value`  | `EvaluationScalar` | The scalar result of the evaluation (boolean, integer, float, or string). | *required*                                        |
| `reason` | \`str              | None\`                                                                    | An optional explanation of the evaluation result. |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@dataclass
class EvaluationReason:
    """The result of running an evaluator with an optional explanation.

    Contains a scalar value and an optional "reason" explaining the value.

    Args:
        value: The scalar result of the evaluation (boolean, integer, float, or string).
        reason: An optional explanation of the evaluation result.
    """

    value: EvaluationScalar
    reason: str | None = None
```

### EvaluationResult

Bases: `Generic[EvaluationScalarT]`

The details of an individual evaluation result.

Contains the name, value, reason, and source evaluator for a single evaluation.

Parameters:

| Name     | Type                | Description                                          | Default                                           |
| -------- | ------------------- | ---------------------------------------------------- | ------------------------------------------------- |
| `name`   | `str`               | The name of the evaluation.                          | *required*                                        |
| `value`  | `EvaluationScalarT` | The scalar result of the evaluation.                 | *required*                                        |
| `reason` | \`str               | None\`                                               | An optional explanation of the evaluation result. |
| `source` | `EvaluatorSpec`     | The spec of the evaluator that produced this result. | *required*                                        |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@dataclass
class EvaluationResult(Generic[EvaluationScalarT]):
    """The details of an individual evaluation result.

    Contains the name, value, reason, and source evaluator for a single evaluation.

    Args:
        name: The name of the evaluation.
        value: The scalar result of the evaluation.
        reason: An optional explanation of the evaluation result.
        source: The spec of the evaluator that produced this result.
    """

    name: str
    value: EvaluationScalarT
    reason: str | None
    source: EvaluatorSpec

    def downcast(self, *value_types: type[T]) -> EvaluationResult[T] | None:
        """Attempt to downcast this result to a more specific type.

        Args:
            *value_types: The types to check the value against.

        Returns:
            A downcast version of this result if the value is an instance of one of the given types,
            otherwise None.
        """
        # Check if value matches any of the target types, handling bool as a special case
        for value_type in value_types:
            if isinstance(self.value, value_type):
                # Only match bool with explicit bool type
                if isinstance(self.value, bool) and value_type is not bool:
                    continue
                return cast(EvaluationResult[T], self)
        return None
```

#### downcast

```python
downcast(
    *value_types: type[T],
) -> EvaluationResult[T] | None
```

Attempt to downcast this result to a more specific type.

Parameters:

| Name           | Type      | Description                           | Default |
| -------------- | --------- | ------------------------------------- | ------- |
| `*value_types` | `type[T]` | The types to check the value against. | `()`    |

Returns:

| Type                  | Description |
| --------------------- | ----------- |
| \`EvaluationResult[T] | None\`      |
| \`EvaluationResult[T] | None\`      |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
def downcast(self, *value_types: type[T]) -> EvaluationResult[T] | None:
    """Attempt to downcast this result to a more specific type.

    Args:
        *value_types: The types to check the value against.

    Returns:
        A downcast version of this result if the value is an instance of one of the given types,
        otherwise None.
    """
    # Check if value matches any of the target types, handling bool as a special case
    for value_type in value_types:
        if isinstance(self.value, value_type):
            # Only match bool with explicit bool type
            if isinstance(self.value, bool) and value_type is not bool:
                continue
            return cast(EvaluationResult[T], self)
    return None
```

### Evaluator

Bases: `BaseEvaluator`, `Generic[InputsT, OutputT, MetadataT]`

Base class for all evaluators.

Evaluators can assess the performance of a task in a variety of ways, as a function of the EvaluatorContext.

Subclasses must implement the `evaluate` method. Note it can be defined with either `def` or `async def`.

Example:

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ExactMatch(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output == ctx.expected_output
```

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

````python
@dataclass(repr=False)
class Evaluator(BaseEvaluator, Generic[InputsT, OutputT, MetadataT]):
    """Base class for all evaluators.

    Evaluators can assess the performance of a task in a variety of ways, as a function of the EvaluatorContext.

    Subclasses must implement the `evaluate` method. Note it can be defined with either `def` or `async def`.

    Example:
    ```python
    from dataclasses import dataclass

    from pydantic_evals.evaluators import Evaluator, EvaluatorContext


    @dataclass
    class ExactMatch(Evaluator):
        def evaluate(self, ctx: EvaluatorContext) -> bool:
            return ctx.output == ctx.expected_output
    ```
    """

    @classmethod
    @deprecated('`name` has been renamed, use `get_serialization_name` instead.')
    def name(cls) -> str:
        """`name` has been renamed, use `get_serialization_name` instead."""
        return cls.get_serialization_name()

    def get_default_evaluation_name(self) -> str:
        """Return the default name to use in reports for the output of this evaluator.

        By default, if the evaluator has an attribute called `evaluation_name` of type string, that will be used.
        Otherwise, the serialization name of the evaluator (which is usually the class name) will be used.

        This can be overridden to get a more descriptive name in evaluation reports, e.g. using instance information.

        Note that evaluators that return a mapping of results will always use the keys of that mapping as the names
        of the associated evaluation results.
        """
        evaluation_name = getattr(self, 'evaluation_name', None)
        if isinstance(evaluation_name, str):
            # If the evaluator has an attribute `name` of type string, use that
            return evaluation_name

        return self.get_serialization_name()

    @abstractmethod
    def evaluate(
        self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]
    ) -> EvaluatorOutput | Awaitable[EvaluatorOutput]:  # pragma: no cover
        """Evaluate the task output in the given context.

        This is the main evaluation method that subclasses must implement. It can be either synchronous
        or asynchronous, returning either an EvaluatorOutput directly or an Awaitable[EvaluatorOutput].

        Args:
            ctx: The context containing the inputs, outputs, and metadata for evaluation.

        Returns:
            The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
            of evaluation names to either of those. Can be returned either synchronously or as an
            awaitable for asynchronous evaluation.
        """
        raise NotImplementedError('You must implement `evaluate`.')

    def evaluate_sync(self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]) -> EvaluatorOutput:
        """Run the evaluator synchronously, handling both sync and async implementations.

        This method ensures synchronous execution by running any async evaluate implementation
        to completion using run_until_complete.

        Args:
            ctx: The context containing the inputs, outputs, and metadata for evaluation.

        Returns:
            The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
            of evaluation names to either of those.
        """
        output = self.evaluate(ctx)
        if inspect.iscoroutine(output):  # pragma: no cover
            return get_event_loop().run_until_complete(output)
        else:
            return cast(EvaluatorOutput, output)

    async def evaluate_async(self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]) -> EvaluatorOutput:
        """Run the evaluator asynchronously, handling both sync and async implementations.

        This method ensures asynchronous execution by properly awaiting any async evaluate
        implementation. For synchronous implementations, it returns the result directly.

        Args:
            ctx: The context containing the inputs, outputs, and metadata for evaluation.

        Returns:
            The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
            of evaluation names to either of those.
        """
        # Note: If self.evaluate is synchronous, but you need to prevent this from blocking, override this method with:
        # return await anyio.to_thread.run_sync(self.evaluate, ctx)
        output = self.evaluate(ctx)
        if inspect.iscoroutine(output):
            return await output
        else:
            return cast(EvaluatorOutput, output)
````

#### name

```python
name() -> str
```

Deprecated

`name` has been renamed, use `get_serialization_name` instead.

`name` has been renamed, use `get_serialization_name` instead.

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@classmethod
@deprecated('`name` has been renamed, use `get_serialization_name` instead.')
def name(cls) -> str:
    """`name` has been renamed, use `get_serialization_name` instead."""
    return cls.get_serialization_name()
```

#### get_default_evaluation_name

```python
get_default_evaluation_name() -> str
```

Return the default name to use in reports for the output of this evaluator.

By default, if the evaluator has an attribute called `evaluation_name` of type string, that will be used. Otherwise, the serialization name of the evaluator (which is usually the class name) will be used.

This can be overridden to get a more descriptive name in evaluation reports, e.g. using instance information.

Note that evaluators that return a mapping of results will always use the keys of that mapping as the names of the associated evaluation results.

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
def get_default_evaluation_name(self) -> str:
    """Return the default name to use in reports for the output of this evaluator.

    By default, if the evaluator has an attribute called `evaluation_name` of type string, that will be used.
    Otherwise, the serialization name of the evaluator (which is usually the class name) will be used.

    This can be overridden to get a more descriptive name in evaluation reports, e.g. using instance information.

    Note that evaluators that return a mapping of results will always use the keys of that mapping as the names
    of the associated evaluation results.
    """
    evaluation_name = getattr(self, 'evaluation_name', None)
    if isinstance(evaluation_name, str):
        # If the evaluator has an attribute `name` of type string, use that
        return evaluation_name

    return self.get_serialization_name()
```

#### evaluate

```python
evaluate(
    ctx: EvaluatorContext[InputsT, OutputT, MetadataT],
) -> EvaluatorOutput | Awaitable[EvaluatorOutput]
```

Evaluate the task output in the given context.

This is the main evaluation method that subclasses must implement. It can be either synchronous or asynchronous, returning either an EvaluatorOutput directly or an Awaitable[EvaluatorOutput].

Parameters:

| Name  | Type                                            | Description                                                              | Default    |
| ----- | ----------------------------------------------- | ------------------------------------------------------------------------ | ---------- |
| `ctx` | `EvaluatorContext[InputsT, OutputT, MetadataT]` | The context containing the inputs, outputs, and metadata for evaluation. | *required* |

Returns:

| Type              | Description                  |
| ----------------- | ---------------------------- |
| \`EvaluatorOutput | Awaitable[EvaluatorOutput]\` |
| \`EvaluatorOutput | Awaitable[EvaluatorOutput]\` |
| \`EvaluatorOutput | Awaitable[EvaluatorOutput]\` |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@abstractmethod
def evaluate(
    self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]
) -> EvaluatorOutput | Awaitable[EvaluatorOutput]:  # pragma: no cover
    """Evaluate the task output in the given context.

    This is the main evaluation method that subclasses must implement. It can be either synchronous
    or asynchronous, returning either an EvaluatorOutput directly or an Awaitable[EvaluatorOutput].

    Args:
        ctx: The context containing the inputs, outputs, and metadata for evaluation.

    Returns:
        The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
        of evaluation names to either of those. Can be returned either synchronously or as an
        awaitable for asynchronous evaluation.
    """
    raise NotImplementedError('You must implement `evaluate`.')
```

#### evaluate_sync

```python
evaluate_sync(
    ctx: EvaluatorContext[InputsT, OutputT, MetadataT],
) -> EvaluatorOutput
```

Run the evaluator synchronously, handling both sync and async implementations.

This method ensures synchronous execution by running any async evaluate implementation to completion using run_until_complete.

Parameters:

| Name  | Type                                            | Description                                                              | Default    |
| ----- | ----------------------------------------------- | ------------------------------------------------------------------------ | ---------- |
| `ctx` | `EvaluatorContext[InputsT, OutputT, MetadataT]` | The context containing the inputs, outputs, and metadata for evaluation. | *required* |

Returns:

| Type              | Description                                                                           |
| ----------------- | ------------------------------------------------------------------------------------- |
| `EvaluatorOutput` | The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping |
| `EvaluatorOutput` | of evaluation names to either of those.                                               |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
def evaluate_sync(self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]) -> EvaluatorOutput:
    """Run the evaluator synchronously, handling both sync and async implementations.

    This method ensures synchronous execution by running any async evaluate implementation
    to completion using run_until_complete.

    Args:
        ctx: The context containing the inputs, outputs, and metadata for evaluation.

    Returns:
        The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
        of evaluation names to either of those.
    """
    output = self.evaluate(ctx)
    if inspect.iscoroutine(output):  # pragma: no cover
        return get_event_loop().run_until_complete(output)
    else:
        return cast(EvaluatorOutput, output)
```

#### evaluate_async

```python
evaluate_async(
    ctx: EvaluatorContext[InputsT, OutputT, MetadataT],
) -> EvaluatorOutput
```

Run the evaluator asynchronously, handling both sync and async implementations.

This method ensures asynchronous execution by properly awaiting any async evaluate implementation. For synchronous implementations, it returns the result directly.

Parameters:

| Name  | Type                                            | Description                                                              | Default    |
| ----- | ----------------------------------------------- | ------------------------------------------------------------------------ | ---------- |
| `ctx` | `EvaluatorContext[InputsT, OutputT, MetadataT]` | The context containing the inputs, outputs, and metadata for evaluation. | *required* |

Returns:

| Type              | Description                                                                           |
| ----------------- | ------------------------------------------------------------------------------------- |
| `EvaluatorOutput` | The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping |
| `EvaluatorOutput` | of evaluation names to either of those.                                               |

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
async def evaluate_async(self, ctx: EvaluatorContext[InputsT, OutputT, MetadataT]) -> EvaluatorOutput:
    """Run the evaluator asynchronously, handling both sync and async implementations.

    This method ensures asynchronous execution by properly awaiting any async evaluate
    implementation. For synchronous implementations, it returns the result directly.

    Args:
        ctx: The context containing the inputs, outputs, and metadata for evaluation.

    Returns:
        The evaluation result, which can be a scalar value, an EvaluationReason, or a mapping
        of evaluation names to either of those.
    """
    # Note: If self.evaluate is synchronous, but you need to prevent this from blocking, override this method with:
    # return await anyio.to_thread.run_sync(self.evaluate, ctx)
    output = self.evaluate(ctx)
    if inspect.iscoroutine(output):
        return await output
    else:
        return cast(EvaluatorOutput, output)
```

### EvaluatorFailure

Represents a failure raised during the execution of an evaluator.

Source code in `pydantic_evals/pydantic_evals/evaluators/evaluator.py`

```python
@dataclass
class EvaluatorFailure:
    """Represents a failure raised during the execution of an evaluator."""

    name: str
    error_message: str
    error_stacktrace: str
    source: EvaluatorSpec
```

### EvaluatorOutput

```python
EvaluatorOutput = (
    EvaluationScalar
    | EvaluationReason
    | Mapping[str, EvaluationScalar | EvaluationReason]
)
```

Type for the output of an evaluator, which can be a scalar, an EvaluationReason, or a mapping of names to either.

### EvaluatorSpec

```python
EvaluatorSpec = NamedSpec
```

The specification of an evaluator to be run.

This class is used to represent evaluators in a serializable format, supporting various short forms for convenience when defining evaluators in YAML or JSON dataset files.

In particular, each of the following forms is supported for specifying an evaluator with name `MyEvaluator`: * `'MyEvaluator'` - Just the (string) name of the Evaluator subclass is used if its `__init__` takes no arguments * `{'MyEvaluator': first_arg}` - A single argument is passed as the first positional argument to `MyEvaluator.__init__` * `{'MyEvaluator': {k1: v1, k2: v2}}` - Multiple kwargs are passed to `MyEvaluator.__init__`

### ConfusionMatrixEvaluator

Bases: `ReportEvaluator`

Computes a confusion matrix from case data.

Source code in `pydantic_evals/pydantic_evals/evaluators/report_common.py`

```python
@dataclass(repr=False)
class ConfusionMatrixEvaluator(ReportEvaluator):
    """Computes a confusion matrix from case data."""

    predicted_from: Literal['expected_output', 'output', 'metadata', 'labels'] = 'output'
    predicted_key: str | None = None

    expected_from: Literal['expected_output', 'output', 'metadata', 'labels'] = 'expected_output'
    expected_key: str | None = None

    title: str = 'Confusion Matrix'

    def evaluate(self, ctx: ReportEvaluatorContext[Any, Any, Any]) -> ConfusionMatrix:
        predicted: list[str] = []
        expected: list[str] = []

        for case in ctx.report.cases:
            pred = self._extract(case, self.predicted_from, self.predicted_key)
            exp = self._extract(case, self.expected_from, self.expected_key)
            if pred is None or exp is None:
                continue
            predicted.append(pred)
            expected.append(exp)

        all_labels = sorted(set(predicted) | set(expected))
        label_to_idx = {label: i for i, label in enumerate(all_labels)}
        matrix = [[0] * len(all_labels) for _ in all_labels]

        for e, p in zip(expected, predicted):
            matrix[label_to_idx[e]][label_to_idx[p]] += 1

        return ConfusionMatrix(
            title=self.title,
            class_labels=all_labels,
            matrix=matrix,
        )

    @staticmethod
    def _extract(
        case: ReportCase[Any, Any, Any],
        from_: Literal['expected_output', 'output', 'metadata', 'labels'],
        key: str | None,
    ) -> str | None:
        if from_ == 'expected_output':
            return str(case.expected_output) if case.expected_output is not None else None
        elif from_ == 'output':
            return str(case.output) if case.output is not None else None
        elif from_ == 'metadata':
            if key is not None:
                if isinstance(case.metadata, dict):
                    metadata_dict = cast(dict[str, Any], case.metadata)  # pyright: ignore[reportUnknownMemberType]
                    val = metadata_dict.get(key)
                    return str(val) if val is not None else None
                return None  # key requested but metadata isn't a dict — skip this case
            return str(case.metadata) if case.metadata is not None else None
        elif from_ == 'labels':
            if key is None:
                raise ValueError("'key' is required when from_='labels'")
            label_result = case.labels.get(key)
            return label_result.value if label_result else None
        assert_never(from_)
```

### KolmogorovSmirnovEvaluator

Bases: `ReportEvaluator`

Computes a Kolmogorov-Smirnov plot and statistic from case data.

Plots the empirical CDFs of the score distribution for positive and negative cases, and computes the KS statistic (maximum vertical distance between the two CDFs).

Returns a `LinePlot` with the two CDF curves and a `ScalarResult` with the KS statistic.

Source code in `pydantic_evals/pydantic_evals/evaluators/report_common.py`

```python
@dataclass(repr=False)
class KolmogorovSmirnovEvaluator(ReportEvaluator):
    """Computes a Kolmogorov-Smirnov plot and statistic from case data.

    Plots the empirical CDFs of the score distribution for positive and negative cases,
    and computes the KS statistic (maximum vertical distance between the two CDFs).

    Returns a `LinePlot` with the two CDF curves and a `ScalarResult` with the KS statistic.
    """

    score_key: str
    positive_from: Literal['expected_output', 'assertions', 'labels']
    positive_key: str | None = None

    score_from: Literal['scores', 'metrics'] = 'scores'

    title: str = 'KS Plot'
    n_thresholds: int = 100

    def evaluate(self, ctx: ReportEvaluatorContext[Any, Any, Any]) -> list[ReportAnalysis]:
        scored_cases = _extract_scored_cases(
            ctx.report.cases, self.score_key, self.score_from, self.positive_from, self.positive_key
        )

        empty_result: list[ReportAnalysis] = [
            LinePlot(
                title=self.title,
                x_label='Score',
                y_label='Cumulative Probability',
                y_range=(0, 1),
                curves=[],
            ),
            ScalarResult(title='KS Statistic', value=float('nan')),
        ]
        if not scored_cases:
            return empty_result

        pos_scores = sorted(s for s, p in scored_cases if p)
        neg_scores = sorted(s for s, p in scored_cases if not p)

        if not pos_scores or not neg_scores:
            return empty_result

        # Compute CDFs at all unique scores using binary search
        all_scores = sorted({s for s, _ in scored_cases})
        # Start both CDFs at y=0 at the minimum score
        pos_cdf: list[tuple[float, float]] = [(all_scores[0], 0.0)]
        neg_cdf: list[tuple[float, float]] = [(all_scores[0], 0.0)]
        ks_stat = 0.0

        for score in all_scores:
            pos_val = bisect_right(pos_scores, score) / len(pos_scores)
            neg_val = bisect_right(neg_scores, score) / len(neg_scores)
            pos_cdf.append((score, pos_val))
            neg_cdf.append((score, neg_val))
            ks_stat = max(ks_stat, abs(pos_val - neg_val))

        # Downsample for display
        display_pos = _downsample(pos_cdf, self.n_thresholds)
        display_neg = _downsample(neg_cdf, self.n_thresholds)

        pos_curve = LinePlotCurve(
            name='Positive',
            points=[LinePlotPoint(x=s, y=v) for s, v in display_pos],
            step='end',
        )
        neg_curve = LinePlotCurve(
            name='Negative',
            points=[LinePlotPoint(x=s, y=v) for s, v in display_neg],
            step='end',
        )

        return [
            LinePlot(
                title=self.title,
                x_label='Score',
                y_label='Cumulative Probability',
                y_range=(0, 1),
                curves=[pos_curve, neg_curve],
            ),
            ScalarResult(title='KS Statistic', value=ks_stat),
        ]
```

### PrecisionRecallEvaluator

Bases: `ReportEvaluator`

Computes a precision-recall curve from case data.

Returns both a `PrecisionRecall` chart and a `ScalarResult` with the AUC value. The AUC is computed at full resolution (every unique score threshold) for accuracy, while the chart points are downsampled to `n_thresholds` for display.

Source code in `pydantic_evals/pydantic_evals/evaluators/report_common.py`

```python
@dataclass(repr=False)
class PrecisionRecallEvaluator(ReportEvaluator):
    """Computes a precision-recall curve from case data.

    Returns both a `PrecisionRecall` chart and a `ScalarResult` with the AUC value.
    The AUC is computed at full resolution (every unique score threshold) for accuracy,
    while the chart points are downsampled to `n_thresholds` for display.
    """

    score_key: str
    positive_from: Literal['expected_output', 'assertions', 'labels']
    positive_key: str | None = None

    score_from: Literal['scores', 'metrics'] = 'scores'

    title: str = 'Precision-Recall Curve'
    n_thresholds: int = 100

    def evaluate(self, ctx: ReportEvaluatorContext[Any, Any, Any]) -> list[ReportAnalysis]:
        scored_cases = _extract_scored_cases(
            ctx.report.cases, self.score_key, self.score_from, self.positive_from, self.positive_key
        )

        if not scored_cases:
            return [
                PrecisionRecall(title=self.title, curves=[]),
                ScalarResult(title=f'{self.title} AUC', value=float('nan')),
            ]

        total_positives = sum(1 for _, p in scored_cases if p)

        # Compute precision/recall at every unique score for exact AUC
        unique_thresholds = sorted({s for s, _ in scored_cases}, reverse=True)
        # Start with anchor at (recall=0, precision=1) — the "no predictions" point
        max_score = unique_thresholds[0]
        all_points: list[PrecisionRecallPoint] = [PrecisionRecallPoint(threshold=max_score, precision=1.0, recall=0.0)]
        for threshold in unique_thresholds:
            tp = sum(1 for s, p in scored_cases if s >= threshold and p)
            fp = sum(1 for s, p in scored_cases if s >= threshold and not p)
            fn = total_positives - tp
            precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
            recall = tp / (fn + tp) if (fn + tp) > 0 else 0.0
            all_points.append(PrecisionRecallPoint(threshold=threshold, precision=precision, recall=recall))

        # Exact AUC from the full-resolution points (anchor included)
        auc_points = [(p.recall, p.precision) for p in all_points]
        auc = _trapezoidal_auc(auc_points)

        # Downsample for display
        if len(all_points) <= self.n_thresholds or self.n_thresholds <= 1:
            display_points = all_points
        else:
            indices = sorted(
                {int(i * (len(all_points) - 1) / (self.n_thresholds - 1)) for i in range(self.n_thresholds)}
            )
            display_points = [all_points[i] for i in indices]

        curve = PrecisionRecallCurve(name=ctx.name, points=display_points, auc=auc)
        return [
            PrecisionRecall(title=self.title, curves=[curve]),
            ScalarResult(title=f'{self.title} AUC', value=auc),
        ]
```

### ROCAUCEvaluator

Bases: `ReportEvaluator`

Computes an ROC curve and AUC from case data.

Returns a `LinePlot` with the ROC curve (plus a dashed random-baseline diagonal) and a `ScalarResult` with the AUC value.

Source code in `pydantic_evals/pydantic_evals/evaluators/report_common.py`

```python
@dataclass(repr=False)
class ROCAUCEvaluator(ReportEvaluator):
    """Computes an ROC curve and AUC from case data.

    Returns a `LinePlot` with the ROC curve (plus a dashed random-baseline diagonal)
    and a `ScalarResult` with the AUC value.
    """

    score_key: str
    positive_from: Literal['expected_output', 'assertions', 'labels']
    positive_key: str | None = None

    score_from: Literal['scores', 'metrics'] = 'scores'

    title: str = 'ROC Curve'
    n_thresholds: int = 100

    def evaluate(self, ctx: ReportEvaluatorContext[Any, Any, Any]) -> list[ReportAnalysis]:
        scored_cases = _extract_scored_cases(
            ctx.report.cases, self.score_key, self.score_from, self.positive_from, self.positive_key
        )

        empty_result: list[ReportAnalysis] = [
            LinePlot(
                title=self.title,
                x_label='False Positive Rate',
                y_label='True Positive Rate',
                x_range=(0, 1),
                y_range=(0, 1),
                curves=[],
            ),
            ScalarResult(title=f'{self.title} AUC', value=float('nan')),
        ]
        if not scored_cases:
            return empty_result

        total_positives = sum(1 for _, p in scored_cases if p)
        total_negatives = len(scored_cases) - total_positives

        if total_positives == 0 or total_negatives == 0:
            return empty_result

        # Compute TPR/FPR at every unique score for exact AUC
        unique_thresholds = sorted({s for s, _ in scored_cases}, reverse=True)
        all_fpr_tpr: list[tuple[float, float]] = [(0.0, 0.0)]
        for threshold in unique_thresholds:
            tp = sum(1 for s, p in scored_cases if s >= threshold and p)
            fp = sum(1 for s, p in scored_cases if s >= threshold and not p)
            tpr = tp / total_positives
            fpr = fp / total_negatives
            all_fpr_tpr.append((fpr, tpr))
        all_fpr_tpr.sort()

        # Exact AUC
        auc = _trapezoidal_auc(all_fpr_tpr)

        # Downsample for display
        downsampled = _downsample(all_fpr_tpr, self.n_thresholds)

        roc_curve = LinePlotCurve(
            name=f'{ctx.name} (AUC: {auc:.3f})',
            points=[LinePlotPoint(x=fpr, y=tpr) for fpr, tpr in downsampled],
        )
        baseline = LinePlotCurve(
            name='Random',
            points=[LinePlotPoint(x=0, y=0), LinePlotPoint(x=1, y=1)],
            style='dashed',
        )

        return [
            LinePlot(
                title=self.title,
                x_label='False Positive Rate',
                y_label='True Positive Rate',
                x_range=(0, 1),
                y_range=(0, 1),
                curves=[roc_curve, baseline],
            ),
            ScalarResult(title=f'{self.title} AUC', value=auc),
        ]
```

### ReportEvaluator

Bases: `BaseEvaluator`, `Generic[InputsT, OutputT, MetadataT]`

Base class for experiment-wide evaluators that analyze full reports.

Unlike case-level Evaluators which assess individual task outputs, ReportEvaluators see all case results together and produce experiment-wide analyses like confusion matrices, precision-recall curves, or scalar statistics.

Source code in `pydantic_evals/pydantic_evals/evaluators/report_evaluator.py`

```python
@dataclass(repr=False)
class ReportEvaluator(BaseEvaluator, Generic[InputsT, OutputT, MetadataT]):
    """Base class for experiment-wide evaluators that analyze full reports.

    Unlike case-level Evaluators which assess individual task outputs,
    ReportEvaluators see all case results together and produce
    experiment-wide analyses like confusion matrices, precision-recall curves,
    or scalar statistics.
    """

    @abstractmethod
    def evaluate(
        self, ctx: ReportEvaluatorContext[InputsT, OutputT, MetadataT]
    ) -> ReportAnalysis | list[ReportAnalysis] | Awaitable[ReportAnalysis | list[ReportAnalysis]]:
        """Evaluate the full report and return experiment-wide analysis/analyses."""
        ...

    async def evaluate_async(
        self, ctx: ReportEvaluatorContext[InputsT, OutputT, MetadataT]
    ) -> ReportAnalysis | list[ReportAnalysis]:
        """Evaluate, handling both sync and async implementations."""
        output = self.evaluate(ctx)
        if inspect.iscoroutine(output):
            return await output
        return cast('ReportAnalysis | list[ReportAnalysis]', output)
```

#### evaluate

```python
evaluate(
    ctx: ReportEvaluatorContext[
        InputsT, OutputT, MetadataT
    ],
) -> (
    ReportAnalysis
    | list[ReportAnalysis]
    | Awaitable[ReportAnalysis | list[ReportAnalysis]]
)
```

Evaluate the full report and return experiment-wide analysis/analyses.

Source code in `pydantic_evals/pydantic_evals/evaluators/report_evaluator.py`

```python
@abstractmethod
def evaluate(
    self, ctx: ReportEvaluatorContext[InputsT, OutputT, MetadataT]
) -> ReportAnalysis | list[ReportAnalysis] | Awaitable[ReportAnalysis | list[ReportAnalysis]]:
    """Evaluate the full report and return experiment-wide analysis/analyses."""
    ...
```

#### evaluate_async

```python
evaluate_async(
    ctx: ReportEvaluatorContext[
        InputsT, OutputT, MetadataT
    ],
) -> ReportAnalysis | list[ReportAnalysis]
```

Evaluate, handling both sync and async implementations.

Source code in `pydantic_evals/pydantic_evals/evaluators/report_evaluator.py`

```python
async def evaluate_async(
    self, ctx: ReportEvaluatorContext[InputsT, OutputT, MetadataT]
) -> ReportAnalysis | list[ReportAnalysis]:
    """Evaluate, handling both sync and async implementations."""
    output = self.evaluate(ctx)
    if inspect.iscoroutine(output):
        return await output
    return cast('ReportAnalysis | list[ReportAnalysis]', output)
```

### ReportEvaluatorContext

Bases: `Generic[InputsT, OutputT, MetadataT]`

Context for report-level evaluation, containing the full experiment results.

Source code in `pydantic_evals/pydantic_evals/evaluators/report_evaluator.py`

```python
@dataclass(kw_only=True)
class ReportEvaluatorContext(Generic[InputsT, OutputT, MetadataT]):
    """Context for report-level evaluation, containing the full experiment results."""

    name: str
    """The experiment name."""
    report: EvaluationReport[InputsT, OutputT, MetadataT]
    """The full evaluation report."""
    experiment_metadata: dict[str, Any] | None
    """Experiment-level metadata."""
```

#### name

```python
name: str
```

The experiment name.

#### report

```python
report: EvaluationReport[InputsT, OutputT, MetadataT]
```

The full evaluation report.

#### experiment_metadata

```python
experiment_metadata: dict[str, Any] | None
```

Experiment-level metadata.

### GradingOutput

Bases: `BaseModel`

The output of a grading operation.

Source code in `pydantic_evals/pydantic_evals/evaluators/llm_as_a_judge.py`

```python
class GradingOutput(BaseModel, populate_by_name=True):
    """The output of a grading operation."""

    reason: str
    pass_: bool = Field(validation_alias='pass', serialization_alias='pass')
    score: float
```

### judge_output

```python
judge_output(
    output: Any,
    rubric: str,
    model: Model | KnownModelName | str | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput
```

Judge the output of a model based on a rubric.

If the model is not specified, a default model is used. The default model starts as 'openai:gpt-5.2', but this can be changed using the `set_default_judge_model` function.

Source code in `pydantic_evals/pydantic_evals/evaluators/llm_as_a_judge.py`

```python
async def judge_output(
    output: Any,
    rubric: str,
    model: models.Model | models.KnownModelName | str | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput:
    """Judge the output of a model based on a rubric.

    If the model is not specified, a default model is used. The default model starts as 'openai:gpt-5.2',
    but this can be changed using the `set_default_judge_model` function.
    """
    user_prompt = _build_prompt(output=output, rubric=rubric)
    return (
        await _judge_output_agent.run(user_prompt, model=model or _default_model, model_settings=model_settings)
    ).output
```

### judge_input_output

```python
judge_input_output(
    inputs: Any,
    output: Any,
    rubric: str,
    model: Model | KnownModelName | str | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput
```

Judge the output of a model based on the inputs and a rubric.

If the model is not specified, a default model is used. The default model starts as 'openai:gpt-5.2', but this can be changed using the `set_default_judge_model` function.

Source code in `pydantic_evals/pydantic_evals/evaluators/llm_as_a_judge.py`

```python
async def judge_input_output(
    inputs: Any,
    output: Any,
    rubric: str,
    model: models.Model | models.KnownModelName | str | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput:
    """Judge the output of a model based on the inputs and a rubric.

    If the model is not specified, a default model is used. The default model starts as 'openai:gpt-5.2',
    but this can be changed using the `set_default_judge_model` function.
    """
    user_prompt = _build_prompt(inputs=inputs, output=output, rubric=rubric)

    return (
        await _judge_input_output_agent.run(user_prompt, model=model or _default_model, model_settings=model_settings)
    ).output
```

### judge_input_output_expected

```python
judge_input_output_expected(
    inputs: Any,
    output: Any,
    expected_output: Any,
    rubric: str,
    model: Model | KnownModelName | str | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput
```

Judge the output of a model based on the inputs and a rubric.

If the model is not specified, a default model is used. The default model starts as 'openai:gpt-5.2', but this can be changed using the `set_default_judge_model` function.

Source code in `pydantic_evals/pydantic_evals/evaluators/llm_as_a_judge.py`

```python
async def judge_input_output_expected(
    inputs: Any,
    output: Any,
    expected_output: Any,
    rubric: str,
    model: models.Model | models.KnownModelName | str | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput:
    """Judge the output of a model based on the inputs and a rubric.

    If the model is not specified, a default model is used. The default model starts as 'openai:gpt-5.2',
    but this can be changed using the `set_default_judge_model` function.
    """
    user_prompt = _build_prompt(inputs=inputs, output=output, rubric=rubric, expected_output=expected_output)

    return (
        await _judge_input_output_expected_agent.run(
            user_prompt, model=model or _default_model, model_settings=model_settings
        )
    ).output
```

### judge_output_expected

```python
judge_output_expected(
    output: Any,
    expected_output: Any,
    rubric: str,
    model: Model | KnownModelName | str | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput
```

Judge the output of a model based on the expected output, output, and a rubric.

If the model is not specified, a default model is used. The default model starts as 'openai:gpt-5.2', but this can be changed using the `set_default_judge_model` function.

Source code in `pydantic_evals/pydantic_evals/evaluators/llm_as_a_judge.py`

```python
async def judge_output_expected(
    output: Any,
    expected_output: Any,
    rubric: str,
    model: models.Model | models.KnownModelName | str | None = None,
    model_settings: ModelSettings | None = None,
) -> GradingOutput:
    """Judge the output of a model based on the expected output, output, and a rubric.

    If the model is not specified, a default model is used. The default model starts as 'openai:gpt-5.2',
    but this can be changed using the `set_default_judge_model` function.
    """
    user_prompt = _build_prompt(output=output, rubric=rubric, expected_output=expected_output)
    return (
        await _judge_output_expected_agent.run(
            user_prompt, model=model or _default_model, model_settings=model_settings
        )
    ).output
```

### set_default_judge_model

```python
set_default_judge_model(
    model: Model | KnownModelName,
) -> None
```

Set the default model used for judging.

This model is used if `None` is passed to the `model` argument of `judge_output` and `judge_input_output`.

Source code in `pydantic_evals/pydantic_evals/evaluators/llm_as_a_judge.py`

```python
def set_default_judge_model(model: models.Model | models.KnownModelName) -> None:
    """Set the default model used for judging.

    This model is used if `None` is passed to the `model` argument of `judge_output` and `judge_input_output`.
    """
    global _default_model
    _default_model = model
```
