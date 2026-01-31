# Lesson 1: Introduction to PydanticAI

## What is PydanticAI?

PydanticAI is a Python agent framework designed to make it easy to build production-grade applications with Generative AI. It's developed by the team behind Pydantic and focuses on:

- **Type Safety**: Leverages Python's type system and Pydantic models
- **Model Agnostic**: Works with OpenAI, Anthropic, Gemini, Ollama, and more
- **Developer Experience**: Clean, Pythonic API that's easy to test and maintain
- **Production Ready**: Built-in retry logic, validation, and error handling

## Key Features

1. **Type-safe agent framework** - Uses Pydantic models for validation
2. **Model-agnostic design** - Switch between different LLM providers easily
3. **Dependency injection** - Clean separation of concerns
4. **Structured outputs** - Get validated, typed responses
5. **Tool/function calling** - Extend agents with custom functions
6. **Streaming support** - Handle real-time responses
7. **Testing utilities** - Mock responses for testing

## Installation

Install PydanticAI using pip:

```bash
pip install pydantic-ai
```

For specific model support, install additional dependencies:

```bash
# For OpenAI
pip install pydantic-ai[openai]

# For Anthropic
pip install pydantic-ai[anthropic]

# For Google Gemini
pip install pydantic-ai[gemini]

# For Ollama (local models)
pip install pydantic-ai[ollama]

# Install all providers
pip install pydantic-ai[openai,anthropic,gemini,ollama]
```

## Core Concepts

### Agent

The `Agent` is the central class in PydanticAI. It represents an AI agent that can:
- Receive user messages
- Process them using an LLM
- Return structured responses
- Use tools to perform actions

### Models

PydanticAI supports multiple model providers:
- **OpenAI**: GPT-4, GPT-3.5, etc.
- **Anthropic**: Claude 3 Opus, Sonnet, Haiku
- **Google**: Gemini Pro, Gemini Ultra
- **Ollama**: Local models like Llama, Mistral
- **Custom**: Build your own model integration

### Dependencies

Dependencies allow you to inject context and services into your agent, making it testable and maintainable.

### Tools

Tools (or function calling) let your agent perform actions beyond text generation, like:
- Querying databases
- Calling APIs
- Performing calculations
- Accessing files

## Your First Example

Here's a minimal PydanticAI example:

```python
from pydantic_ai import Agent

# Create a simple agent
agent = Agent('openai:gpt-4')

# Run the agent with a prompt
result = agent.run_sync('What is the capital of France?')
print(result.data)
# Output: Paris
```

## Setting Up API Keys

Most LLM providers require API keys. Set them as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY='your-api-key-here'

# Anthropic
export ANTHROPIC_API_KEY='your-api-key-here'

# Google Gemini
export GEMINI_API_KEY='your-api-key-here'
```

Or in Python:

```python
import os
os.environ['OPENAI_API_KEY'] = 'your-api-key-here'
```

## Project Structure

A typical PydanticAI project structure:

```
my_project/
├── agents/
│   ├── __init__.py
│   ├── customer_support.py
│   └── data_analyst.py
├── tools/
│   ├── __init__.py
│   ├── database.py
│   └── api_client.py
├── models/
│   ├── __init__.py
│   └── schemas.py
├── tests/
│   ├── test_agents.py
│   └── test_tools.py
└── main.py
```

## Best Practices

1. **Use type hints**: Always annotate your functions and agent results
2. **Validate inputs**: Use Pydantic models for structured data
3. **Handle errors**: Implement proper error handling and retries
4. **Test thoroughly**: Use PydanticAI's testing utilities
5. **Monitor usage**: Track token usage and costs
6. **Version control prompts**: Keep system prompts in version control

## What's Next?

In the next lesson, we'll create our first PydanticAI agent and learn about:
- Agent initialization
- Running agents synchronously and asynchronously
- Handling responses
- Basic error handling

## Resources

- [PydanticAI Documentation](https://ai.pydantic.dev/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [GitHub Repository](https://github.com/pydantic/pydantic-ai)

## Exercise

1. Install PydanticAI in a virtual environment
2. Set up your API key for your preferred LLM provider
3. Run the simple example above and verify it works
4. Try changing the model (e.g., from GPT-4 to GPT-3.5-turbo)

---

**Next Lesson**: [Lesson 2: Creating Your First Agent](../lesson-02-first-agent/README.md)
