# Lesson 7: Streaming Responses

## Overview

Streaming allows your agent to return responses progressively, improving user experience for long responses. In this lesson, you'll learn:
- How to stream agent responses
- Streaming with structured outputs
- Displaying partial results
- Handling streaming errors
- Best practices for streaming

## Why Streaming?

Benefits of streaming responses:
- **Better UX**: Users see responses as they're generated
- **Perceived performance**: Feels faster even if total time is the same
- **Early feedback**: Users can interrupt if response is wrong
- **Resource efficiency**: Can process results before completion

## Basic Streaming

### Streaming Text Responses

Use `run_stream()` for streaming (async only):

```python
import asyncio
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')

async def stream_example():
    """Stream a text response."""
    async with agent.run_stream('Write a short story about a robot.') as result:
        async for chunk in result.stream_text():
            print(chunk, end='', flush=True)
        
        # Get the final complete result
        final_result = await result.get_data()
        print(f"\n\nFinal result: {final_result}")

asyncio.run(stream_example())
```

### Streaming with Message History

```python
import asyncio
from pydantic_ai import Agent

async def streaming_chat():
    """A streaming chatbot."""
    agent = Agent('openai:gpt-4')
    message_history = []
    
    print("Chat started! Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            break
        
        print("Bot: ", end='', flush=True)
        
        async with agent.run_stream(
            user_input,
            message_history=message_history
        ) as result:
            # Stream the response
            async for chunk in result.stream_text():
                print(chunk, end='', flush=True)
            
            print()  # New line after response
            
            # Update message history
            message_history = result.all_messages()

asyncio.run(streaming_chat())
```

## Streaming Structured Data

### Streaming with Validated Results

Stream while still getting validated Pydantic models:

```python
import asyncio
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List

class MovieRecommendation(BaseModel):
    title: str
    year: int
    genre: str
    rating: float
    reason: str

agent = Agent(
    'openai:gpt-4',
    result_type=MovieRecommendation
)

async def stream_structured():
    """Stream a structured response."""
    async with agent.run_stream(
        'Recommend a sci-fi movie from the 1980s'
    ) as result:
        # Stream text as it comes
        print("Streaming response:")
        async for chunk in result.stream_text():
            print(chunk, end='', flush=True)
        
        print("\n\n" + "="*50)
        
        # Get the validated structured result
        final_data = await result.get_data()
        
        print("\nValidated Result:")
        print(f"Title: {final_data.title}")
        print(f"Year: {final_data.year}")
        print(f"Genre: {final_data.genre}")
        print(f"Rating: {final_data.rating}/10")
        print(f"Reason: {final_data.reason}")

asyncio.run(stream_structured())
```

### Streaming Lists

```python
import asyncio
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List

class Task(BaseModel):
    title: str
    description: str
    priority: str

agent = Agent(
    'openai:gpt-4',
    result_type=List[Task]
)

async def stream_list():
    """Stream a list of structured items."""
    async with agent.run_stream(
        'Give me 5 tasks for planning a wedding'
    ) as result:
        print("Generating tasks...\n")
        
        # Stream text representation
        async for chunk in result.stream_text():
            print(chunk, end='', flush=True)
        
        # Get validated structured list
        tasks = await result.get_data()
        
        print("\n\n" + "="*50)
        print("Structured Tasks:")
        for i, task in enumerate(tasks, 1):
            print(f"\n{i}. {task.title}")
            print(f"   Description: {task.description}")
            print(f"   Priority: {task.priority}")

asyncio.run(stream_list())
```

## Streaming with Dependencies

```python
import asyncio
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass

@dataclass
class UserContext:
    user_id: str
    preferences: dict

agent = Agent(
    'openai:gpt-4',
    deps_type=UserContext
)

@agent.system_prompt
def get_prompt(ctx: RunContext[UserContext]) -> str:
    prefs = ctx.deps.preferences
    return f"You are a personalized assistant. User preferences: {prefs}"

async def stream_with_deps():
    """Stream with dependency injection."""
    user = UserContext(
        user_id='user_123',
        preferences={'tone': 'friendly', 'style': 'concise'}
    )
    
    async with agent.run_stream(
        'Tell me about Python',
        deps=user
    ) as result:
        async for chunk in result.stream_text():
            print(chunk, end='', flush=True)
        
        print()

asyncio.run(stream_with_deps())
```

## Advanced Streaming Patterns

