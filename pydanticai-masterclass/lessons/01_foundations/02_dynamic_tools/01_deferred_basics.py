"""Lesson 02.1: Deferred Tools Basics - Tools decided at runtime.

This example demonstrates:
- Creating tools that can only be determined after agent initialization
- Using tool_plain decorator for deferred registration
- Runtime tool decision making
- Using Logfire to trace dynamic tool calls

Deferred tools are useful when:
- Tool availability depends on user permissions
- Tool configuration depends on runtime data
- Tools need to be created dynamically per request
"""

import asyncio
import os
import sys
from pathlib import Path

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings
import logfire
from pydantic_ai import Agent, RunContext

# Get structured logger
log = get_logger(__name__)

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()


# Example 1: Basic deferred tool
basic_agent = Agent[str, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a helpful assistant with access to various tools.",
)


async def create_greeting_tool(language: str):
    """Create a greeting tool for a specific language."""
    
    async def greet_user(ctx: RunContext[str]) -> str:
        """Greet the user in the specified language."""
        greetings = {
            "english": f"Hello, {ctx.deps}!",
            "spanish": f"¡Hola, {ctx.deps}!",
            "french": f"Bonjour, {ctx.deps}!",
            "german": f"Guten Tag, {ctx.deps}!",
        }
        return greetings.get(language, f"Hello, {ctx.deps}!")
    
    return greet_user


async def example_basic_deferred():
    """Basic example of deferred tool registration."""
    print("=== Example 1: Basic Deferred Tool ===\n")
    
    # User prefers Spanish
    language = "spanish"
    user_name = "Maria"
    
    # Create the appropriate greeting tool
    greeting_tool = await create_greeting_tool(language)
    
    # Run agent with the tool
    result = await basic_agent.run(
        "Please greet me",
        deps=user_name,
        tool_plain=greeting_tool,
    )
    
    print(f"Language: {language}")
    print(f"User: {user_name}")
    print(f"Response: {result.output}\n")


# Example 2: Permission-based tools
permissions_agent = Agent[dict, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a file system assistant with permission-based access.",
)


async def create_file_tools(permissions: list[str]):
    """Create file operation tools based on permissions."""
    
    tools = []
    
    if "read" in permissions:
        async def read_file(ctx: RunContext[dict], filename: str) -> str:
            """Read a file (requires 'read' permission)."""
            files = ctx.deps.get("files", {})
            content = files.get(filename, "File not found")
            return f"Content of {filename}: {content}"
        
        tools.append(read_file)
    
    if "write" in permissions:
        async def write_file(ctx: RunContext[dict], filename: str, content: str) -> str:
            """Write to a file (requires 'write' permission)."""
            ctx.deps.setdefault("files", {})[filename] = content
            return f"Successfully wrote to {filename}"
        
        tools.append(write_file)
    
    if "delete" in permissions:
        async def delete_file(ctx: RunContext[dict], filename: str) -> str:
            """Delete a file (requires 'delete' permission)."""
            files = ctx.deps.get("files", {})
            if filename in files:
                del files[filename]
                return f"Successfully deleted {filename}"
            return f"File {filename} not found"
        
        tools.append(delete_file)
    
    return tools


async def example_permission_based():
    """Example with permission-based tool availability."""
    print("=== Example 2: Permission-Based Tools ===\n")
    
    # Test with read-only user
    print("Read-only user:")
    read_only_deps = {
        "files": {
            "document.txt": "This is a document",
            "notes.txt": "Important notes",
        }
    }
    
    read_tools = await create_file_tools(["read"])
    result = await permissions_agent.run(
        "Read document.txt and then try to delete it",
        deps=read_only_deps,
        tool_plain=read_tools,
    )
    print(f"Response: {result.output}\n")
    
    # Test with full permissions
    print("\nFull permission user:")
    admin_deps = {
        "files": {
            "test.txt": "Test content",
        }
    }
    
    all_tools = await create_file_tools(["read", "write", "delete"])
    result = await permissions_agent.run(
        "Read test.txt, write 'New content' to new.txt, then delete test.txt",
        deps=admin_deps,
        tool_plain=all_tools,
    )
    print(f"Response: {result.output}\n")


# Example 3: Runtime configuration
calculator_agent = Agent[dict, str](
    "openai:gpt-4o-mini",
    system_prompt="You are a calculator assistant.",
)


async def create_calculator_tools(allowed_operations: list[str]):
    """Create calculator tools based on allowed operations."""
    
    tools = []
    
    if "add" in allowed_operations:
        async def add(ctx: RunContext[dict], a: float, b: float) -> float:
            """Add two numbers."""
            return a + b
        
        tools.append(add)
    
    if "subtract" in allowed_operations:
        async def subtract(ctx: RunContext[dict], a: float, b: float) -> float:
            """Subtract b from a."""
            return a - b
        
        tools.append(subtract)
    
    if "multiply" in allowed_operations:
        async def multiply(ctx: RunContext[dict], a: float, b: float) -> float:
            """Multiply two numbers."""
            return a * b
        
        tools.append(multiply)
    
    if "divide" in allowed_operations:
        async def divide(ctx: RunContext[dict], a: float, b: float) -> str:
            """Divide a by b."""
            if b == 0:
                return "Error: Division by zero"
            return str(a / b)
        
        tools.append(divide)
    
    return tools


async def example_runtime_configuration():
    """Example with runtime configuration of available tools."""
    print("=== Example 3: Runtime Configuration ===\n")
    
    # Basic calculator (only addition and subtraction)
    print("Basic calculator:")
    basic_tools = await create_calculator_tools(["add", "subtract"])
    result = await calculator_agent.run(
        "Calculate (15 + 7) - 3",
        deps={},
        tool_plain=basic_tools,
    )
    print(f"Response: {result.output}\n")
    
    # Scientific calculator (all operations)
    print("\nScientific calculator:")
    scientific_tools = await create_calculator_tools(["add", "subtract", "multiply", "divide"])
    result = await calculator_agent.run(
        "Calculate (15 + 7) * 3 / 2",
        deps={},
        tool_plain=scientific_tools,
    )
    print(f"Response: {result.output}\n")


async def main():
    """Run all deferred tools examples."""
    print("\n" + "=" * 80)
    print("DEFERRED TOOLS BASICS")
    print("=" * 80 + "\n")
    
    await example_basic_deferred()
    await example_permission_based()
    await example_runtime_configuration()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("1. Deferred tools are registered at runtime with tool_plain")
    print("2. Perfect for permission-based feature access")
    print("3. Allows dynamic tool configuration per request")
    print("4. Check Logfire to see which tools were available and used!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
