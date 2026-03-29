# Image, Audio, Video & Document Input

Some LLMs are now capable of understanding audio, video, image and document content.

## Image Input

Info

Some models do not support image input. Please check the model's documentation to confirm whether it supports image input.

If you have a direct URL for the image, you can use ImageUrl:

[Learn about Gateway](https://ai.pydantic.dev/gateway) image_input.py

```python
from pydantic_ai import Agent, ImageUrl

agent = Agent(model='gateway/openai:gpt-5.2')
result = agent.run_sync(
    [
        'What company is this logo from?',
        ImageUrl(url='https://iili.io/3Hs4FMg.png'),
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.
```

image_input.py

```python
from pydantic_ai import Agent, ImageUrl

agent = Agent(model='openai:gpt-5.2')
result = agent.run_sync(
    [
        'What company is this logo from?',
        ImageUrl(url='https://iili.io/3Hs4FMg.png'),
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.
```

If you have the image locally, you can also use BinaryContent:

[Learn about Gateway](https://ai.pydantic.dev/gateway) local_image_input.py

```python
import httpx

from pydantic_ai import Agent, BinaryContent

image_response = httpx.get('https://iili.io/3Hs4FMg.png')  # Pydantic logo

agent = Agent(model='gateway/openai:gpt-5.2')
result = agent.run_sync(
    [
        'What company is this logo from?',
        BinaryContent(data=image_response.content, media_type='image/png'),  # (1)!
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.
```

1. To ensure the example is runnable we download this image from the web, but you can also use `Path().read_bytes()` to read a local file's contents.

local_image_input.py

```python
import httpx

from pydantic_ai import Agent, BinaryContent

image_response = httpx.get('https://iili.io/3Hs4FMg.png')  # Pydantic logo

agent = Agent(model='openai:gpt-5.2')
result = agent.run_sync(
    [
        'What company is this logo from?',
        BinaryContent(data=image_response.content, media_type='image/png'),  # (1)!
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.
```

1. To ensure the example is runnable we download this image from the web, but you can also use `Path().read_bytes()` to read a local file's contents.

## Audio Input

Info

Some models do not support audio input. Please check the model's documentation to confirm whether it supports audio input.

You can provide audio input using either AudioUrl or BinaryContent. The process is analogous to the examples above.

## Video Input

Info

Some models do not support video input. Please check the model's documentation to confirm whether it supports video input.

You can provide video input using either VideoUrl or BinaryContent. The process is analogous to the examples above.

## Document Input

Info

Some models do not support document input. Please check the model's documentation to confirm whether it supports document input.

You can provide document input using either DocumentUrl or BinaryContent. The process is similar to the examples above.

If you have a direct URL for the document, you can use DocumentUrl:

[Learn about Gateway](https://ai.pydantic.dev/gateway) document_input.py

```python
from pydantic_ai import Agent, DocumentUrl

agent = Agent(model='gateway/anthropic:claude-sonnet-4-6')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        DocumentUrl(url='https://storage.googleapis.com/cloud-samples-data/generative-ai/pdf/2403.05530.pdf'),
    ]
)
print(result.output)
#> This document is the technical report introducing Gemini 1.5, Google's latest large language model...
```

document_input.py

```python
from pydantic_ai import Agent, DocumentUrl

agent = Agent(model='anthropic:claude-sonnet-4-6')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        DocumentUrl(url='https://storage.googleapis.com/cloud-samples-data/generative-ai/pdf/2403.05530.pdf'),
    ]
)
print(result.output)
#> This document is the technical report introducing Gemini 1.5, Google's latest large language model...
```

The supported document formats vary by model.

You can also use BinaryContent to pass document data directly:

[Learn about Gateway](https://ai.pydantic.dev/gateway) binary_content_input.py

```python
from pathlib import Path
from pydantic_ai import Agent, BinaryContent

pdf_path = Path('document.pdf')
agent = Agent(model='gateway/anthropic:claude-sonnet-4-6')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        BinaryContent(data=pdf_path.read_bytes(), media_type='application/pdf'),
    ]
)
print(result.output)
#> The document discusses...
```

binary_content_input.py

```python
from pathlib import Path
from pydantic_ai import Agent, BinaryContent

pdf_path = Path('document.pdf')
agent = Agent(model='anthropic:claude-sonnet-4-6')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        BinaryContent(data=pdf_path.read_bytes(), media_type='application/pdf'),
    ]
)
print(result.output)
#> The document discusses...
```

## User-side download vs. direct file URL

When using one of `ImageUrl`, `AudioUrl`, `VideoUrl` or `DocumentUrl`, Pydantic AI will default to sending the URL to the model provider, so the file is downloaded on their side.

Support for file URLs varies depending on type and provider:

| Model                | Send URL directly                                                                                                                                                                | Download and send bytes               | Unsupported                                     |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | ----------------------------------------------- |
| OpenAIChatModel      | `ImageUrl`                                                                                                                                                                       | `AudioUrl`, `DocumentUrl`             | `VideoUrl`                                      |
| OpenAIResponsesModel | `ImageUrl`, `AudioUrl`, `DocumentUrl`                                                                                                                                            | —                                     | `VideoUrl`                                      |
| AnthropicModel       | `ImageUrl`, `DocumentUrl` (PDF)                                                                                                                                                  | `DocumentUrl` (`text/plain`)          | `AudioUrl`, `VideoUrl`                          |
| GoogleModel (Vertex) | All URL types                                                                                                                                                                    | —                                     | —                                               |
| GoogleModel (GLA)    | [YouTube](https://ai.pydantic.dev/models/google/#document-image-audio-and-video-input), [Files API](https://ai.pydantic.dev/models/google/#document-image-audio-and-video-input) | All other URLs                        | —                                               |
| XaiModel             | `ImageUrl`                                                                                                                                                                       | `DocumentUrl`                         | `AudioUrl`, `VideoUrl`                          |
| MistralModel         | `ImageUrl`, `DocumentUrl` (PDF)                                                                                                                                                  | —                                     | `AudioUrl`, `VideoUrl`, `DocumentUrl` (non-PDF) |
| BedrockConverseModel | S3 URLs (`s3://`)                                                                                                                                                                | `ImageUrl`, `DocumentUrl`, `VideoUrl` | `AudioUrl`                                      |
| OpenRouterModel      | `ImageUrl`, `DocumentUrl`, `VideoUrl`                                                                                                                                            | `AudioUrl`                            | —                                               |

A model API may be unable to download a file (e.g., because of crawling or access restrictions) even if it supports file URLs. For example, GoogleModel on Vertex AI limits YouTube video URLs to one URL per request. In such cases, you can instruct Pydantic AI to download the file content locally and send that instead of the URL by setting `force_download` on the URL object:

force_download.py

```python
from pydantic_ai import ImageUrl, AudioUrl, VideoUrl, DocumentUrl

ImageUrl(url='https://example.com/image.png', force_download=True)
AudioUrl(url='https://example.com/audio.mp3', force_download=True)
VideoUrl(url='https://example.com/video.mp4', force_download=True)
DocumentUrl(url='https://example.com/doc.pdf', force_download=True)
```

## Uploaded Files

Some model providers have their own file storage APIs where you can upload files and reference them by ID or URL.

Use UploadedFile to reference files that have been uploaded to a provider's file storage API.

Tip

For providers that return a file URL (like Google Files API or S3 URLs for Bedrock), you can also use DocumentUrl, ImageUrl, or VideoUrl directly. However, we recommend using `UploadedFile` for a unified API across providers and consistent provider name validation.

### Supported Models

| Model                | Support                                                                                  |
| -------------------- | ---------------------------------------------------------------------------------------- |
| AnthropicModel       | ✅ via [Anthropic Files API](https://docs.anthropic.com/en/docs/build-with-claude/files) |
| OpenAIChatModel      | ✅ via [OpenAI Files API](https://platform.openai.com/docs/api-reference/files)          |
| OpenAIResponsesModel | ✅ via [OpenAI Files API](https://platform.openai.com/docs/api-reference/files)          |
| GoogleModel          | ✅ via [Google Files API](https://ai.google.dev/gemini-api/docs/files)                   |
| BedrockConverseModel | ✅ via S3 URLs (`s3://bucket/key`)                                                       |
| XaiModel             | ✅ via [xAI Files API](https://docs.x.ai/docs/guides/files)                              |
| Other models         | ❌ Not supported                                                                         |

### Provider Name Requirement

When using UploadedFile you must set the `provider_name`. Uploaded files are specific to the system they are uploaded to and are not transferable across providers. Trying to use a message that contains an `UploadedFile` with a different provider will result in an error.

Getting the provider name

Use model.system to get the correct provider name dynamically. This ensures your code works correctly even if the provider name changes. All examples below demonstrate this pattern.

If you want to introduce portability into your agent logic to allow the same prompt history to work with different provider backends, you can use a [history processor](https://ai.pydantic.dev/message-history/#processing-message-history) to remove or rewrite `UploadedFile` parts from messages before sending them to a provider that does not support them. Be aware that stripping out `UploadedFile` instances might confuse the model, especially if references to those files remain in the text.

### Media Type Inference

The `media_type` parameter is optional for UploadedFile. If not specified, Pydantic AI will attempt to infer it from the `file_id`:

1. If `file_id` is a URL or path with a recognizable file extension (e.g., `.pdf`, `.png`), the media type is inferred automatically
1. For opaque file IDs (e.g., `'file-abc123'`), the media type defaults to `'application/octet-stream'`

Tip

While `media_type` is optional, we recommend explicitly setting it when known to ensure correct handling by the model provider.

### Anthropic

Follow the [Anthropic Files API docs](https://docs.anthropic.com/en/docs/build-with-claude/files) to upload files. You can access the underlying Anthropic client via `provider.client`.

Beta Feature

The Anthropic Files API is currently in beta. You need to include the beta header `anthropic-beta: files-api-2025-04-14` when making requests.

uploaded_file_anthropic.py

```python
import asyncio

from pydantic_ai import Agent, ModelSettings, UploadedFile
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider


async def main():
    provider = AnthropicProvider()
    model = AnthropicModel('claude-sonnet-4-5', provider=provider)

    # Upload a file using the provider's client (Anthropic client)
    with open('document.pdf', 'rb') as f:
        uploaded_file = await provider.client.beta.files.upload(file=f)

    # Reference the uploaded file, including the required beta header
    agent = Agent(model)
    result = await agent.run(
        [
            'Summarize this document',
            UploadedFile(file_id=uploaded_file.id, provider_name=model.system),
        ],
        model_settings=ModelSettings(extra_headers={'anthropic-beta': 'files-api-2025-04-14'}),
    )
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```

### OpenAI

Follow the [OpenAI Files API docs](https://platform.openai.com/docs/api-reference/files/create) to upload files. You can access the underlying OpenAI client via `provider.client`.

uploaded_file_openai.py

```python
import asyncio

from pydantic_ai import Agent, UploadedFile
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider


async def main():
    provider = OpenAIProvider()
    model = OpenAIChatModel('gpt-5', provider=provider)

    # Upload a file using the provider's client (OpenAI client)
    with open('document.pdf', 'rb') as f:
        uploaded_file = await provider.client.files.create(file=f, purpose='user_data')

    # Reference the uploaded file
    agent = Agent(model)
    result = await agent.run(
        [
            'Summarize this document',
            UploadedFile(file_id=uploaded_file.id, provider_name=model.system),
        ]
    )
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```

### Google

Follow the [Google Files API docs](https://ai.google.dev/gemini-api/docs/files) to upload files. You can access the underlying Google GenAI client via `provider.client`.

uploaded_file_google.py

```python
import asyncio

from pydantic_ai import Agent, UploadedFile
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider


async def main():
    provider = GoogleProvider()
    model = GoogleModel('gemini-2.5-flash', provider=provider)

    # Upload a file using the provider's client (Google GenAI client)
    with open('document.pdf', 'rb') as f:
        file = await provider.client.aio.files.upload(file=f)
        assert file.uri is not None

    # Reference the uploaded file by URI (media_type is optional for Google)
    agent = Agent(model)
    result = await agent.run(
        [
            'Summarize this document',
            UploadedFile(file_id=file.uri, media_type=file.mime_type, provider_name=model.system),
        ]
    )
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```

### Bedrock (S3)

For Bedrock, files must be uploaded to S3 separately (e.g., using [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html)). The assumed role must have `s3:GetObject` permission on the bucket.

`media_type` may be required

Bedrock requires `media_type` when the file extension is ambiguous or missing. For S3 URLs with clear extensions like `.pdf`, `.png`, etc., it can be inferred automatically.

uploaded_file_bedrock.py

```python
import asyncio

from pydantic_ai import Agent, UploadedFile
from pydantic_ai.models.bedrock import BedrockConverseModel


async def main():
    model = BedrockConverseModel('us.anthropic.claude-sonnet-4-20250514-v1:0')

    agent = Agent(model)
    result = await agent.run([
        'Summarize this document',
        UploadedFile(
            file_id='s3://my-bucket/document.pdf',
            provider_name=model.system,  # 'bedrock'
            media_type='application/pdf',  # Optional for .pdf, but recommended
        ),
    ])
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```

Note

You can optionally specify a `bucketOwner` query parameter if the bucket is not owned by the account making the request: `s3://my-bucket/document.pdf?bucketOwner=123456789012`

### xAI

Follow the [xAI Files API docs](https://docs.x.ai/docs/guides/files) to upload files. You can access the underlying xAI client via `provider.client`.

uploaded_file_xai.py

```python
import asyncio

from pydantic_ai import Agent, UploadedFile
from pydantic_ai.models.xai import XaiModel
from pydantic_ai.providers.xai import XaiProvider


async def main():
    provider = XaiProvider()
    model = XaiModel('grok-4-fast', provider=provider)

    # Upload a file using the provider's client (xAI client)
    with open('document.pdf', 'rb') as f:
        uploaded_file = await provider.client.files.upload(f, filename='document.pdf')

    # Reference the uploaded file
    agent = Agent(model)
    result = await agent.run(
        [
            'Summarize this document',
            UploadedFile(file_id=uploaded_file.id, provider_name=model.system),
        ]
    )
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```
