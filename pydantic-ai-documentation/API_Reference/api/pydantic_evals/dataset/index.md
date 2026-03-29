# `pydantic_evals.dataset`

Dataset management for pydantic evals.

This module provides functionality for creating, loading, saving, and evaluating datasets of test cases. Each case must have inputs, and can optionally have a name, expected output, metadata, and case-specific evaluators.

Datasets can be loaded from and saved to YAML or JSON files, and can be evaluated against a task function to produce an evaluation report.

### InputsT

```python
InputsT = TypeVar('InputsT', default=Any)
```

Generic type for the inputs to the task being evaluated.

### OutputT

```python
OutputT = TypeVar('OutputT', default=Any)
```

Generic type for the expected output of the task being evaluated.

### MetadataT

```python
MetadataT = TypeVar('MetadataT', default=Any)
```

Generic type for the metadata associated with the task being evaluated.

### DEFAULT_DATASET_PATH

```python
DEFAULT_DATASET_PATH = './test_cases.yaml'
```

Default path for saving/loading datasets.

### DEFAULT_SCHEMA_PATH_TEMPLATE

```python
DEFAULT_SCHEMA_PATH_TEMPLATE = './{stem}_schema.json'
```

Default template for schema file paths, where {stem} is replaced with the dataset filename stem.

### Case

Bases: `Generic[InputsT, OutputT, MetadataT]`

A single row of a Dataset.

Each case represents a single test scenario with inputs to test. A case may optionally specify a name, expected outputs to compare against, and arbitrary metadata.

Cases can also have their own specific evaluators which are run in addition to dataset-level evaluators.

Example:

```python
from pydantic_evals import Case

case = Case(
    name='Simple addition',
    inputs={'a': 1, 'b': 2},
    expected_output=3,
    metadata={'description': 'Tests basic addition'},
)
```

Source code in `pydantic_evals/pydantic_evals/dataset.py`

````python
@dataclass(init=False)
class Case(Generic[InputsT, OutputT, MetadataT]):
    """A single row of a [`Dataset`][pydantic_evals.Dataset].

    Each case represents a single test scenario with inputs to test. A case may optionally specify a name, expected
    outputs to compare against, and arbitrary metadata.

    Cases can also have their own specific evaluators which are run in addition to dataset-level evaluators.

    Example:
    ```python
    from pydantic_evals import Case

    case = Case(
        name='Simple addition',
        inputs={'a': 1, 'b': 2},
        expected_output=3,
        metadata={'description': 'Tests basic addition'},
    )
    ```
    """

    name: str | None
    """Name of the case. This is used to identify the case in the report and can be used to filter cases."""
    inputs: InputsT
    """Inputs to the task. This is the input to the task that will be evaluated."""
    metadata: MetadataT | None = None
    """Metadata to be used in the evaluation.

    This can be used to provide additional information about the case to the evaluators.
    """
    expected_output: OutputT | None = None
    """Expected output of the task. This is the expected output of the task that will be evaluated."""
    evaluators: list[Evaluator[InputsT, OutputT, MetadataT]] = field(
        default_factory=list[Evaluator[InputsT, OutputT, MetadataT]]
    )
    """Evaluators to be used just on this case."""

    def __init__(
        self,
        *,
        name: str | None = None,
        inputs: InputsT,
        metadata: MetadataT | None = None,
        expected_output: OutputT | None = None,
        evaluators: tuple[Evaluator[InputsT, OutputT, MetadataT], ...] = (),
    ):
        """Initialize a new test case.

        Args:
            name: Optional name for the case. If not provided, a generic name will be assigned when added to a dataset.
            inputs: The inputs to the task being evaluated.
            metadata: Optional metadata for the case, which can be used by evaluators.
            expected_output: Optional expected output of the task, used for comparison in evaluators.
            evaluators: Tuple of evaluators specific to this case. These are in addition to any
                dataset-level evaluators.

        """
        # Note: `evaluators` must be a tuple instead of Sequence due to misbehavior with pyright's generic parameter
        # inference if it has type `Sequence`
        self.name = name
        self.inputs = inputs
        self.metadata = metadata
        self.expected_output = expected_output
        self.evaluators = list(evaluators)
````

#### __init__

```python
__init__(
    *,
    name: str | None = None,
    inputs: InputsT,
    metadata: MetadataT | None = None,
    expected_output: OutputT | None = None,
    evaluators: tuple[
        Evaluator[InputsT, OutputT, MetadataT], ...
    ] = ()
)
```

Initialize a new test case.

Parameters:

| Name              | Type                                                 | Description                                                                                       | Default                                                                                               |
| ----------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `name`            | \`str                                                | None\`                                                                                            | Optional name for the case. If not provided, a generic name will be assigned when added to a dataset. |
| `inputs`          | `InputsT`                                            | The inputs to the task being evaluated.                                                           | *required*                                                                                            |
| `metadata`        | \`MetadataT                                          | None\`                                                                                            | Optional metadata for the case, which can be used by evaluators.                                      |
| `expected_output` | \`OutputT                                            | None\`                                                                                            | Optional expected output of the task, used for comparison in evaluators.                              |
| `evaluators`      | `tuple[Evaluator[InputsT, OutputT, MetadataT], ...]` | Tuple of evaluators specific to this case. These are in addition to any dataset-level evaluators. | `()`                                                                                                  |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def __init__(
    self,
    *,
    name: str | None = None,
    inputs: InputsT,
    metadata: MetadataT | None = None,
    expected_output: OutputT | None = None,
    evaluators: tuple[Evaluator[InputsT, OutputT, MetadataT], ...] = (),
):
    """Initialize a new test case.

    Args:
        name: Optional name for the case. If not provided, a generic name will be assigned when added to a dataset.
        inputs: The inputs to the task being evaluated.
        metadata: Optional metadata for the case, which can be used by evaluators.
        expected_output: Optional expected output of the task, used for comparison in evaluators.
        evaluators: Tuple of evaluators specific to this case. These are in addition to any
            dataset-level evaluators.

    """
    # Note: `evaluators` must be a tuple instead of Sequence due to misbehavior with pyright's generic parameter
    # inference if it has type `Sequence`
    self.name = name
    self.inputs = inputs
    self.metadata = metadata
    self.expected_output = expected_output
    self.evaluators = list(evaluators)
```

#### name

```python
name: str | None = name
```

Name of the case. This is used to identify the case in the report and can be used to filter cases.

#### inputs

```python
inputs: InputsT = inputs
```

Inputs to the task. This is the input to the task that will be evaluated.

#### metadata

```python
metadata: MetadataT | None = metadata
```

Metadata to be used in the evaluation.

This can be used to provide additional information about the case to the evaluators.

#### expected_output

```python
expected_output: OutputT | None = expected_output
```

Expected output of the task. This is the expected output of the task that will be evaluated.

#### evaluators

```python
evaluators: list[Evaluator[InputsT, OutputT, MetadataT]] = (
    list(evaluators)
)
```

Evaluators to be used just on this case.

### Dataset

Bases: `BaseModel`, `Generic[InputsT, OutputT, MetadataT]`

A dataset of test cases.

Datasets allow you to organize a collection of test cases and evaluate them against a task function. They can be loaded from and saved to YAML or JSON files, and can have dataset-level evaluators that apply to all cases.

Example:

```python
# Create a dataset with two test cases
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ExactMatch(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output == ctx.expected_output

dataset = Dataset(
    cases=[
        Case(name='test1', inputs={'text': 'Hello'}, expected_output='HELLO'),
        Case(name='test2', inputs={'text': 'World'}, expected_output='WORLD'),
    ],
    evaluators=[ExactMatch()],
)

# Evaluate the dataset against a task function
async def uppercase(inputs: dict) -> str:
    return inputs['text'].upper()

async def main():
    report = await dataset.evaluate(uppercase)
    report.print()
'''
   Evaluation Summary: uppercase
┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID  ┃ Assertions ┃ Duration ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ test1    │ ✔          │     10ms │
├──────────┼────────────┼──────────┤
│ test2    │ ✔          │     10ms │
├──────────┼────────────┼──────────┤
│ Averages │ 100.0% ✔   │     10ms │
└──────────┴────────────┴──────────┘
'''
```

Source code in `pydantic_evals/pydantic_evals/dataset.py`