### Progress Indicators

Show progress while streaming:

```python
import asyncio
from pydantic_ai import Agent

async def stream_with_progress():
    """Stream with a progress indicator."""
    agent = Agent('openai:gpt-4')
    
    print("Generating response", end='', flush=True)
    
    async with agent.run_stream(
        'Explain quantum computing in detail'
    ) as result:
        char_count = 0
        
        async for chunk in result.stream_text():
            print(chunk, end='', flush=True)
            char_count += len(chunk)
            
            # Show progress every 100 characters
            if char_count % 100 == 0:
                print(f"\n[{char_count} chars]", end='', flush=True)
        
        print(f"\n\nTotal characters: {char_count}")

asyncio.run(stream_with_progress())
```

### Buffered Streaming

Buffer chunks for smoother display:

```python
import asyncio
from pydantic_ai import Agent
from collections import deque

async def buffered_stream():
    """Stream with buffering for smoother output."""
    agent = Agent('openai:gpt-4')
    
    async with agent.run_stream(
        'Write a paragraph about artificial intelligence'
    ) as result:
        buffer = deque(maxlen=5)  # Buffer up to 5 chunks
        
        async for chunk in result.stream_text():
            buffer.append(chunk)
            
            # Display buffered content smoothly
            if len(buffer) >= 3:
                print(buffer.popleft(), end='', flush=True)
                await asyncio.sleep(0.05)  # Smooth display
        
        # Flush remaining buffer
        while buffer:
            print(buffer.popleft(), end='', flush=True)
        
        print()

asyncio.run(buffered_stream())
```

### Streaming with Tool Calls

Monitor tool calls during streaming:

```python
import asyncio
from pydantic_ai import Agent, RunContext

agent = Agent('openai:gpt-4')

@agent.tool
async def search_database(query: str) -> dict:
    """Search the database."""
    print(f"\n[Searching database for: {query}]")
    await asyncio.sleep(1)  # Simulate search
    return {'results': ['Item 1', 'Item 2']}

@agent.tool
async def calculate(expression: str) -> float:
    """Evaluate a math expression."""
    print(f"\n[Calculating: {expression}]")
    return eval(expression)

async def stream_with_tools():
    """Stream responses with tool calls."""
    print("Query: What is 25 * 4 + 10?\n")
    print("Response: ", end='', flush=True)
    
    async with agent.run_stream(
        'What is 25 * 4 + 10?'
    ) as result:
        async for chunk in result.stream_text():
            print(chunk, end='', flush=True)
        
        print()

asyncio.run(stream_with_tools())
```

## Real-World Example: Code Generator

```python
import asyncio
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List

class CodeSnippet(BaseModel):
    language: str
    code: str
    explanation: str
    dependencies: List[str]

agent = Agent(
    'openai:gpt-4',
    result_type=CodeSnippet,
    system_prompt='You are a helpful coding assistant that generates clean code.'
)

async def generate_code_streaming():
    """Generate code with streaming feedback."""
    prompt = 'Create a Python function to fetch data from a REST API'
    
    print("="*60)
    print("CODE GENERATION")
    print("="*60)
    print(f"\nRequest: {prompt}\n")
    print("Generating...\n")
    
    async with agent.run_stream(prompt) as result:
        # Show streaming text
        async for chunk in result.stream_text():
            print(chunk, end='', flush=True)
        
        # Get structured result
        code_snippet = await result.get_data()
        
        print("\n\n" + "="*60)
        print("GENERATED CODE")
        print("="*60)
        
        print(f"\nLanguage: {code_snippet.language}")
        print(f"\nCode:\n```{code_snippet.language}")
        print(code_snippet.code)
        print("```")
        
        print(f"\nExplanation:\n{code_snippet.explanation}")
        
        if code_snippet.dependencies:
            print(f"\nDependencies:")
            for dep in code_snippet.dependencies:
                print(f"  - {dep}")

asyncio.run(generate_code_streaming())
```

## Streaming to Web UI

### FastAPI Integration

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic_ai import Agent
import asyncio

app = FastAPI()
agent = Agent('openai:gpt-4')

@app.get("/chat/stream")
async def stream_chat(message: str):
    """Stream chat responses to web client."""
    
    async def generate():
        async with agent.run_stream(message) as result:
            async for chunk in result.stream_text():
                # Yield in Server-Sent Events format
                yield f"data: {chunk}\n\n"
            
            # Signal completion
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

# To run: uvicorn main:app --reload
```

