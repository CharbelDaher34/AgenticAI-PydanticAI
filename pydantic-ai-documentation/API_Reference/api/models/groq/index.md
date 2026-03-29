# `pydantic_ai.models.groq`

## Setup

For details on how to set up authentication with this model, see [model configuration for Groq](https://ai.pydantic.dev/models/groq/index.md).

### ProductionGroqModelNames

```python
ProductionGroqModelNames = Literal[
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-guard-4-12b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "whisper-large-v3",
    "whisper-large-v3-turbo",
]
```

Production Groq models from <https://console.groq.com/docs/models#production-models>.

### PreviewGroqModelNames

```python
PreviewGroqModelNames = Literal[
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-prompt-guard-2-22m",
    "meta-llama/llama-prompt-guard-2-86m",
    "moonshotai/kimi-k2-instruct-0905",
    "openai/gpt-oss-safeguard-20b",
    "playai-tts",
    "playai-tts-arabic",
    "qwen/qwen-3-32b",
]
```

Preview Groq models from <https://console.groq.com/docs/models#preview-models>.

### GroqModelName

```python
GroqModelName = (
    str | ProductionGroqModelNames | PreviewGroqModelNames
)
```

Possible Groq model names.

Since Groq supports a variety of models and the list changes frequencly, we explicitly list the named models as of 2025-03-31 but allow any name in the type hints.

See <https://console.groq.com/docs/models> for an up to date date list of models and more details.

### GroqModelSettings

Bases: `ModelSettings`

Settings used for a Groq model request.

Source code in `pydantic_ai_slim/pydantic_ai/models/groq.py`

```python
class GroqModelSettings(ModelSettings, total=False):
    """Settings used for a Groq model request."""

    # ALL FIELDS MUST BE `groq_` PREFIXED SO YOU CAN MERGE THEM WITH OTHER MODELS.

    groq_reasoning_format: Literal['hidden', 'raw', 'parsed']
    """The format of the reasoning output.

    See [the Groq docs](https://console.groq.com/docs/reasoning#reasoning-format) for more details.
    """
```

#### groq_reasoning_format

```python
groq_reasoning_format: Literal['hidden', 'raw', 'parsed']
```

The format of the reasoning output.

See [the Groq docs](https://console.groq.com/docs/reasoning#reasoning-format) for more details.

### GroqModel

Bases: `Model`

A model that uses the Groq API.

Internally, this uses the [Groq Python client](https://github.com/groq/groq-python) to interact with the API.

Apart from `__init__`, all methods are private or match those of the base class.

Source code in `pydantic_ai_slim/pydantic_ai/models/groq.py`

```python
@dataclass(init=False)
class GroqModel(Model):
    """A model that uses the Groq API.

    Internally, this uses the [Groq Python client](https://github.com/groq/groq-python) to interact with the API.

    Apart from `__init__`, all methods are private or match those of the base class.
    """

    client: AsyncGroq = field(repr=False)

    _model_name: GroqModelName = field(repr=False)
    _provider: Provider[AsyncGroq] = field(repr=False)

    def __init__(
        self,
        model_name: GroqModelName,
        *,
        provider: Literal['groq', 'gateway'] | Provider[AsyncGroq] = 'groq',
        profile: ModelProfileSpec | None = None,
        settings: ModelSettings | None = None,
    ):
        """Initialize a Groq model.

        Args:
            model_name: The name of the Groq model to use. List of model names available
                [here](https://console.groq.com/docs/models).
            provider: The provider to use for authentication and API access. Can be either the string
                'groq' or an instance of `Provider[AsyncGroq]`. If not provided, a new provider will be
                created using the other parameters.
            profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
            settings: Model-specific settings that will be used as defaults for this model.
        """
        self._model_name = model_name

        if isinstance(provider, str):
            provider = infer_provider('gateway/groq' if provider == 'gateway' else provider)
        self._provider = provider
        self.client = provider.client

        super().__init__(settings=settings, profile=profile or provider.model_profile)

    @property
    def base_url(self) -> str:
        return str(self.client.base_url)

    @property
    def model_name(self) -> GroqModelName:
        """The model name."""
        return self._model_name

    @property
    def system(self) -> str:
        """The model provider."""
        return self._provider.name

    @classmethod
    def supported_builtin_tools(cls) -> frozenset[type[AbstractBuiltinTool]]:
        """Return the set of builtin tool types this model can handle."""
        return frozenset({WebSearchTool})

    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        check_allow_model_requests()
        model_settings, model_request_parameters = self.prepare_request(
            model_settings,
            model_request_parameters,
        )
        try:
            response = await self._completions_create(
                messages, False, cast(GroqModelSettings, model_settings or {}), model_request_parameters
            )
        except ModelHTTPError as e:
            # The Groq SDK tries to be helpful by raising an exception when generated tool arguments don't match the schema,
            # but we'd rather handle it ourselves so we can tell the model to retry the tool call.
            if (failed_generation := _parse_tool_use_failed_error(e.body)) is not None:
                if isinstance(failed_generation, _GroqToolUseFailedGeneration):
                    part = ToolCallPart(
                        tool_name=failed_generation.name,
                        args=failed_generation.arguments,
                    )
                elif failed_generation:
                    part = TextPart(content=failed_generation)
                else:  # pragma: no cover
                    part = None

                return ModelResponse(
                    parts=[part] if part else [],
                    model_name=e.model_name,
                    provider_name=self._provider.name,
                    provider_url=self.base_url,
                    finish_reason='error',
                )
            raise
        model_response = self._process_response(response)
        return model_response

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        check_allow_model_requests()
        model_settings, model_request_parameters = self.prepare_request(
            model_settings,
            model_request_parameters,
        )
        response = await self._completions_create(
            messages, True, cast(GroqModelSettings, model_settings or {}), model_request_parameters
        )
        async with response:
            yield await self._process_streamed_response(response, model_request_parameters)

    def _get_reasoning_format(
        self,
        model_settings: GroqModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> Literal['hidden', 'raw', 'parsed'] | NotGiven:
        """Get reasoning format, falling back to unified thinking when provider-specific setting is not set."""
        if fmt := model_settings.get('groq_reasoning_format'):
            return fmt
        thinking = model_request_parameters.thinking
        if thinking is False:
            # Groq has no true disable; 'hidden' suppresses reasoning output
            return 'hidden'
        if thinking is not None:
            return 'parsed'
        return NOT_GIVEN

    @overload
    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: Literal[True],
        model_settings: GroqModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> AsyncStream[chat.ChatCompletionChunk]:
        pass

    @overload
    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: Literal[False],
        model_settings: GroqModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> chat.ChatCompletion:
        pass

    async def _completions_create(
        self,
        messages: list[ModelMessage],
        stream: bool,
        model_settings: GroqModelSettings,
        model_request_parameters: ModelRequestParameters,
    ) -> chat.ChatCompletion | AsyncStream[chat.ChatCompletionChunk]:
        tools = self._get_tools(model_request_parameters)
        tools += self._get_builtin_tools(model_request_parameters)
        if not tools:
            tool_choice: Literal['none', 'required', 'auto'] | None = None
        elif not model_request_parameters.allow_text_output:
            tool_choice = 'required'
        else:
            tool_choice = 'auto'

        groq_messages = await self._map_messages(messages, model_request_parameters)

        response_format: chat.completion_create_params.ResponseFormat | None = None
        if model_request_parameters.output_mode == 'native':
            output_object = model_request_parameters.output_object
            assert output_object is not None
            response_format = self._map_json_schema(output_object)
        elif (
            model_request_parameters.output_mode == 'prompted'
            and not tools
            and self.profile.supports_json_object_output
        ):  # pragma: no branch
            response_format = {'type': 'json_object'}

        try:
            extra_headers = model_settings.get('extra_headers', {})
            extra_headers.setdefault('User-Agent', get_user_agent())
            return await self.client.chat.completions.create(
                model=self._model_name,
                messages=groq_messages,
                n=1,
                parallel_tool_calls=model_settings.get('parallel_tool_calls', NOT_GIVEN),
                tools=tools or NOT_GIVEN,
                tool_choice=tool_choice or NOT_GIVEN,
                stop=model_settings.get('stop_sequences', NOT_GIVEN),
                stream=stream,
                response_format=response_format or NOT_GIVEN,
                max_tokens=model_settings.get('max_tokens', NOT_GIVEN),
                temperature=model_settings.get('temperature', NOT_GIVEN),
                top_p=model_settings.get('top_p', NOT_GIVEN),
                timeout=model_settings.get('timeout', NOT_GIVEN),
                seed=model_settings.get('seed', NOT_GIVEN),
                presence_penalty=model_settings.get('presence_penalty', NOT_GIVEN),
                reasoning_format=self._get_reasoning_format(model_settings, model_request_parameters),
                frequency_penalty=model_settings.get('frequency_penalty', NOT_GIVEN),
                logit_bias=model_settings.get('logit_bias', NOT_GIVEN),
                extra_headers=extra_headers,
                extra_body=model_settings.get('extra_body'),
            )
        except APIStatusError as e:
            if (status_code := e.status_code) >= 400:
                raise ModelHTTPError(status_code=status_code, model_name=self.model_name, body=e.body) from e
            raise ModelAPIError(model_name=self.model_name, message=e.message) from e  # pragma: no cover
        except APIConnectionError as e:
            raise ModelAPIError(model_name=self.model_name, message=e.message) from e

    def _process_response(self, response: chat.ChatCompletion) -> ModelResponse:
        """Process a non-streamed response, and prepare a message to return."""
        choice = response.choices[0]
        items: list[ModelResponsePart] = []
        if choice.message.reasoning is not None:
            # NOTE: The `reasoning` field is only present if `groq_reasoning_format` is set to `parsed`.
            items.append(ThinkingPart(content=choice.message.reasoning))
        if choice.message.executed_tools:
            for tool in choice.message.executed_tools:
                call_part, return_part = _map_executed_tool(tool, self.system)
                if call_part and return_part:  # pragma: no branch
                    items.append(call_part)
                    items.append(return_part)
        if choice.message.content:
            # NOTE: The `<think>` tag is only present if `groq_reasoning_format` is set to `raw`.
            items.extend(split_content_into_text_and_thinking(choice.message.content, self.profile.thinking_tags))
        if choice.message.tool_calls is not None:
            for c in choice.message.tool_calls:
                items.append(ToolCallPart(tool_name=c.function.name, args=c.function.arguments, tool_call_id=c.id))

        raw_finish_reason = choice.finish_reason
        provider_details: dict[str, Any] = {'finish_reason': raw_finish_reason}
        if response.created:  # pragma: no branch
            provider_details['timestamp'] = number_to_datetime(response.created)
        finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason)
        return ModelResponse(
            parts=items,
            usage=_map_usage(response),
            model_name=response.model,
            provider_response_id=response.id,
            provider_name=self._provider.name,
            provider_url=self.base_url,
            finish_reason=finish_reason,
            provider_details=provider_details,
        )

    async def _process_streamed_response(
        self, response: AsyncStream[chat.ChatCompletionChunk], model_request_parameters: ModelRequestParameters
    ) -> GroqStreamedResponse:
        """Process a streamed response, and prepare a streaming response to return."""
        peekable_response = _utils.PeekableAsyncStream(response)
        first_chunk = await peekable_response.peek()
        if isinstance(first_chunk, _utils.Unset):
            raise UnexpectedModelBehavior(  # pragma: no cover
                'Streamed response ended without content or tool calls'
            )

        return GroqStreamedResponse(
            model_request_parameters=model_request_parameters,
            _response=peekable_response,
            _model_name=first_chunk.model,
            _model_profile=self.profile,
            _provider_name=self._provider.name,
            _provider_url=self.base_url,
            _provider_timestamp=number_to_datetime(first_chunk.created),
        )

    def _get_tools(self, model_request_parameters: ModelRequestParameters) -> list[chat.ChatCompletionToolParam]:
        return [self._map_tool_definition(r) for r in model_request_parameters.tool_defs.values()]

    def _get_builtin_tools(
        self, model_request_parameters: ModelRequestParameters
    ) -> list[chat.ChatCompletionToolParam]:
        tools: list[chat.ChatCompletionToolParam] = []
        for tool in model_request_parameters.builtin_tools:
            if isinstance(tool, WebSearchTool):
                if not GroqModelProfile.from_profile(self.profile).groq_always_has_web_search_builtin_tool:
                    raise UserError('`WebSearchTool` is not supported by Groq')  # pragma: no cover
            else:  # pragma: no cover
                raise UserError(
                    f'`{tool.__class__.__name__}` is not supported by `GroqModel`. If it should be, please file an issue.'
                )
        return tools

    async def _map_messages(
        self, messages: list[ModelMessage], model_request_parameters: ModelRequestParameters
    ) -> list[chat.ChatCompletionMessageParam]:
        """Just maps a `pydantic_ai.Message` to a `groq.types.ChatCompletionMessageParam`."""
        groq_messages: list[chat.ChatCompletionMessageParam] = []
        for message in messages:
            if isinstance(message, ModelRequest):
                async for item in self._map_user_message(message):
                    groq_messages.append(item)
            elif isinstance(message, ModelResponse):
                texts: list[str] = []
                tool_calls: list[chat.ChatCompletionMessageToolCallParam] = []
                for item in message.parts:
                    if isinstance(item, TextPart):
                        texts.append(item.content)
                    elif isinstance(item, ToolCallPart):
                        tool_calls.append(self._map_tool_call(item))
                    elif isinstance(item, ThinkingPart):
                        start_tag, end_tag = self.profile.thinking_tags
                        texts.append('\n'.join([start_tag, item.content, end_tag]))
                    elif isinstance(item, BuiltinToolCallPart | BuiltinToolReturnPart):  # pragma: no cover
                        # These are not currently sent back
                        pass
                    elif isinstance(item, FilePart):  # pragma: no cover
                        # Files generated by models are not sent back to models that don't themselves generate files.
                        pass
                    else:
                        assert_never(item)
                message_param = chat.ChatCompletionAssistantMessageParam(role='assistant')
                if texts:
                    # Note: model responses from this model should only have one text item, so the following
                    # shouldn't merge multiple texts into one unless you switch models between runs:
                    message_param['content'] = '\n\n'.join(texts)
                if tool_calls:
                    message_param['tool_calls'] = tool_calls
                groq_messages.append(message_param)
            else:
                assert_never(message)
        if instructions := self._get_instructions(messages, model_request_parameters):
            system_prompt_count = sum(1 for m in groq_messages if m.get('role') == 'system')
            groq_messages.insert(
                system_prompt_count, chat.ChatCompletionSystemMessageParam(role='system', content=instructions)
            )
        return groq_messages

    @staticmethod
    def _map_tool_call(t: ToolCallPart) -> chat.ChatCompletionMessageToolCallParam:
        return chat.ChatCompletionMessageToolCallParam(
            id=_guard_tool_call_id(t=t),
            type='function',
            function={'name': t.tool_name, 'arguments': t.args_as_json_str()},
        )

    @staticmethod
    def _map_tool_definition(f: ToolDefinition) -> chat.ChatCompletionToolParam:
        return {
            'type': 'function',
            'function': {
                'name': f.name,
                'description': f.description or '',
                'parameters': f.parameters_json_schema,
            },
        }

    def _map_json_schema(self, o: OutputObjectDefinition) -> chat.completion_create_params.ResponseFormat:
        response_format_param: chat.completion_create_params.ResponseFormatResponseFormatJsonSchema = {
            'type': 'json_schema',
            'json_schema': {
                'name': o.name or DEFAULT_OUTPUT_TOOL_NAME,
                'schema': o.json_schema,
                'strict': o.strict,
            },
        }
        if o.description:  # pragma: no branch
            response_format_param['json_schema']['description'] = o.description
        return response_format_param

    async def _map_user_message(self, message: ModelRequest) -> AsyncIterable[chat.ChatCompletionMessageParam]:
        file_content: list[UserContent] = []
        for part in message.parts:
            if isinstance(part, SystemPromptPart):
                yield chat.ChatCompletionSystemMessageParam(role='system', content=part.content)
            elif isinstance(part, UserPromptPart):
                yield await self._map_user_prompt(part)
            elif isinstance(part, ToolReturnPart):
                tool_text, tool_file_content = part.model_response_str_and_user_content()
                file_content.extend(tool_file_content)
                yield chat.ChatCompletionToolMessageParam(
                    role='tool',
                    tool_call_id=_guard_tool_call_id(t=part),
                    content=tool_text,
                )
            elif isinstance(part, RetryPromptPart):  # pragma: no branch
                if part.tool_name is None:
                    yield chat.ChatCompletionUserMessageParam(role='user', content=part.model_response())
                else:
                    yield chat.ChatCompletionToolMessageParam(
                        role='tool',
                        tool_call_id=_guard_tool_call_id(t=part),
                        content=part.model_response(),
                    )
        if file_content:
            yield await self._map_user_prompt(UserPromptPart(content=file_content))

    async def _map_user_prompt(self, part: UserPromptPart) -> chat.ChatCompletionUserMessageParam:
        content: str | list[chat.ChatCompletionContentPartParam]
        if isinstance(part.content, str):
            content = part.content
        else:
            content = []
            for item in part.content:
                if isinstance(item, str):
                    content.append(chat.ChatCompletionContentPartTextParam(text=item, type='text'))
                elif isinstance(item, ImageUrl):
                    image_url_str = item.url
                    if item.force_download:
                        downloaded = await download_item(item, data_format='base64_uri')
                        image_url_str = downloaded['data']
                    image_url = ImageURL(url=image_url_str)
                    content.append(chat.ChatCompletionContentPartImageParam(image_url=image_url, type='image_url'))
                elif isinstance(item, BinaryContent):
                    if item.is_image:
                        image_url = ImageURL(url=item.data_uri)
                        content.append(chat.ChatCompletionContentPartImageParam(image_url=image_url, type='image_url'))
                    else:
                        raise NotImplementedError('Only images are supported for BinaryContent in Groq user prompts')
                elif isinstance(item, DocumentUrl):
                    raise NotImplementedError('DocumentUrl is not supported in Groq user prompts')
                elif isinstance(item, AudioUrl):
                    raise NotImplementedError('AudioUrl is not supported in Groq user prompts')
                elif isinstance(item, VideoUrl):
                    raise NotImplementedError('VideoUrl is not supported in Groq user prompts')
                elif isinstance(item, UploadedFile):
                    raise NotImplementedError('UploadedFile is not supported in Groq user prompts')
                elif isinstance(item, CachePoint):
                    pass
                else:
                    assert_never(item)

        return chat.ChatCompletionUserMessageParam(role='user', content=content)
```

#### __init__

```python
__init__(
    model_name: GroqModelName,
    *,
    provider: (
        Literal["groq", "gateway"] | Provider[AsyncGroq]
    ) = "groq",
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None
)
```

Initialize a Groq model.

Parameters:

| Name         | Type                         | Description                                                            | Default                                                                                                                                                                                                   |
| ------------ | ---------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model_name` | `GroqModelName`              | The name of the Groq model to use. List of model names available here. | *required*                                                                                                                                                                                                |
| `provider`   | \`Literal['groq', 'gateway'] | Provider[AsyncGroq]\`                                                  | The provider to use for authentication and API access. Can be either the string 'groq' or an instance of Provider[AsyncGroq]. If not provided, a new provider will be created using the other parameters. |
| `profile`    | \`ModelProfileSpec           | None\`                                                                 | The model profile to use. Defaults to a profile picked by the provider based on the model name.                                                                                                           |
| `settings`   | \`ModelSettings              | None\`                                                                 | Model-specific settings that will be used as defaults for this model.                                                                                                                                     |

Source code in `pydantic_ai_slim/pydantic_ai/models/groq.py`

```python
def __init__(
    self,
    model_name: GroqModelName,
    *,
    provider: Literal['groq', 'gateway'] | Provider[AsyncGroq] = 'groq',
    profile: ModelProfileSpec | None = None,
    settings: ModelSettings | None = None,
):
    """Initialize a Groq model.

    Args:
        model_name: The name of the Groq model to use. List of model names available
            [here](https://console.groq.com/docs/models).
        provider: The provider to use for authentication and API access. Can be either the string
            'groq' or an instance of `Provider[AsyncGroq]`. If not provided, a new provider will be
            created using the other parameters.
        profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
        settings: Model-specific settings that will be used as defaults for this model.
    """
    self._model_name = model_name

    if isinstance(provider, str):
        provider = infer_provider('gateway/groq' if provider == 'gateway' else provider)
    self._provider = provider
    self.client = provider.client

    super().__init__(settings=settings, profile=profile or provider.model_profile)
```

#### model_name

```python
model_name: GroqModelName
```

The model name.

#### system

```python
system: str
```

The model provider.

#### supported_builtin_tools

```python
supported_builtin_tools() -> (
    frozenset[type[AbstractBuiltinTool]]
)
```

Return the set of builtin tool types this model can handle.

Source code in `pydantic_ai_slim/pydantic_ai/models/groq.py`

```python
@classmethod
def supported_builtin_tools(cls) -> frozenset[type[AbstractBuiltinTool]]:
    """Return the set of builtin tool types this model can handle."""
    return frozenset({WebSearchTool})
```

### GroqStreamedResponse

Bases: `StreamedResponse`

Implementation of `StreamedResponse` for Groq models.

Source code in `pydantic_ai_slim/pydantic_ai/models/groq.py`

```python
@dataclass
class GroqStreamedResponse(StreamedResponse):
    """Implementation of `StreamedResponse` for Groq models."""

    _model_name: GroqModelName
    _model_profile: ModelProfile
    _response: AsyncIterable[chat.ChatCompletionChunk]
    _provider_name: str
    _provider_url: str
    _provider_timestamp: datetime | None = None
    _timestamp: datetime = field(default_factory=_utils.now_utc)

    async def _get_event_iterator(self) -> AsyncIterator[ModelResponseStreamEvent]:  # noqa: C901
        try:
            executed_tool_call_id: str | None = None
            reasoning_index = 0
            reasoning = False
            if self._provider_timestamp is not None:  # pragma: no branch
                self.provider_details = {'timestamp': self._provider_timestamp}
            async for chunk in self._response:
                self._usage += _map_usage(chunk)

                if chunk.id:  # pragma: no branch
                    self.provider_response_id = chunk.id

                try:
                    choice = chunk.choices[0]
                except IndexError:
                    continue

                if raw_finish_reason := choice.finish_reason:
                    self.provider_details = {**(self.provider_details or {}), 'finish_reason': raw_finish_reason}
                    self.finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason)

                if choice.delta.reasoning is not None:
                    if not reasoning:
                        reasoning_index += 1
                        reasoning = True

                    # NOTE: The `reasoning` field is only present if `groq_reasoning_format` is set to `parsed`.
                    for event in self._parts_manager.handle_thinking_delta(
                        vendor_part_id=f'reasoning-{reasoning_index}', content=choice.delta.reasoning
                    ):
                        yield event
                else:
                    reasoning = False

                if choice.delta.executed_tools:
                    for tool in choice.delta.executed_tools:
                        call_part, return_part = _map_executed_tool(
                            tool, self.provider_name, streaming=True, tool_call_id=executed_tool_call_id
                        )
                        if call_part:
                            executed_tool_call_id = call_part.tool_call_id
                            yield self._parts_manager.handle_part(
                                vendor_part_id=f'executed_tools-{tool.index}-call', part=call_part
                            )
                        if return_part:
                            executed_tool_call_id = None
                            yield self._parts_manager.handle_part(
                                vendor_part_id=f'executed_tools-{tool.index}-return', part=return_part
                            )

                # Handle the text part of the response
                content = choice.delta.content
                if content:
                    for event in self._parts_manager.handle_text_delta(
                        vendor_part_id='content',
                        content=content,
                        thinking_tags=self._model_profile.thinking_tags,
                        ignore_leading_whitespace=self._model_profile.ignore_streamed_leading_whitespace,
                    ):
                        yield event

                # Handle the tool calls
                for dtc in choice.delta.tool_calls or []:
                    maybe_event = self._parts_manager.handle_tool_call_delta(
                        vendor_part_id=dtc.index,
                        tool_name=dtc.function and dtc.function.name,
                        args=dtc.function and dtc.function.arguments,
                        tool_call_id=dtc.id,
                    )
                    if maybe_event is not None:
                        yield maybe_event
        except APIError as e:
            # The Groq SDK tries to be helpful by raising an exception when generated tool arguments don't match the schema,
            # but we'd rather handle it ourselves so we can tell the model to retry the tool call
            if (failed_generation := _parse_tool_use_failed_error(e.body)) is not None:
                if isinstance(failed_generation, _GroqToolUseFailedGeneration):
                    yield self._parts_manager.handle_tool_call_part(
                        vendor_part_id='tool_use_failed',
                        tool_name=failed_generation.name,
                        args=failed_generation.arguments,
                    )
                elif failed_generation:  # pragma: no cover
                    # This branch is not covered because when streaming, the non-tool call text would already
                    # have streamed before the `tool_use_failed` error which comes with `failed_generation=''`,
                    # but we keep this here for (hypothetical?) cases where that field would not be empty.
                    for event in self._parts_manager.handle_text_delta(
                        vendor_part_id='tool_use_failed',
                        content=failed_generation,
                        thinking_tags=self._model_profile.thinking_tags,
                        ignore_leading_whitespace=self._model_profile.ignore_streamed_leading_whitespace,
                    ):
                        yield event
                return
            raise  # pragma: no cover

    @property
    def model_name(self) -> GroqModelName:
        """Get the model name of the response."""
        return self._model_name

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self._provider_name

    @property
    def provider_url(self) -> str:
        """Get the provider base URL."""
        return self._provider_url

    @property
    def timestamp(self) -> datetime:
        """Get the timestamp of the response."""
        return self._timestamp
```

#### model_name

```python
model_name: GroqModelName
```

Get the model name of the response.

#### provider_name

```python
provider_name: str
```

Get the provider name.

#### provider_url

```python
provider_url: str
```

Get the provider base URL.

#### timestamp

```python
timestamp: datetime
```

Get the timestamp of the response.