````python
class Dataset(BaseModel, Generic[InputsT, OutputT, MetadataT], extra='forbid', arbitrary_types_allowed=True):
    """A dataset of test [cases][pydantic_evals.Case].

    Datasets allow you to organize a collection of test cases and evaluate them against a task function.
    They can be loaded from and saved to YAML or JSON files, and can have dataset-level evaluators that
    apply to all cases.

    Example:
    ```python
    # Create a dataset with two test cases
    from dataclasses import dataclass

    from pydantic_evals import Case, Dataset
    from pydantic_evals.evaluators import Evaluator, EvaluatorContext


    @dataclass
    class ExactMatch(Evaluator):
        def evaluate(self, ctx: EvaluatorContext) -> bool:
            return ctx.output == ctx.expected_output

    dataset = Dataset(
        cases=[
            Case(name='test1', inputs={'text': 'Hello'}, expected_output='HELLO'),
            Case(name='test2', inputs={'text': 'World'}, expected_output='WORLD'),
        ],
        evaluators=[ExactMatch()],
    )

    # Evaluate the dataset against a task function
    async def uppercase(inputs: dict) -> str:
        return inputs['text'].upper()

    async def main():
        report = await dataset.evaluate(uppercase)
        report.print()
    '''
       Evaluation Summary: uppercase
    ┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
    ┃ Case ID  ┃ Assertions ┃ Duration ┃
    ┡━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
    │ test1    │ ✔          │     10ms │
    ├──────────┼────────────┼──────────┤
    │ test2    │ ✔          │     10ms │
    ├──────────┼────────────┼──────────┤
    │ Averages │ 100.0% ✔   │     10ms │
    └──────────┴────────────┴──────────┘
    '''
    ```
    """

    name: str | None = None
    """Optional name of the dataset."""
    cases: list[Case[InputsT, OutputT, MetadataT]]
    """List of test cases in the dataset."""
    evaluators: list[Evaluator[InputsT, OutputT, MetadataT]] = []
    """List of evaluators to be used on all cases in the dataset."""
    report_evaluators: list[ReportEvaluator[InputsT, OutputT, MetadataT]] = []
    """Evaluators that operate on the full report to produce experiment-wide analyses."""

    def __init__(
        self,
        *,
        name: str | None = None,
        cases: Sequence[Case[InputsT, OutputT, MetadataT]],
        evaluators: Sequence[Evaluator[InputsT, OutputT, MetadataT]] = (),
        report_evaluators: Sequence[ReportEvaluator[InputsT, OutputT, MetadataT]] = (),
    ):
        """Initialize a new dataset with test cases and optional evaluators.

        Args:
            name: Optional name for the dataset.
            cases: Sequence of test cases to include in the dataset.
            evaluators: Optional sequence of evaluators to apply to all cases in the dataset.
            report_evaluators: Optional sequence of report evaluators that run on the full evaluation report.
        """
        case_names = set[str]()
        for case in cases:
            if case.name is None:
                continue
            if case.name in case_names:
                raise ValueError(f'Duplicate case name: {case.name!r}')
            case_names.add(case.name)

        super().__init__(
            name=name,
            cases=cases,
            evaluators=list(evaluators),
            report_evaluators=list(report_evaluators),
        )

    def _build_tasks_to_run(self, repeat: int) -> list[tuple[Case[InputsT, OutputT, MetadataT], str, str | None]]:
        """Build the list of (case, report_case_name, source_case_name) tuples for evaluation."""
        if repeat > 1:
            return [
                (case, f'{case_name} [{run_idx}/{repeat}]', case_name)
                for i, case in enumerate(self.cases, 1)
                for run_idx in range(1, repeat + 1)
                if (case_name := case.name or f'Case {i}')
            ]
        else:
            return [(case, case.name or f'Case {i}', None) for i, case in enumerate(self.cases, 1)]

    # TODO in v2: Make everything not required keyword-only
    async def evaluate(
        self,
        task: Callable[[InputsT], Awaitable[OutputT]] | Callable[[InputsT], OutputT],
        name: str | None = None,
        max_concurrency: int | None = None,
        progress: bool = True,
        retry_task: RetryConfig | None = None,
        retry_evaluators: RetryConfig | None = None,
        *,
        task_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        repeat: int = 1,
        lifecycle: type[CaseLifecycle[InputsT, OutputT, MetadataT]] | None = None,
    ) -> EvaluationReport[InputsT, OutputT, MetadataT]:
        """Evaluates the test cases in the dataset using the given task.

        This method runs the task on each case in the dataset, applies evaluators,
        and collects results into a report. Cases are run concurrently, limited by `max_concurrency` if specified.

        Args:
            task: The task to evaluate. This should be a callable that takes the inputs of the case
                and returns the output.
            name: The name of the experiment being run, this is used to identify the experiment in the report.
                If omitted, the task_name will be used; if that is not specified, the name of the task function is used.
            max_concurrency: The maximum number of concurrent evaluations of the task to allow.
                If None, all cases will be evaluated concurrently.
            progress: Whether to show a progress bar for the evaluation. Defaults to `True`.
            retry_task: Optional retry configuration for the task execution.
            retry_evaluators: Optional retry configuration for evaluator execution.
            task_name: Optional override to the name of the task being executed, otherwise the name of the task
                function will be used.
            metadata: Optional dict of experiment metadata.
            repeat: Number of times to run each case. When > 1, each case is run multiple times and
                results are grouped by the original case name for aggregation. Defaults to 1.
            lifecycle: Optional lifecycle class for per-case setup, context preparation, and teardown hooks.
                A new instance is created for each case. See [`CaseLifecycle`][pydantic_evals.lifecycle.CaseLifecycle].

        Returns:
            A report containing the results of the evaluation.
        """
        if repeat < 1:
            raise ValueError(f'repeat must be >= 1, got {repeat}')

        task_name = task_name or get_unwrapped_function_name(task)
        name = name or task_name

        tasks_to_run = self._build_tasks_to_run(repeat)
        total_tasks = len(tasks_to_run)
        progress_bar = Progress() if progress else None

        limiter = anyio.Semaphore(max_concurrency) if max_concurrency is not None else AsyncExitStack()

        extra_attributes: dict[str, Any] = {'gen_ai.operation.name': 'experiment'}
        if metadata is not None:
            extra_attributes['metadata'] = metadata
        if repeat > 1:
            extra_attributes['logfire.experiment.repeat'] = repeat
        with (
            logfire_span(
                'evaluate {name}',
                name=name,
                task_name=task_name,
                dataset_name=self.name,
                n_cases=len(self.cases),
                **extra_attributes,
            ) as eval_span,
            progress_bar or nullcontext(),
        ):
            task_id = progress_bar.add_task(f'Evaluating {task_name}', total=total_tasks) if progress_bar else None

            async def _handle_case(
                case: Case[InputsT, OutputT, MetadataT],
                report_case_name: str,
                source_case_name: str | None,
            ):
                async with limiter:
                    result = await _run_task_and_evaluators(
                        task,
                        case,
                        report_case_name,
                        self.evaluators,
                        retry_task,
                        retry_evaluators,
                        source_case_name=source_case_name,
                        lifecycle=lifecycle,
                    )
                    if progress_bar and task_id is not None:  # pragma: no branch
                        progress_bar.update(task_id, advance=1)
                    return result

            if (context := eval_span.context) is None:  # pragma: no cover
                trace_id = None
                span_id = None
            else:
                trace_id = f'{context.trace_id:032x}'
                span_id = f'{context.span_id:016x}'
            cases_and_failures = await task_group_gather(
                [
                    lambda case=case, rn=report_name, scn=source_name: _handle_case(case, rn, scn)
                    for case, report_name, source_name in tasks_to_run
                ]
            )
            cases: list[ReportCase] = []
            failures: list[ReportCaseFailure] = []
            for item in cases_and_failures:
                if isinstance(item, ReportCase):
                    cases.append(item)
                else:
                    failures.append(item)
            report = EvaluationReport(
                name=name,
                cases=cases,
                failures=failures,
                experiment_metadata=metadata,
                span_id=span_id,
                trace_id=trace_id,
            )

            # Run report evaluators
            if self.report_evaluators:
                report_ctx = ReportEvaluatorContext(
                    name=name,
                    report=report,
                    experiment_metadata=metadata,
                )
                await _run_report_evaluators(self.report_evaluators, report_ctx)

            _set_experiment_span_attributes(eval_span, report, metadata, len(self.cases), repeat)
        return report

    def evaluate_sync(
        self,
        task: Callable[[InputsT], Awaitable[OutputT]] | Callable[[InputsT], OutputT],
        name: str | None = None,
        max_concurrency: int | None = None,
        progress: bool = True,
        retry_task: RetryConfig | None = None,
        retry_evaluators: RetryConfig | None = None,
        *,
        task_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        repeat: int = 1,
        lifecycle: type[CaseLifecycle[InputsT, OutputT, MetadataT]] | None = None,
    ) -> EvaluationReport[InputsT, OutputT, MetadataT]:
        """Evaluates the test cases in the dataset using the given task.

        This is a synchronous wrapper around [`evaluate`][pydantic_evals.dataset.Dataset.evaluate] provided for convenience.

        Args:
            task: The task to evaluate. This should be a callable that takes the inputs of the case
                and returns the output.
            name: The name of the experiment being run, this is used to identify the experiment in the report.
                If omitted, the task_name will be used; if that is not specified, the name of the task function is used.
            max_concurrency: The maximum number of concurrent evaluations of the task to allow.
                If None, all cases will be evaluated concurrently.
            progress: Whether to show a progress bar for the evaluation. Defaults to `True`.
            retry_task: Optional retry configuration for the task execution.
            retry_evaluators: Optional retry configuration for evaluator execution.
            task_name: Optional override to the name of the task being executed, otherwise the name of the task
                function will be used.
            metadata: Optional dict of experiment metadata.
            repeat: Number of times to run each case. When > 1, each case is run multiple times and
                results are grouped by the original case name for aggregation. Defaults to 1.
            lifecycle: Optional lifecycle class for per-case setup, context preparation, and teardown hooks.
                A new instance is created for each case. See [`CaseLifecycle`][pydantic_evals.lifecycle.CaseLifecycle].

        Returns:
            A report containing the results of the evaluation.
        """
        return get_event_loop().run_until_complete(
            self.evaluate(
                task,
                name=name,
                max_concurrency=max_concurrency,
                progress=progress,
                retry_task=retry_task,
                retry_evaluators=retry_evaluators,
                task_name=task_name,
                metadata=metadata,
                repeat=repeat,
                lifecycle=lifecycle,
            )
        )

    def add_case(
        self,
        *,
        name: str | None = None,
        inputs: InputsT,
        metadata: MetadataT | None = None,
        expected_output: OutputT | None = None,
        evaluators: tuple[Evaluator[InputsT, OutputT, MetadataT], ...] = (),
    ) -> None:
        """Adds a case to the dataset.

        This is a convenience method for creating a [`Case`][pydantic_evals.Case] and adding it to the dataset.

        Args:
            name: Optional name for the case. If not provided, a generic name will be assigned.
            inputs: The inputs to the task being evaluated.
            metadata: Optional metadata for the case, which can be used by evaluators.
            expected_output: The expected output of the task, used for comparison in evaluators.
            evaluators: Tuple of evaluators specific to this case, in addition to dataset-level evaluators.
        """
        if name in {case.name for case in self.cases}:
            raise ValueError(f'Duplicate case name: {name!r}')

        case = Case[InputsT, OutputT, MetadataT](
            name=name,
            inputs=inputs,
            metadata=metadata,
            expected_output=expected_output,
            evaluators=evaluators,
        )
        self.cases.append(case)

    def add_evaluator(
        self,
        evaluator: Evaluator[InputsT, OutputT, MetadataT],
        specific_case: str | None = None,
    ) -> None:
        """Adds an evaluator to the dataset or a specific case.

        Args:
            evaluator: The evaluator to add.
            specific_case: If provided, the evaluator will only be added to the case with this name.
                If None, the evaluator will be added to all cases in the dataset.

        Raises:
            ValueError: If `specific_case` is provided but no case with that name exists in the dataset.
        """
        if specific_case is None:
            self.evaluators.append(evaluator)
        else:
            # If this is too slow, we could try to add a case lookup dict.
            # Note that if we do that, we'd need to make the cases list private to prevent modification.
            added = False
            for case in self.cases:
                if case.name == specific_case:
                    case.evaluators.append(evaluator)
                    added = True
            if not added:
                raise ValueError(f'Case {specific_case!r} not found in the dataset')

    @classmethod
    @functools.cache
    def _params(cls) -> tuple[type[InputsT], type[OutputT], type[MetadataT]]:
        """Get the type parameters for the Dataset class.

        Returns:
            A tuple of (InputsT, OutputT, MetadataT) types.
        """
        for c in cls.__mro__:
            metadata = getattr(c, '__pydantic_generic_metadata__', {})
            if len(args := (metadata.get('args', ()) or getattr(c, '__args__', ()))) == 3:  # pragma: no branch
                return args
        else:  # pragma: no cover
            warnings.warn(
                f'Could not determine the generic parameters for {cls}; using `Any` for each.'
                f' You should explicitly set the generic parameters via `Dataset[MyInputs, MyOutput, MyMetadata]`'
                f' when serializing or deserializing.',
                UserWarning,
            )
            return Any, Any, Any  # type: ignore

    @classmethod
    def from_file(
        cls,
        path: Path | str,
        fmt: Literal['yaml', 'json'] | None = None,
        custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
        custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
    ) -> Self:
        """Load a dataset from a file.

        Args:
            path: Path to the file to load.
            fmt: Format of the file. If None, the format will be inferred from the file extension.
                Must be either 'yaml' or 'json'.
            custom_evaluator_types: Custom evaluator classes to use when deserializing the dataset.
                These are additional evaluators beyond the default ones.
            custom_report_evaluator_types: Custom report evaluator classes to use when deserializing the dataset.
                These are additional report evaluators beyond the default ones.

        Returns:
            A new Dataset instance loaded from the file.

        Raises:
            ValidationError: If the file cannot be parsed as a valid dataset.
            ValueError: If the format cannot be inferred from the file extension.
        """
        path = Path(path)
        fmt = cls._infer_fmt(path, fmt)

        raw = Path(path).read_text(encoding='utf-8')
        try:
            return cls.from_text(
                raw,
                fmt=fmt,
                custom_evaluator_types=custom_evaluator_types,
                custom_report_evaluator_types=custom_report_evaluator_types,
                default_name=path.stem,
            )
        except ValidationError as e:  # pragma: no cover
            raise ValueError(f'{path} contains data that does not match the schema for {cls.__name__}:\n{e}.') from e

    @classmethod
    def from_text(
        cls,
        contents: str,
        fmt: Literal['yaml', 'json'] = 'yaml',
        custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
        custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
        *,
        default_name: str | None = None,
    ) -> Self:
        """Load a dataset from a string.

        Args:
            contents: The string content to parse.
            fmt: Format of the content. Must be either 'yaml' or 'json'.
            custom_evaluator_types: Custom evaluator classes to use when deserializing the dataset.
                These are additional evaluators beyond the default ones.
            custom_report_evaluator_types: Custom report evaluator classes to use when deserializing the dataset.
                These are additional report evaluators beyond the default ones.
            default_name: Default name of the dataset, to be used if not specified in the serialized contents.

        Returns:
            A new Dataset instance parsed from the string.

        Raises:
            ValidationError: If the content cannot be parsed as a valid dataset.
        """
        if fmt == 'yaml':
            loaded = yaml.safe_load(contents)
            return cls.from_dict(
                loaded, custom_evaluator_types, custom_report_evaluator_types, default_name=default_name
            )
        else:
            dataset_model_type = cls._serialization_type()
            dataset_model = dataset_model_type.model_validate_json(contents)
            return cls._from_dataset_model(
                dataset_model, custom_evaluator_types, custom_report_evaluator_types, default_name
            )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
        custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
        *,
        default_name: str | None = None,
    ) -> Self:
        """Load a dataset from a dictionary.

        Args:
            data: Dictionary representation of the dataset.
            custom_evaluator_types: Custom evaluator classes to use when deserializing the dataset.
                These are additional evaluators beyond the default ones.
            custom_report_evaluator_types: Custom report evaluator classes to use when deserializing the dataset.
                These are additional report evaluators beyond the default ones.
            default_name: Default name of the dataset, to be used if not specified in the data.

        Returns:
            A new Dataset instance created from the dictionary.

        Raises:
            ValidationError: If the dictionary cannot be converted to a valid dataset.
        """
        dataset_model_type = cls._serialization_type()
        dataset_model = dataset_model_type.model_validate(data)
        return cls._from_dataset_model(
            dataset_model, custom_evaluator_types, custom_report_evaluator_types, default_name
        )

    @classmethod
    def _from_dataset_model(
        cls,
        dataset_model: _DatasetModel[InputsT, OutputT, MetadataT],
        custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
        custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
        default_name: str | None = None,
    ) -> Self:
        """Create a Dataset from a _DatasetModel.

        Args:
            dataset_model: The _DatasetModel to convert.
            custom_evaluator_types: Custom evaluator classes to register for deserialization.
            custom_report_evaluator_types: Custom report evaluator classes to register for deserialization.
            default_name: Default name of the dataset, to be used if the value is `None` in the provided model.

        Returns:
            A new Dataset instance created from the _DatasetModel.
        """
        registry = _get_evaluator_registry(custom_evaluator_types, Evaluator, DEFAULT_EVALUATORS, 'evaluator')
        report_evaluator_registry = _get_evaluator_registry(
            custom_report_evaluator_types, ReportEvaluator, DEFAULT_REPORT_EVALUATORS, 'report evaluator'
        )

        cases: list[Case[InputsT, OutputT, MetadataT]] = []
        errors: list[ValueError] = []
        dataset_evaluators: list[Evaluator] = []
        for spec in dataset_model.evaluators:
            try:
                dataset_evaluator = _load_evaluator_from_registry(
                    registry, spec, 'evaluator', 'custom_evaluator_types', context='dataset'
                )
            except ValueError as e:
                errors.append(e)
                continue
            dataset_evaluators.append(dataset_evaluator)

        report_evaluators: list[ReportEvaluator] = []
        for spec in dataset_model.report_evaluators:
            try:
                report_evaluator = _load_evaluator_from_registry(
                    report_evaluator_registry,
                    spec,
                    'report evaluator',
                    'custom_report_evaluator_types',
                    context='dataset',
                )
            except ValueError as e:
                errors.append(e)
                continue
            report_evaluators.append(report_evaluator)

        for row in dataset_model.cases:
            evaluators: list[Evaluator] = []
            for spec in row.evaluators:
                try:
                    evaluator = _load_evaluator_from_registry(
                        registry, spec, 'evaluator', 'custom_evaluator_types', context=f'case {row.name!r}'
                    )
                except ValueError as e:
                    errors.append(e)
                    continue
                evaluators.append(evaluator)
            row = Case[InputsT, OutputT, MetadataT](
                name=row.name,
                inputs=row.inputs,
                metadata=row.metadata,
                expected_output=row.expected_output,
            )
            row.evaluators = evaluators
            cases.append(row)
        if errors:
            raise ExceptionGroup(f'{len(errors)} error(s) loading evaluators from registry', errors[:3])
        result = cls(name=dataset_model.name, cases=cases, report_evaluators=report_evaluators)
        if result.name is None:
            result.name = default_name
        result.evaluators = dataset_evaluators
        return result

    def to_file(
        self,
        path: Path | str,
        fmt: Literal['yaml', 'json'] | None = None,
        schema_path: Path | str | None = DEFAULT_SCHEMA_PATH_TEMPLATE,
        custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
        custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
    ):
        """Save the dataset to a file.

        Args:
            path: Path to save the dataset to.
            fmt: Format to use. If None, the format will be inferred from the file extension.
                Must be either 'yaml' or 'json'.
            schema_path: Path to save the JSON schema to. If None, no schema will be saved.
                Can be a string template with {stem} which will be replaced with the dataset filename stem.
            custom_evaluator_types: Custom evaluator classes to include in the schema.
            custom_report_evaluator_types: Custom report evaluator classes to include in the schema.
        """
        path = Path(path)
        fmt = self._infer_fmt(path, fmt)

        schema_ref: str | None = None
        if schema_path is not None:  # pragma: no branch
            if isinstance(schema_path, str):  # pragma: no branch
                schema_path = Path(schema_path.format(stem=path.stem))

            if not schema_path.is_absolute():
                schema_ref = str(schema_path)
                schema_path = path.parent / schema_path
            elif schema_path.is_relative_to(path):  # pragma: no cover
                schema_ref = str(_get_relative_path_reference(schema_path, path))
            else:  # pragma: no cover
                schema_ref = str(schema_path)
            self._save_schema(schema_path, custom_evaluator_types, custom_report_evaluator_types)

        context: dict[str, Any] = {'use_short_form': True}
        if fmt == 'yaml':
            dumped_data = self.model_dump(mode='json', by_alias=True, context=context)
            content = yaml.dump(dumped_data, sort_keys=False)
            if schema_ref:  # pragma: no branch
                yaml_language_server_line = f'{_YAML_SCHEMA_LINE_PREFIX}{schema_ref}'
                content = f'{yaml_language_server_line}\n{content}'
            path.write_text(content, encoding='utf-8')
        else:
            context['$schema'] = schema_ref
            json_data = self.model_dump_json(indent=2, by_alias=True, context=context)
            path.write_text(json_data + '\n', encoding='utf-8')

    @classmethod
    def model_json_schema_with_evaluators(
        cls,
        custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
        custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
    ) -> dict[str, Any]:
        """Generate a JSON schema for this dataset type, including evaluator details.

        This is useful for generating a schema that can be used to validate YAML-format dataset files.

        Args:
            custom_evaluator_types: Custom evaluator classes to include in the schema.
            custom_report_evaluator_types: Custom report evaluator classes to include in the schema.

        Returns:
            A dictionary representing the JSON schema.
        """
        evaluator_schema_types = _build_evaluator_schema_types(
            _get_evaluator_registry(custom_evaluator_types, Evaluator, DEFAULT_EVALUATORS, 'evaluator')
        )
        report_evaluator_schema_types = _build_evaluator_schema_types(
            _get_evaluator_registry(
                custom_report_evaluator_types, ReportEvaluator, DEFAULT_REPORT_EVALUATORS, 'report evaluator'
            )
        )

        in_type, out_type, meta_type = cls._params()

        # Note: we shadow the `Case` and `Dataset` class names here to generate a clean JSON schema
        class Case(BaseModel, extra='forbid'):  # pyright: ignore[reportUnusedClass]  # this _is_ used below, but pyright doesn't seem to notice..
            name: str | None = None
            inputs: in_type  # pyright: ignore[reportInvalidTypeForm]
            metadata: meta_type | None = None  # pyright: ignore[reportInvalidTypeForm]
            expected_output: out_type | None = None  # pyright: ignore[reportInvalidTypeForm]
            if evaluator_schema_types:  # pragma: no branch
                evaluators: list[Union[tuple(evaluator_schema_types)]] = []  # pyright: ignore  # noqa: UP007

        class Dataset(BaseModel, extra='forbid'):
            name: str | None = None
            cases: list[Case]
            if evaluator_schema_types:  # pragma: no branch
                evaluators: list[Union[tuple(evaluator_schema_types)]] = []  # pyright: ignore  # noqa: UP007
            if report_evaluator_schema_types:  # pragma: no branch
                report_evaluators: list[Union[tuple(report_evaluator_schema_types)]] = []  # pyright: ignore  # noqa: UP007

        json_schema = Dataset.model_json_schema()
        # See `_add_json_schema` below, since `$schema` is added to the JSON, it has to be supported in the JSON
        json_schema['properties']['$schema'] = {'type': 'string'}
        return json_schema

    @classmethod
    def _save_schema(
        cls,
        path: Path | str,
        custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
        custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
    ):
        """Save the JSON schema for this dataset type to a file.

        Args:
            path: Path to save the schema to.
            custom_evaluator_types: Custom evaluator classes to include in the schema.
            custom_report_evaluator_types: Custom report evaluator classes to include in the schema.
        """
        path = Path(path)
        json_schema = cls.model_json_schema_with_evaluators(custom_evaluator_types, custom_report_evaluator_types)
        schema_content = to_json(json_schema, indent=2).decode() + '\n'
        if not path.exists() or path.read_text(encoding='utf-8') != schema_content:  # pragma: no branch
            path.write_text(schema_content, encoding='utf-8')

    @classmethod
    @functools.cache
    def _serialization_type(cls) -> type[_DatasetModel[InputsT, OutputT, MetadataT]]:
        """Get the serialization type for this dataset class.

        Returns:
            A _DatasetModel type with the same generic parameters as this Dataset class.
        """
        input_type, output_type, metadata_type = cls._params()
        return _DatasetModel[input_type, output_type, metadata_type]

    @classmethod
    def _infer_fmt(cls, path: Path, fmt: Literal['yaml', 'json'] | None) -> Literal['yaml', 'json']:
        """Infer the format to use for a file based on its extension.

        Args:
            path: The path to infer the format for.
            fmt: The explicitly provided format, if any.

        Returns:
            The inferred format ('yaml' or 'json').

        Raises:
            ValueError: If the format cannot be inferred from the file extension.
        """
        if fmt is not None:
            return fmt
        suffix = path.suffix.lower()
        if suffix in {'.yaml', '.yml'}:
            return 'yaml'
        elif suffix == '.json':
            return 'json'
        raise ValueError(
            f'Could not infer format for filename {path.name!r}. Use the `fmt` argument to specify the format.'
        )

    @model_serializer(mode='wrap')
    def _add_json_schema(self, nxt: SerializerFunctionWrapHandler, info: SerializationInfo) -> dict[str, Any]:
        """Add the JSON schema path to the serialized output.

        See <https://github.com/json-schema-org/json-schema-spec/issues/828> for context, that seems to be the nearest
        there is to a spec for this.
        """
        context = cast(dict[str, Any] | None, info.context)
        if isinstance(context, dict) and (schema := context.get('$schema')):
            return {'$schema': schema} | nxt(self)
        else:
            return nxt(self)
