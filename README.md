# PydanticAI Tutorial

A comprehensive, hands-on tutorial for learning PydanticAI - the Python agent framework for building production-grade AI applications.

## 📚 About This Tutorial

This tutorial is designed to take you from beginner to advanced in PydanticAI, with practical examples and real-world use cases. Each lesson is self-contained and builds upon previous concepts.

## 🎯 What is PydanticAI?

PydanticAI is a Python agent framework developed by the Pydantic team that makes it easy to build production-grade applications with Generative AI. It features:

- **Type Safety**: Leverages Python's type system and Pydantic models
- **Model Agnostic**: Works with OpenAI, Anthropic, Gemini, Ollama, and more
- **Developer Experience**: Clean, Pythonic API that's easy to test and maintain
- **Production Ready**: Built-in retry logic, validation, and error handling

## 📖 Tutorial Structure

### Beginner Lessons

#### [Lesson 1: Introduction to PydanticAI](./lessons/lesson-01-introduction/README.md)
- What is PydanticAI and why use it?
- Installation and setup
- Core concepts and architecture
- Your first agent example

#### [Lesson 2: Creating Your First Agent](./lessons/lesson-02-first-agent/README.md)
- Agent initialization with different models
- Synchronous vs asynchronous execution
- Understanding agent results
- Basic error handling
- Complete chatbot example

#### [Lesson 3: System Prompts and Configuration](./lessons/lesson-03-system-prompts/README.md)
- Static and dynamic system prompts
- Context-based prompts
- Prompt templates and best practices
- Real-world examples (customer support, tutoring)

### Intermediate Lessons

#### [Lesson 4: Dependencies and Dependency Injection](./lessons/lesson-04-dependencies/README.md)
- Understanding dependencies
- Using dependencies in agents and tools
- Database and API integration
- Testing with mock dependencies

#### [Lesson 5: Tools and Function Calling](./lessons/lesson-05-tools/README.md)
- Creating and registering tools
- Tool parameters and return types
- Using dependencies in tools
- Async tools and error handling
- E-commerce assistant example

#### [Lesson 6: Result Validation with Pydantic](./lessons/lesson-06-result-validation/README.md)
- Structured outputs with Pydantic models
- Data validation and constraints
- Complex nested structures
- Data extraction use cases (invoices, meetings, contacts)

### Advanced Lessons

#### [Lesson 7: Streaming Responses](./lessons/lesson-07-streaming/README.md)
- Streaming text and structured data
- Streaming with dependencies
- Web UI integration (FastAPI, WebSocket)
- Error handling in streaming

#### [Lesson 8: Advanced Features](./lessons/lesson-08-advanced-features/README.md)
- Retry logic and error handling
- Model configuration and switching
- Context and conversation management
- Performance optimization (caching, batching)
- Testing strategies
- Production best practices

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Basic knowledge of Python and async/await
- Familiarity with type hints (helpful but not required)

### Installation

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install PydanticAI with your preferred model provider
pip install pydantic-ai[openai]

# Or install with multiple providers
pip install pydantic-ai[openai,anthropic,gemini]
```

### Set Up API Keys

```bash
# For OpenAI
export OPENAI_API_KEY='your-api-key-here'

# For Anthropic
export ANTHROPIC_API_KEY='your-api-key-here'

# For Google Gemini
export GEMINI_API_KEY='your-api-key-here'
```

### Quick Start

```python
from pydantic_ai import Agent

# Create a simple agent
agent = Agent('openai:gpt-4')

# Run the agent
result = agent.run_sync('What is the capital of France?')
print(result.data)  # Output: Paris
```

## 🎓 Learning Path

### Recommended Order

1. **Start with basics** → Lessons 1-3
2. **Build practical skills** → Lessons 4-6
3. **Master advanced topics** → Lessons 7-8

### Time Commitment

- **Beginner (Lessons 1-3)**: ~2-3 hours
- **Intermediate (Lessons 4-6)**: ~3-4 hours
- **Advanced (Lessons 7-8)**: ~3-4 hours
- **Total**: ~8-11 hours

### Practice Projects

After completing the lessons, try building:

1. **Customer Support Bot** - Use dependencies, tools, and system prompts
2. **Data Extraction Service** - Parse invoices, receipts, or documents
3. **Code Review Assistant** - Analyze code and provide feedback
4. **Personal Assistant** - Manage tasks, schedule, and reminders
5. **Content Generator** - Create blogs, social media posts, or documentation

## 💡 Key Concepts

### Agents
The core abstraction representing an AI agent that can receive messages, process them using LLMs, and return structured responses.

### Dependencies
Services, data, or context injected into agents using dependency injection for clean, testable code.

### Tools
Python functions that agents can call to perform actions beyond text generation (database queries, API calls, calculations).

### System Prompts
Instructions that define agent behavior, personality, and capabilities. Can be static or dynamic.

### Result Types
Pydantic models that validate and structure agent outputs, ensuring type safety and data quality.

### Streaming
Progressive response generation for better user experience and real-time feedback.

## 🛠️ Supported Models

- **OpenAI**: GPT-4, GPT-3.5-turbo, GPT-4-turbo
- **Anthropic**: Claude 3 Opus, Sonnet, Haiku
- **Google**: Gemini Pro, Gemini Flash
- **Ollama**: Llama, Mistral, and other local models
- **Custom**: Build your own model integration

## 📚 Additional Resources

### Official Documentation
- [PydanticAI Docs](https://ai.pydantic.dev/) - Official documentation
- [Pydantic Docs](https://docs.pydantic.dev/) - Pydantic library docs
- [GitHub Repository](https://github.com/pydantic/pydantic-ai) - Source code and issues

### Community
- [Discord](https://discord.gg/pydantic) - Join the Pydantic community
- [GitHub Discussions](https://github.com/pydantic/pydantic-ai/discussions) - Ask questions and share ideas

### Learning Resources
- [Python Type Hints](https://docs.python.org/3/library/typing.html) - Understanding type annotations
- [Async Python](https://docs.python.org/3/library/asyncio.html) - Async/await programming
- [LLM Basics](https://platform.openai.com/docs/guides/text-generation) - Understanding LLMs

## 🤝 Contributing

Found an issue or want to improve the tutorial? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This tutorial is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Pydantic Team** - For creating PydanticAI and Pydantic
- **Community Contributors** - For feedback and improvements
- **OpenAI, Anthropic, Google** - For providing excellent LLM APIs

## 📬 Feedback

Have questions or suggestions? Please [open an issue](https://github.com/CharbelDaher34/AgenticAI-PydanticAI/issues) or start a [discussion](https://github.com/CharbelDaher34/AgenticAI-PydanticAI/discussions).

---

**Happy Learning! 🚀**

Start your journey: [Lesson 1: Introduction to PydanticAI](./lessons/lesson-01-introduction/README.md)