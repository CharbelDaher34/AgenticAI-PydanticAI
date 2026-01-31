# PydanticAI Masterclass

A comprehensive, hands-on course covering PydanticAI from foundations to production deployment. All examples follow **async-only** patterns and include **Logfire instrumentation** for complete observability.

## 🎯 Course Philosophy

- **Async-Only**: All examples use async/await patterns for production-ready code
- **Observable by Default**: Every example includes Logfire tracing (free tier)
- **Practical & Hands-On**: Learn by building real-world examples
- **Clean Architecture**: Follow Python best practices and clean code principles

## 📁 Project Structure

```
pydanticai-masterclass/
├── README.md                   # This file
├── .env.example                # API Keys template
├── common/                     # Shared utilities
│   ├── __init__.py
│   └── database.py             # Mock DB for examples
└── lessons/
    ├── 01_foundations/
    │   ├── 00_basics/              # Agent basics
    │   ├── 01_dependency_injection/ # Deps & Context
    │   └── 02_dynamic_tools/        # Deferred Tools
    ├── 02_architecture/
    │   ├── 01_multi_agent_handoff/  # Agent Transfer
    │   └── 02_pydantic_graph/       # Graph/State Machine
    ├── 03_integration/
    │   ├── 01_mcp_client/           # MCP Integration
    │   └── 02_web_ui_agui/          # AG-UI & Streaming
    └── 04_production/
        ├── 01_durable_execution/    # DBOS/Reliability
        └── 02_testing_strategies/   # Pytest & Evals
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- OpenAI API key (or other LLM provider)
- uv package manager (recommended) or poetry

### Installation with uv

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
cd pydanticai-masterclass

# Install dependencies with Logfire support
uv add "pydantic-ai[logfire]" pydantic-settings

# Setup environment variables
cp .env.example .env
# Edit .env and add your API keys (see below)
```

### Logfire Setup (Free - No Credit Card Required)

Logfire provides complete observability for your agents. It's free to use with a generous free tier.

```bash
# Authenticate with Logfire
uv run logfire auth

# Create or select a project
uv run logfire projects use
# or
uv run logfire projects new
```

This creates a `.logfire/` directory that the SDK uses for configuration.

### Environment Variables

All configuration is managed via **Pydantic Settings** for type safety and validation.

Create a `.env` file in the project root:

```bash
# Required - Get your key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Optional - Other providers
# ANTHROPIC_API_KEY=...
# GOOGLE_API_KEY=...
```

The settings are automatically loaded by the `common.settings` module.

## 📚 Learning Path

### Level 1: Foundations (Start Here)

**Lesson 00: PydanticAI Basics** (`lessons/01_foundations/00_basics/`)
- Agent creation and async execution
- Streaming responses
- Logfire integration

**Lesson 01: Dependency Injection** (`lessons/01_foundations/01_dependency_injection/`)
- Using RunContext for dependencies
- Database injection patterns
- Dynamic system prompts
- Testing with mocks

**Lesson 02: Dynamic Tools** (`lessons/01_foundations/02_dynamic_tools/`)
- Deferred tool registration
- Permission-based tools
- Runtime configuration

### Level 2: Architecture (Coming Soon)

**Lesson 03: Multi-Agent Handoff**
- Agent-to-agent communication
- Context transfer
- Orchestration patterns

**Lesson 04: Pydantic Graph**
- State machines with agents
- Graph-based workflows
- Complex decision trees

### Level 3: Integration (Coming Soon)

**Lesson 05: MCP Client**
- Model Context Protocol integration
- External tool providers
- Plugin architecture

**Lesson 06: Web UI with AG-UI**
- Building chat interfaces
- Server-sent events
- Real-time streaming

### Level 4: Production (Coming Soon)

**Lesson 07: Durable Execution**
- DBOS integration
- Reliability patterns
- Error recovery

**Lesson 08: Testing Strategies**
- Pytest patterns
- Agent testing
- Evaluation frameworks

## 🏃 Running Examples

All examples are designed to run independently:

```bash
# Run any example directly
uv run lessons/01_foundations/00_basics/01_simple_agent.py

# Or navigate to the directory
cd lessons/01_foundations/01_dependency_injection
uv run 01_basic_deps.py
```

After running, check your [Logfire dashboard](https://logfire.pydantic.dev) to see:
- Complete execution traces
- Tool calls and results
- Token usage and costs
- Performance metrics

## 🔍 Why Async-Only?

This course uses async/await exclusively because:

1. **Production Ready**: Real-world applications need async for performance
2. **Concurrent Operations**: Run multiple agents or tool calls in parallel
3. **Non-Blocking**: Better resource utilization and responsiveness
4. **Modern Python**: Async is the standard for I/O-bound operations
5. **Native Support**: PydanticAI is built with async-first design

## 📊 Why Logfire?

Logfire instrumentation is included in every example because:

1. **Understand Agent Behavior**: See exactly what the LLM is doing
2. **Debug Issues**: Full trace context when things go wrong
3. **Monitor Costs**: Track token usage across all requests
4. **Optimize Performance**: Identify slow operations
5. **Free to Use**: Generous free tier, no credit card required

## 🛠️ Common Utilities

### Pydantic Settings

All configuration is centralized in `common/settings.py`:

```python
from common import settings

# Settings are loaded from .env automatically
api_key = settings.openai_api_key
debug_mode = settings.debug
```

### Mock Database

The `common/database.py` module provides an in-memory database for examples:

```python
from common.database import MockDatabase, mock_db

# Use in examples
db = MockDatabase()
user = await db.get_user(1)
products = await db.search_products("laptop")
```

This lets you focus on learning PydanticAI without setting up real databases.

## 🎓 Learning Tips

1. **Run the examples**: Don't just read - execute and modify them
2. **Check Logfire**: Always review traces to understand agent behavior
3. **Experiment**: Try different prompts, tools, and configurations
4. **Build Projects**: Apply concepts to your own use cases
5. **Read Documentation**: Examples reference official PydanticAI docs

## 📖 Resources

- [PydanticAI Documentation](https://ai.pydantic.dev/)
- [Logfire Documentation](https://logfire.pydantic.dev/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## 🤝 Contributing

Found an issue or have a suggestion? Contributions welcome!

## 📝 License

This course is open-source and available under the MIT License.

## 🙏 Acknowledgments

Built with:
- [PydanticAI](https://ai.pydantic.dev/) by the Pydantic team
- [Logfire](https://logfire.pydantic.dev/) for observability
- Examples inspired by real-world production use cases

---

**Ready to start?** Head to [`lessons/01_foundations/00_basics/`](lessons/01_foundations/00_basics/) and run your first agent!