````

#### name

```python
name: str | None = None
```

Optional name of the dataset.

#### cases

```python
cases: list[Case[InputsT, OutputT, MetadataT]]
```

List of test cases in the dataset.

#### evaluators

```python
evaluators: list[Evaluator[InputsT, OutputT, MetadataT]] = (
    []
)
```

List of evaluators to be used on all cases in the dataset.

#### report_evaluators

```python
report_evaluators: list[
    ReportEvaluator[InputsT, OutputT, MetadataT]
] = []
```

Evaluators that operate on the full report to produce experiment-wide analyses.

#### __init__

```python
__init__(
    *,
    name: str | None = None,
    cases: Sequence[Case[InputsT, OutputT, MetadataT]],
    evaluators: Sequence[
        Evaluator[InputsT, OutputT, MetadataT]
    ] = (),
    report_evaluators: Sequence[
        ReportEvaluator[InputsT, OutputT, MetadataT]
    ] = ()
)
```

Initialize a new dataset with test cases and optional evaluators.

Parameters:

| Name                | Type                                                     | Description                                                                    | Default                        |
| ------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------ |
| `name`              | \`str                                                    | None\`                                                                         | Optional name for the dataset. |
| `cases`             | `Sequence[Case[InputsT, OutputT, MetadataT]]`            | Sequence of test cases to include in the dataset.                              | *required*                     |
| `evaluators`        | `Sequence[Evaluator[InputsT, OutputT, MetadataT]]`       | Optional sequence of evaluators to apply to all cases in the dataset.          | `()`                           |
| `report_evaluators` | `Sequence[ReportEvaluator[InputsT, OutputT, MetadataT]]` | Optional sequence of report evaluators that run on the full evaluation report. | `()`                           |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def __init__(
    self,
    *,
    name: str | None = None,
    cases: Sequence[Case[InputsT, OutputT, MetadataT]],
    evaluators: Sequence[Evaluator[InputsT, OutputT, MetadataT]] = (),
    report_evaluators: Sequence[ReportEvaluator[InputsT, OutputT, MetadataT]] = (),
):
    """Initialize a new dataset with test cases and optional evaluators.

    Args:
        name: Optional name for the dataset.
        cases: Sequence of test cases to include in the dataset.
        evaluators: Optional sequence of evaluators to apply to all cases in the dataset.
        report_evaluators: Optional sequence of report evaluators that run on the full evaluation report.
    """
    case_names = set[str]()
    for case in cases:
        if case.name is None:
            continue
        if case.name in case_names:
            raise ValueError(f'Duplicate case name: {case.name!r}')
        case_names.add(case.name)

    super().__init__(
        name=name,
        cases=cases,
        evaluators=list(evaluators),
        report_evaluators=list(report_evaluators),
    )
```