### WebSocket Streaming

```python
from fastapi import FastAPI, WebSocket
from pydantic_ai import Agent

app = FastAPI()
agent = Agent('openai:gpt-4')

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Stream chat via WebSocket."""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            
            # Stream response
            async with agent.run_stream(message) as result:
                async for chunk in result.stream_text():
                    await websocket.send_text(chunk)
                
                # Send completion signal
                await websocket.send_json({"type": "done"})
    
    except Exception as e:
        await websocket.close()
```

## Error Handling in Streaming

### Handling Stream Interruptions

```python
import asyncio
from pydantic_ai import Agent

async def stream_with_error_handling():
    """Handle errors during streaming."""
    agent = Agent('openai:gpt-4')
    
    try:
        async with agent.run_stream('Explain machine learning') as result:
            try:
                async for chunk in result.stream_text():
                    print(chunk, end='', flush=True)
            
            except asyncio.CancelledError:
                print("\n\nStream cancelled by user")
                raise
            
            except Exception as e:
                print(f"\n\nError during streaming: {e}")
                raise
            
            # Get final result even if streaming had issues
            final_data = await result.get_data()
            print(f"\n\nCompleted: {len(str(final_data))} characters")
    
    except Exception as e:
        print(f"Failed to complete stream: {e}")

asyncio.run(stream_with_error_handling())
```

### Timeout Handling

```python
import asyncio
from pydantic_ai import Agent

async def stream_with_timeout():
    """Stream with timeout protection."""
    agent = Agent('openai:gpt-4')
    
    try:
        async with asyncio.timeout(30):  # 30 second timeout
            async with agent.run_stream(
                'Write a long essay about philosophy'
            ) as result:
                async for chunk in result.stream_text():
                    print(chunk, end='', flush=True)
    
    except asyncio.TimeoutError:
        print("\n\nStream timed out after 30 seconds")

asyncio.run(stream_with_timeout())
```

## Best Practices

### 1. Always Use Async Context Manager

```python
# ✅ Good
async with agent.run_stream(prompt) as result:
    async for chunk in result.stream_text():
        print(chunk, end='')

# ❌ Bad - Missing context manager
result = await agent.run_stream(prompt)
```

### 2. Handle Partial Results Gracefully

```python
async def safe_streaming():
    async with agent.run_stream(prompt) as result:
        partial_text = ""
        
        try:
            async for chunk in result.stream_text():
                partial_text += chunk
                print(chunk, end='', flush=True)
        except Exception as e:
            print(f"\nStream interrupted: {e}")
            print(f"Partial result: {partial_text}")
```

### 3. Provide User Feedback

```python
async def stream_with_feedback():
    print("🤖 Thinking...\n")
    
    async with agent.run_stream(prompt) as result:
        async for chunk in result.stream_text():
            print(chunk, end='', flush=True)
        
        print("\n\n✅ Response complete!")
```

### 4. Use Appropriate Flush

```python
# For real-time display
async for chunk in result.stream_text():
    print(chunk, end='', flush=True)  # flush=True is important
```

### 5. Consider Buffering for UI

```python
async def smooth_ui_stream():
    """Buffer chunks for smoother UI updates."""
    buffer = ""
    min_chunk_size = 10
    
    async with agent.run_stream(prompt) as result:
        async for chunk in result.stream_text():
            buffer += chunk
            
            if len(buffer) >= min_chunk_size:
                # Update UI with buffer
                print(buffer, end='', flush=True)
                buffer = ""
        
        # Flush remaining
        if buffer:
            print(buffer, end='', flush=True)
```

## Exercise

Create a streaming news summarizer that:
1. Takes a news article URL as input
2. Shows progress indicators while fetching the article
3. Streams the summary as it's generated
4. Returns a structured `NewsSummary` model with:
   - Title
   - Key points (list)
   - Sentiment
   - Category
5. Handles errors gracefully with partial results

## What's Next?

In the next lesson, we'll explore advanced features:
- Retry logic and error handling
- Conversation context management
- Model switching and fallbacks
- Performance optimization
- Production best practices

---

**Previous Lesson**: [Lesson 6: Result Validation with Pydantic](../lesson-06-result-validation/README.md)  
**Next Lesson**: [Lesson 8: Advanced Features](../lesson-08-advanced-features/README.md)