#### evaluate

```python
evaluate(
    task: (
        Callable[[InputsT], Awaitable[OutputT]]
        | Callable[[InputsT], OutputT]
    ),
    name: str | None = None,
    max_concurrency: int | None = None,
    progress: bool = True,
    retry_task: RetryConfig | None = None,
    retry_evaluators: RetryConfig | None = None,
    *,
    task_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    repeat: int = 1,
    lifecycle: (
        type[CaseLifecycle[InputsT, OutputT, MetadataT]]
        | None
    ) = None
) -> EvaluationReport[InputsT, OutputT, MetadataT]
```

Evaluates the test cases in the dataset using the given task.

This method runs the task on each case in the dataset, applies evaluators, and collects results into a report. Cases are run concurrently, limited by `max_concurrency` if specified.

Parameters:

| Name               | Type                                                 | Description                                                                                                                                                   | Default                                                                                                                                                                                               |
| ------------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `task`             | \`Callable\[[InputsT], Awaitable[OutputT]\]          | Callable\[[InputsT], OutputT\]\`                                                                                                                              | The task to evaluate. This should be a callable that takes the inputs of the case and returns the output.                                                                                             |
| `name`             | \`str                                                | None\`                                                                                                                                                        | The name of the experiment being run, this is used to identify the experiment in the report. If omitted, the task_name will be used; if that is not specified, the name of the task function is used. |
| `max_concurrency`  | \`int                                                | None\`                                                                                                                                                        | The maximum number of concurrent evaluations of the task to allow. If None, all cases will be evaluated concurrently.                                                                                 |
| `progress`         | `bool`                                               | Whether to show a progress bar for the evaluation. Defaults to True.                                                                                          | `True`                                                                                                                                                                                                |
| `retry_task`       | \`RetryConfig                                        | None\`                                                                                                                                                        | Optional retry configuration for the task execution.                                                                                                                                                  |
| `retry_evaluators` | \`RetryConfig                                        | None\`                                                                                                                                                        | Optional retry configuration for evaluator execution.                                                                                                                                                 |
| `task_name`        | \`str                                                | None\`                                                                                                                                                        | Optional override to the name of the task being executed, otherwise the name of the task function will be used.                                                                                       |
| `metadata`         | \`dict[str, Any]                                     | None\`                                                                                                                                                        | Optional dict of experiment metadata.                                                                                                                                                                 |
| `repeat`           | `int`                                                | Number of times to run each case. When > 1, each case is run multiple times and results are grouped by the original case name for aggregation. Defaults to 1. | `1`                                                                                                                                                                                                   |
| `lifecycle`        | \`type\[CaseLifecycle[InputsT, OutputT, MetadataT]\] | None\`                                                                                                                                                        | Optional lifecycle class for per-case setup, context preparation, and teardown hooks. A new instance is created for each case. See CaseLifecycle.                                                     |

Returns:

| Type                                            | Description                                        |
| ----------------------------------------------- | -------------------------------------------------- |
| `EvaluationReport[InputsT, OutputT, MetadataT]` | A report containing the results of the evaluation. |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
async def evaluate(
    self,
    task: Callable[[InputsT], Awaitable[OutputT]] | Callable[[InputsT], OutputT],
    name: str | None = None,
    max_concurrency: int | None = None,
    progress: bool = True,
    retry_task: RetryConfig | None = None,
    retry_evaluators: RetryConfig | None = None,
    *,
    task_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    repeat: int = 1,
    lifecycle: type[CaseLifecycle[InputsT, OutputT, MetadataT]] | None = None,
) -> EvaluationReport[InputsT, OutputT, MetadataT]:
    """Evaluates the test cases in the dataset using the given task.

    This method runs the task on each case in the dataset, applies evaluators,
    and collects results into a report. Cases are run concurrently, limited by `max_concurrency` if specified.

    Args:
        task: The task to evaluate. This should be a callable that takes the inputs of the case
            and returns the output.
        name: The name of the experiment being run, this is used to identify the experiment in the report.
            If omitted, the task_name will be used; if that is not specified, the name of the task function is used.
        max_concurrency: The maximum number of concurrent evaluations of the task to allow.
            If None, all cases will be evaluated concurrently.
        progress: Whether to show a progress bar for the evaluation. Defaults to `True`.
        retry_task: Optional retry configuration for the task execution.
        retry_evaluators: Optional retry configuration for evaluator execution.
        task_name: Optional override to the name of the task being executed, otherwise the name of the task
            function will be used.
        metadata: Optional dict of experiment metadata.
        repeat: Number of times to run each case. When > 1, each case is run multiple times and
            results are grouped by the original case name for aggregation. Defaults to 1.
        lifecycle: Optional lifecycle class for per-case setup, context preparation, and teardown hooks.
            A new instance is created for each case. See [`CaseLifecycle`][pydantic_evals.lifecycle.CaseLifecycle].

    Returns:
        A report containing the results of the evaluation.
    """
    if repeat < 1:
        raise ValueError(f'repeat must be >= 1, got {repeat}')

    task_name = task_name or get_unwrapped_function_name(task)
    name = name or task_name

    tasks_to_run = self._build_tasks_to_run(repeat)
    total_tasks = len(tasks_to_run)
    progress_bar = Progress() if progress else None

    limiter = anyio.Semaphore(max_concurrency) if max_concurrency is not None else AsyncExitStack()

    extra_attributes: dict[str, Any] = {'gen_ai.operation.name': 'experiment'}
    if metadata is not None:
        extra_attributes['metadata'] = metadata
    if repeat > 1:
        extra_attributes['logfire.experiment.repeat'] = repeat
    with (
        logfire_span(
            'evaluate {name}',
            name=name,
            task_name=task_name,
            dataset_name=self.name,
            n_cases=len(self.cases),
            **extra_attributes,
        ) as eval_span,
        progress_bar or nullcontext(),
    ):
        task_id = progress_bar.add_task(f'Evaluating {task_name}', total=total_tasks) if progress_bar else None

        async def _handle_case(
            case: Case[InputsT, OutputT, MetadataT],
            report_case_name: str,
            source_case_name: str | None,
        ):
            async with limiter:
                result = await _run_task_and_evaluators(
                    task,
                    case,
                    report_case_name,
                    self.evaluators,
                    retry_task,
                    retry_evaluators,
                    source_case_name=source_case_name,
                    lifecycle=lifecycle,
                )
                if progress_bar and task_id is not None:  # pragma: no branch
                    progress_bar.update(task_id, advance=1)
                return result

        if (context := eval_span.context) is None:  # pragma: no cover
            trace_id = None
            span_id = None
        else:
            trace_id = f'{context.trace_id:032x}'
            span_id = f'{context.span_id:016x}'
        cases_and_failures = await task_group_gather(
            [
                lambda case=case, rn=report_name, scn=source_name: _handle_case(case, rn, scn)
                for case, report_name, source_name in tasks_to_run
            ]
        )
        cases: list[ReportCase] = []
        failures: list[ReportCaseFailure] = []
        for item in cases_and_failures:
            if isinstance(item, ReportCase):
                cases.append(item)
            else:
                failures.append(item)
        report = EvaluationReport(
            name=name,
            cases=cases,
            failures=failures,
            experiment_metadata=metadata,
            span_id=span_id,
            trace_id=trace_id,
        )

        # Run report evaluators
        if self.report_evaluators:
            report_ctx = ReportEvaluatorContext(
                name=name,
                report=report,
                experiment_metadata=metadata,
            )
            await _run_report_evaluators(self.report_evaluators, report_ctx)

        _set_experiment_span_attributes(eval_span, report, metadata, len(self.cases), repeat)
    return report
```

#### evaluate_sync

```python
evaluate_sync(
    task: (
        Callable[[InputsT], Awaitable[OutputT]]
        | Callable[[InputsT], OutputT]
    ),
    name: str | None = None,
    max_concurrency: int | None = None,
    progress: bool = True,
    retry_task: RetryConfig | None = None,
    retry_evaluators: RetryConfig | None = None,
    *,
    task_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    repeat: int = 1,
    lifecycle: (
        type[CaseLifecycle[InputsT, OutputT, MetadataT]]
        | None
    ) = None
) -> EvaluationReport[InputsT, OutputT, MetadataT]
```

Evaluates the test cases in the dataset using the given task.

This is a synchronous wrapper around evaluate provided for convenience.

Parameters:

| Name               | Type                                                 | Description                                                                                                                                                   | Default                                                                                                                                                                                               |
| ------------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `task`             | \`Callable\[[InputsT], Awaitable[OutputT]\]          | Callable\[[InputsT], OutputT\]\`                                                                                                                              | The task to evaluate. This should be a callable that takes the inputs of the case and returns the output.                                                                                             |
| `name`             | \`str                                                | None\`                                                                                                                                                        | The name of the experiment being run, this is used to identify the experiment in the report. If omitted, the task_name will be used; if that is not specified, the name of the task function is used. |
| `max_concurrency`  | \`int                                                | None\`                                                                                                                                                        | The maximum number of concurrent evaluations of the task to allow. If None, all cases will be evaluated concurrently.                                                                                 |
| `progress`         | `bool`                                               | Whether to show a progress bar for the evaluation. Defaults to True.                                                                                          | `True`                                                                                                                                                                                                |
| `retry_task`       | \`RetryConfig                                        | None\`                                                                                                                                                        | Optional retry configuration for the task execution.                                                                                                                                                  |
| `retry_evaluators` | \`RetryConfig                                        | None\`                                                                                                                                                        | Optional retry configuration for evaluator execution.                                                                                                                                                 |
| `task_name`        | \`str                                                | None\`                                                                                                                                                        | Optional override to the name of the task being executed, otherwise the name of the task function will be used.                                                                                       |
| `metadata`         | \`dict[str, Any]                                     | None\`                                                                                                                                                        | Optional dict of experiment metadata.                                                                                                                                                                 |
| `repeat`           | `int`                                                | Number of times to run each case. When > 1, each case is run multiple times and results are grouped by the original case name for aggregation. Defaults to 1. | `1`                                                                                                                                                                                                   |
| `lifecycle`        | \`type\[CaseLifecycle[InputsT, OutputT, MetadataT]\] | None\`                                                                                                                                                        | Optional lifecycle class for per-case setup, context preparation, and teardown hooks. A new instance is created for each case. See CaseLifecycle.                                                     |

Returns:

| Type                                            | Description                                        |
| ----------------------------------------------- | -------------------------------------------------- |
| `EvaluationReport[InputsT, OutputT, MetadataT]` | A report containing the results of the evaluation. |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def evaluate_sync(
    self,
    task: Callable[[InputsT], Awaitable[OutputT]] | Callable[[InputsT], OutputT],
    name: str | None = None,
    max_concurrency: int | None = None,
    progress: bool = True,
    retry_task: RetryConfig | None = None,
    retry_evaluators: RetryConfig | None = None,
    *,
    task_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    repeat: int = 1,
    lifecycle: type[CaseLifecycle[InputsT, OutputT, MetadataT]] | None = None,
) -> EvaluationReport[InputsT, OutputT, MetadataT]:
    """Evaluates the test cases in the dataset using the given task.

    This is a synchronous wrapper around [`evaluate`][pydantic_evals.dataset.Dataset.evaluate] provided for convenience.

    Args:
        task: The task to evaluate. This should be a callable that takes the inputs of the case
            and returns the output.
        name: The name of the experiment being run, this is used to identify the experiment in the report.
            If omitted, the task_name will be used; if that is not specified, the name of the task function is used.
        max_concurrency: The maximum number of concurrent evaluations of the task to allow.
            If None, all cases will be evaluated concurrently.
        progress: Whether to show a progress bar for the evaluation. Defaults to `True`.
        retry_task: Optional retry configuration for the task execution.
        retry_evaluators: Optional retry configuration for evaluator execution.
        task_name: Optional override to the name of the task being executed, otherwise the name of the task
            function will be used.
        metadata: Optional dict of experiment metadata.
        repeat: Number of times to run each case. When > 1, each case is run multiple times and
            results are grouped by the original case name for aggregation. Defaults to 1.
        lifecycle: Optional lifecycle class for per-case setup, context preparation, and teardown hooks.
            A new instance is created for each case. See [`CaseLifecycle`][pydantic_evals.lifecycle.CaseLifecycle].

    Returns:
        A report containing the results of the evaluation.
    """
    return get_event_loop().run_until_complete(
        self.evaluate(
            task,
            name=name,
            max_concurrency=max_concurrency,
            progress=progress,
            retry_task=retry_task,
            retry_evaluators=retry_evaluators,
            task_name=task_name,
            metadata=metadata,
            repeat=repeat,
            lifecycle=lifecycle,
        )
    )
```

#### add_case

```python
add_case(
    *,
    name: str | None = None,
    inputs: InputsT,
    metadata: MetadataT | None = None,
    expected_output: OutputT | None = None,
    evaluators: tuple[
        Evaluator[InputsT, OutputT, MetadataT], ...
    ] = ()
) -> None
```

Adds a case to the dataset.

This is a convenience method for creating a Case and adding it to the dataset.

Parameters:

| Name              | Type                                                 | Description                                                                         | Default                                                                       |
| ----------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `name`            | \`str                                                | None\`                                                                              | Optional name for the case. If not provided, a generic name will be assigned. |
| `inputs`          | `InputsT`                                            | The inputs to the task being evaluated.                                             | *required*                                                                    |
| `metadata`        | \`MetadataT                                          | None\`                                                                              | Optional metadata for the case, which can be used by evaluators.              |
| `expected_output` | \`OutputT                                            | None\`                                                                              | The expected output of the task, used for comparison in evaluators.           |
| `evaluators`      | `tuple[Evaluator[InputsT, OutputT, MetadataT], ...]` | Tuple of evaluators specific to this case, in addition to dataset-level evaluators. | `()`                                                                          |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def add_case(
    self,
    *,
    name: str | None = None,
    inputs: InputsT,
    metadata: MetadataT | None = None,
    expected_output: OutputT | None = None,
    evaluators: tuple[Evaluator[InputsT, OutputT, MetadataT], ...] = (),
) -> None:
    """Adds a case to the dataset.

    This is a convenience method for creating a [`Case`][pydantic_evals.Case] and adding it to the dataset.

    Args:
        name: Optional name for the case. If not provided, a generic name will be assigned.
        inputs: The inputs to the task being evaluated.
        metadata: Optional metadata for the case, which can be used by evaluators.
        expected_output: The expected output of the task, used for comparison in evaluators.
        evaluators: Tuple of evaluators specific to this case, in addition to dataset-level evaluators.
    """
    if name in {case.name for case in self.cases}:
        raise ValueError(f'Duplicate case name: {name!r}')

    case = Case[InputsT, OutputT, MetadataT](
        name=name,
        inputs=inputs,
        metadata=metadata,
        expected_output=expected_output,
        evaluators=evaluators,
    )
    self.cases.append(case)
```

#### add_evaluator

```python
add_evaluator(
    evaluator: Evaluator[InputsT, OutputT, MetadataT],
    specific_case: str | None = None,
) -> None
```

Adds an evaluator to the dataset or a specific case.

Parameters:

| Name            | Type                                     | Description           | Default                                                                                                                                     |
| --------------- | ---------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `evaluator`     | `Evaluator[InputsT, OutputT, MetadataT]` | The evaluator to add. | *required*                                                                                                                                  |
| `specific_case` | \`str                                    | None\`                | If provided, the evaluator will only be added to the case with this name. If None, the evaluator will be added to all cases in the dataset. |

Raises:

| Type         | Description                                                                    |
| ------------ | ------------------------------------------------------------------------------ |
| `ValueError` | If specific_case is provided but no case with that name exists in the dataset. |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def add_evaluator(
    self,
    evaluator: Evaluator[InputsT, OutputT, MetadataT],
    specific_case: str | None = None,
) -> None:
    """Adds an evaluator to the dataset or a specific case.

    Args:
        evaluator: The evaluator to add.
        specific_case: If provided, the evaluator will only be added to the case with this name.
            If None, the evaluator will be added to all cases in the dataset.

    Raises:
        ValueError: If `specific_case` is provided but no case with that name exists in the dataset.
    """
    if specific_case is None:
        self.evaluators.append(evaluator)
    else:
        # If this is too slow, we could try to add a case lookup dict.
        # Note that if we do that, we'd need to make the cases list private to prevent modification.
        added = False
        for case in self.cases:
            if case.name == specific_case:
                case.evaluators.append(evaluator)
                added = True
        if not added:
            raise ValueError(f'Case {specific_case!r} not found in the dataset')
```

#### from_file

```python
from_file(
    path: Path | str,
    fmt: Literal["yaml", "json"] | None = None,
    custom_evaluator_types: Sequence[
        type[Evaluator[InputsT, OutputT, MetadataT]]
    ] = (),
    custom_report_evaluator_types: Sequence[
        type[ReportEvaluator[InputsT, OutputT, MetadataT]]
    ] = (),
) -> Self
```

Load a dataset from a file.

Parameters:

| Name                            | Type                                                           | Description                                                                                                                            | Default                                                                                                            |
| ------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `path`                          | \`Path                                                         | str\`                                                                                                                                  | Path to the file to load.                                                                                          |
| `fmt`                           | \`Literal['yaml', 'json']                                      | None\`                                                                                                                                 | Format of the file. If None, the format will be inferred from the file extension. Must be either 'yaml' or 'json'. |
| `custom_evaluator_types`        | `Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]]`       | Custom evaluator classes to use when deserializing the dataset. These are additional evaluators beyond the default ones.               | `()`                                                                                                               |
| `custom_report_evaluator_types` | `Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]]` | Custom report evaluator classes to use when deserializing the dataset. These are additional report evaluators beyond the default ones. | `()`                                                                                                               |

Returns:

| Type   | Description                                  |
| ------ | -------------------------------------------- |
| `Self` | A new Dataset instance loaded from the file. |

Raises:

| Type              | Description                                               |
| ----------------- | --------------------------------------------------------- |
| `ValidationError` | If the file cannot be parsed as a valid dataset.          |
| `ValueError`      | If the format cannot be inferred from the file extension. |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
@classmethod
def from_file(
    cls,
    path: Path | str,
    fmt: Literal['yaml', 'json'] | None = None,
    custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
    custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
) -> Self:
    """Load a dataset from a file.

    Args:
        path: Path to the file to load.
        fmt: Format of the file. If None, the format will be inferred from the file extension.
            Must be either 'yaml' or 'json'.
        custom_evaluator_types: Custom evaluator classes to use when deserializing the dataset.
            These are additional evaluators beyond the default ones.
        custom_report_evaluator_types: Custom report evaluator classes to use when deserializing the dataset.
            These are additional report evaluators beyond the default ones.

    Returns:
        A new Dataset instance loaded from the file.

    Raises:
        ValidationError: If the file cannot be parsed as a valid dataset.
        ValueError: If the format cannot be inferred from the file extension.
    """
    path = Path(path)
    fmt = cls._infer_fmt(path, fmt)

    raw = Path(path).read_text(encoding='utf-8')
    try:
        return cls.from_text(
            raw,
            fmt=fmt,
            custom_evaluator_types=custom_evaluator_types,
            custom_report_evaluator_types=custom_report_evaluator_types,
            default_name=path.stem,
        )
    except ValidationError as e:  # pragma: no cover
        raise ValueError(f'{path} contains data that does not match the schema for {cls.__name__}:\n{e}.') from e
```

#### from_text

```python
from_text(
    contents: str,
    fmt: Literal["yaml", "json"] = "yaml",
    custom_evaluator_types: Sequence[
        type[Evaluator[InputsT, OutputT, MetadataT]]
    ] = (),
    custom_report_evaluator_types: Sequence[
        type[ReportEvaluator[InputsT, OutputT, MetadataT]]
    ] = (),
    *,
    default_name: str | None = None
) -> Self
```

Load a dataset from a string.

Parameters:

| Name                            | Type                                                           | Description                                                                                                                            | Default                                                                              |
| ------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `contents`                      | `str`                                                          | The string content to parse.                                                                                                           | *required*                                                                           |
| `fmt`                           | `Literal['yaml', 'json']`                                      | Format of the content. Must be either 'yaml' or 'json'.                                                                                | `'yaml'`                                                                             |
| `custom_evaluator_types`        | `Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]]`       | Custom evaluator classes to use when deserializing the dataset. These are additional evaluators beyond the default ones.               | `()`                                                                                 |
| `custom_report_evaluator_types` | `Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]]` | Custom report evaluator classes to use when deserializing the dataset. These are additional report evaluators beyond the default ones. | `()`                                                                                 |
| `default_name`                  | \`str                                                          | None\`                                                                                                                                 | Default name of the dataset, to be used if not specified in the serialized contents. |

Returns:

| Type   | Description                                    |
| ------ | ---------------------------------------------- |
| `Self` | A new Dataset instance parsed from the string. |

Raises:

| Type              | Description                                         |
| ----------------- | --------------------------------------------------- |
| `ValidationError` | If the content cannot be parsed as a valid dataset. |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
@classmethod
def from_text(
    cls,
    contents: str,
    fmt: Literal['yaml', 'json'] = 'yaml',
    custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
    custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
    *,
    default_name: str | None = None,
) -> Self:
    """Load a dataset from a string.

    Args:
        contents: The string content to parse.
        fmt: Format of the content. Must be either 'yaml' or 'json'.
        custom_evaluator_types: Custom evaluator classes to use when deserializing the dataset.
            These are additional evaluators beyond the default ones.
        custom_report_evaluator_types: Custom report evaluator classes to use when deserializing the dataset.
            These are additional report evaluators beyond the default ones.
        default_name: Default name of the dataset, to be used if not specified in the serialized contents.

    Returns:
        A new Dataset instance parsed from the string.

    Raises:
        ValidationError: If the content cannot be parsed as a valid dataset.
    """
    if fmt == 'yaml':
        loaded = yaml.safe_load(contents)
        return cls.from_dict(
            loaded, custom_evaluator_types, custom_report_evaluator_types, default_name=default_name
        )
    else:
        dataset_model_type = cls._serialization_type()
        dataset_model = dataset_model_type.model_validate_json(contents)
        return cls._from_dataset_model(
            dataset_model, custom_evaluator_types, custom_report_evaluator_types, default_name
        )
```

#### from_dict

```python
from_dict(
    data: dict[str, Any],
    custom_evaluator_types: Sequence[
        type[Evaluator[InputsT, OutputT, MetadataT]]
    ] = (),
    custom_report_evaluator_types: Sequence[
        type[ReportEvaluator[InputsT, OutputT, MetadataT]]
    ] = (),
    *,
    default_name: str | None = None
) -> Self
```

Load a dataset from a dictionary.

Parameters:

| Name                            | Type                                                           | Description                                                                                                                            | Default                                                               |
| ------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `data`                          | `dict[str, Any]`                                               | Dictionary representation of the dataset.                                                                                              | *required*                                                            |
| `custom_evaluator_types`        | `Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]]`       | Custom evaluator classes to use when deserializing the dataset. These are additional evaluators beyond the default ones.               | `()`                                                                  |
| `custom_report_evaluator_types` | `Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]]` | Custom report evaluator classes to use when deserializing the dataset. These are additional report evaluators beyond the default ones. | `()`                                                                  |
| `default_name`                  | \`str                                                          | None\`                                                                                                                                 | Default name of the dataset, to be used if not specified in the data. |

Returns:

| Type   | Description                                         |
| ------ | --------------------------------------------------- |
| `Self` | A new Dataset instance created from the dictionary. |

Raises:

| Type              | Description                                               |
| ----------------- | --------------------------------------------------------- |
| `ValidationError` | If the dictionary cannot be converted to a valid dataset. |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
@classmethod
def from_dict(
    cls,
    data: dict[str, Any],
    custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
    custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
    *,
    default_name: str | None = None,
) -> Self:
    """Load a dataset from a dictionary.

    Args:
        data: Dictionary representation of the dataset.
        custom_evaluator_types: Custom evaluator classes to use when deserializing the dataset.
            These are additional evaluators beyond the default ones.
        custom_report_evaluator_types: Custom report evaluator classes to use when deserializing the dataset.
            These are additional report evaluators beyond the default ones.
        default_name: Default name of the dataset, to be used if not specified in the data.

    Returns:
        A new Dataset instance created from the dictionary.

    Raises:
        ValidationError: If the dictionary cannot be converted to a valid dataset.
    """
    dataset_model_type = cls._serialization_type()
    dataset_model = dataset_model_type.model_validate(data)
    return cls._from_dataset_model(
        dataset_model, custom_evaluator_types, custom_report_evaluator_types, default_name
    )
```

#### to_file

```python
to_file(
    path: Path | str,
    fmt: Literal["yaml", "json"] | None = None,
    schema_path: (
        Path | str | None
    ) = DEFAULT_SCHEMA_PATH_TEMPLATE,
    custom_evaluator_types: Sequence[
        type[Evaluator[InputsT, OutputT, MetadataT]]
    ] = (),
    custom_report_evaluator_types: Sequence[
        type[ReportEvaluator[InputsT, OutputT, MetadataT]]
    ] = (),
)
```

Save the dataset to a file.

Parameters:

| Name                            | Type                                                           | Description                                               | Default                                                                                                       |
| ------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `path`                          | \`Path                                                         | str\`                                                     | Path to save the dataset to.                                                                                  |
| `fmt`                           | \`Literal['yaml', 'json']                                      | None\`                                                    | Format to use. If None, the format will be inferred from the file extension. Must be either 'yaml' or 'json'. |
| `schema_path`                   | \`Path                                                         | str                                                       | None\`                                                                                                        |
| `custom_evaluator_types`        | `Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]]`       | Custom evaluator classes to include in the schema.        | `()`                                                                                                          |
| `custom_report_evaluator_types` | `Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]]` | Custom report evaluator classes to include in the schema. | `()`                                                                                                          |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def to_file(
    self,
    path: Path | str,
    fmt: Literal['yaml', 'json'] | None = None,
    schema_path: Path | str | None = DEFAULT_SCHEMA_PATH_TEMPLATE,
    custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
    custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
):
    """Save the dataset to a file.

    Args:
        path: Path to save the dataset to.
        fmt: Format to use. If None, the format will be inferred from the file extension.
            Must be either 'yaml' or 'json'.
        schema_path: Path to save the JSON schema to. If None, no schema will be saved.
            Can be a string template with {stem} which will be replaced with the dataset filename stem.
        custom_evaluator_types: Custom evaluator classes to include in the schema.
        custom_report_evaluator_types: Custom report evaluator classes to include in the schema.
    """
    path = Path(path)
    fmt = self._infer_fmt(path, fmt)

    schema_ref: str | None = None
    if schema_path is not None:  # pragma: no branch
        if isinstance(schema_path, str):  # pragma: no branch
            schema_path = Path(schema_path.format(stem=path.stem))

        if not schema_path.is_absolute():
            schema_ref = str(schema_path)
            schema_path = path.parent / schema_path
        elif schema_path.is_relative_to(path):  # pragma: no cover
            schema_ref = str(_get_relative_path_reference(schema_path, path))
        else:  # pragma: no cover
            schema_ref = str(schema_path)
        self._save_schema(schema_path, custom_evaluator_types, custom_report_evaluator_types)

    context: dict[str, Any] = {'use_short_form': True}
    if fmt == 'yaml':
        dumped_data = self.model_dump(mode='json', by_alias=True, context=context)
        content = yaml.dump(dumped_data, sort_keys=False)
        if schema_ref:  # pragma: no branch
            yaml_language_server_line = f'{_YAML_SCHEMA_LINE_PREFIX}{schema_ref}'
            content = f'{yaml_language_server_line}\n{content}'
        path.write_text(content, encoding='utf-8')
    else:
        context['$schema'] = schema_ref
        json_data = self.model_dump_json(indent=2, by_alias=True, context=context)
        path.write_text(json_data + '\n', encoding='utf-8')
```

#### model_json_schema_with_evaluators

```python
model_json_schema_with_evaluators(
    custom_evaluator_types: Sequence[
        type[Evaluator[InputsT, OutputT, MetadataT]]
    ] = (),
    custom_report_evaluator_types: Sequence[
        type[ReportEvaluator[InputsT, OutputT, MetadataT]]
    ] = (),
) -> dict[str, Any]
```

Generate a JSON schema for this dataset type, including evaluator details.

This is useful for generating a schema that can be used to validate YAML-format dataset files.

Parameters:

| Name                            | Type                                                           | Description                                               | Default |
| ------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------- | ------- |
| `custom_evaluator_types`        | `Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]]`       | Custom evaluator classes to include in the schema.        | `()`    |
| `custom_report_evaluator_types` | `Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]]` | Custom report evaluator classes to include in the schema. | `()`    |

Returns:

| Type             | Description                                |
| ---------------- | ------------------------------------------ |
| `dict[str, Any]` | A dictionary representing the JSON schema. |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
@classmethod
def model_json_schema_with_evaluators(
    cls,
    custom_evaluator_types: Sequence[type[Evaluator[InputsT, OutputT, MetadataT]]] = (),
    custom_report_evaluator_types: Sequence[type[ReportEvaluator[InputsT, OutputT, MetadataT]]] = (),
) -> dict[str, Any]:
    """Generate a JSON schema for this dataset type, including evaluator details.

    This is useful for generating a schema that can be used to validate YAML-format dataset files.

    Args:
        custom_evaluator_types: Custom evaluator classes to include in the schema.
        custom_report_evaluator_types: Custom report evaluator classes to include in the schema.

    Returns:
        A dictionary representing the JSON schema.
    """
    evaluator_schema_types = _build_evaluator_schema_types(
        _get_evaluator_registry(custom_evaluator_types, Evaluator, DEFAULT_EVALUATORS, 'evaluator')
    )
    report_evaluator_schema_types = _build_evaluator_schema_types(
        _get_evaluator_registry(
            custom_report_evaluator_types, ReportEvaluator, DEFAULT_REPORT_EVALUATORS, 'report evaluator'
        )
    )

    in_type, out_type, meta_type = cls._params()

    # Note: we shadow the `Case` and `Dataset` class names here to generate a clean JSON schema
    class Case(BaseModel, extra='forbid'):  # pyright: ignore[reportUnusedClass]  # this _is_ used below, but pyright doesn't seem to notice..
        name: str | None = None
        inputs: in_type  # pyright: ignore[reportInvalidTypeForm]
        metadata: meta_type | None = None  # pyright: ignore[reportInvalidTypeForm]
        expected_output: out_type | None = None  # pyright: ignore[reportInvalidTypeForm]
        if evaluator_schema_types:  # pragma: no branch
            evaluators: list[Union[tuple(evaluator_schema_types)]] = []  # pyright: ignore  # noqa: UP007

    class Dataset(BaseModel, extra='forbid'):
        name: str | None = None
        cases: list[Case]
        if evaluator_schema_types:  # pragma: no branch
            evaluators: list[Union[tuple(evaluator_schema_types)]] = []  # pyright: ignore  # noqa: UP007
        if report_evaluator_schema_types:  # pragma: no branch
            report_evaluators: list[Union[tuple(report_evaluator_schema_types)]] = []  # pyright: ignore  # noqa: UP007

    json_schema = Dataset.model_json_schema()
    # See `_add_json_schema` below, since `$schema` is added to the JSON, it has to be supported in the JSON
    json_schema['properties']['$schema'] = {'type': 'string'}
    return json_schema
```

### set_eval_attribute

```python
set_eval_attribute(name: str, value: Any) -> None
```

Set an attribute on the current task run.

Parameters:

| Name    | Type  | Description                 | Default    |
| ------- | ----- | --------------------------- | ---------- |
| `name`  | `str` | The name of the attribute.  | *required* |
| `value` | `Any` | The value of the attribute. | *required* |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def set_eval_attribute(name: str, value: Any) -> None:
    """Set an attribute on the current task run.

    Args:
        name: The name of the attribute.
        value: The value of the attribute.
    """
    current_case = _CURRENT_TASK_RUN.get()
    if current_case is not None:  # pragma: no branch
        current_case.record_attribute(name, value)
```

### increment_eval_metric

```python
increment_eval_metric(
    name: str, amount: int | float
) -> None
```

Increment a metric on the current task run.

Parameters:

| Name     | Type  | Description             | Default                     |
| -------- | ----- | ----------------------- | --------------------------- |
| `name`   | `str` | The name of the metric. | *required*                  |
| `amount` | \`int | float\`                 | The amount to increment by. |

Source code in `pydantic_evals/pydantic_evals/dataset.py`

```python
def increment_eval_metric(name: str, amount: int | float) -> None:
    """Increment a metric on the current task run.

    Args:
        name: The name of the metric.
        amount: The amount to increment by.
    """
    current_case = _CURRENT_TASK_RUN.get()
    if current_case is not None:  # pragma: no branch
        current_case.increment_metric(name, amount)
```
