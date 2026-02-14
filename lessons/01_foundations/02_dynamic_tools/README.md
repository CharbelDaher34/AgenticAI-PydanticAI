# Lesson 02: Dynamic Tools (Deferred Tools)

## Overview

This lesson explores **deferred tools** in PydanticAI - a powerful pattern for creating tools dynamically at runtime based on dependencies. This enables highly flexible and context-aware agent behaviors.

## What You'll Learn

1. **Deferred Tools Basics** - Understanding the `@agent.tool_deferred` decorator
2. **Dynamic Tool Creation** - Creating tools based on runtime context
3. **Conditional Tools** - Tools that only exist in certain conditions
4. **User-Specific Tools** - Different users get different capabilities
5. **Real-World Patterns** - Practical applications of deferred tools

## Key Concepts

### What are Deferred Tools?

Regular tools are defined once when you create the agent. **Deferred tools** are created fresh for each agent run based on the current dependencies.

```python
# Regular tool - always available
@agent.tool
async def static_tool(ctx: RunContext[Deps]) -> str:
    return "I'm always here"

# Deferred tool - created per-run based on deps
@agent.tool_deferred
async def make_tools(ctx: RunContext[Deps]) -> list[Tool]:
    # Create different tools based on ctx.deps
    if ctx.deps.is_admin:
        return [admin_tool]
    else:
        return [user_tool]
```

### Why Use Deferred Tools?

1. **Conditional Capabilities** - Give different users different tools
2. **Dynamic Data** - Tools that depend on runtime data (e.g., product catalogs)
3. **Permission-Based** - Tools that only exist for authorized users
4. **Personalization** - Adapt agent capabilities to user context

### Deferred vs Regular Tools

| Feature            | Regular Tools      | Deferred Tools             |
| ------------------ | ------------------ | -------------------------- |
| **When created**   | At agent creation  | At each run                |
| **Depends on**     | Static config      | Runtime dependencies       |
| **Performance**    | Faster             | Slight overhead            |
| **Flexibility**    | Fixed              | Highly dynamic             |
| **Use case**       | Standard features  | Context-dependent features |

## Examples

1. **01_basic_deferred.py** - Introduction to deferred tools
2. **02_conditional_tools.py** - Tools that exist conditionally
3. **03_permission_based.py** - Role-based tool access
4. **04_dynamic_catalog.py** - Tools based on available products
5. **05_user_personalization.py** - Per-user tool customization

## Running the Examples

```bash
# Run basic example
uv run lessons/01_foundations/02_dynamic_tools/01_basic_deferred.py

# Run permission example
uv run lessons/01_foundations/02_dynamic_tools/03_permission_based.py

# Run all examples
for f in lessons/01_foundations/02_dynamic_tools/*.py; do
    echo "Running $f..."
    uv run "$f"
done
```

## Best Practices

1. **Keep deferred logic simple** - Complex tool generation slows down each run
2. **Cache when possible** - If tools don't really change, use regular tools
3. **Document dynamic behavior** - Make it clear why tools are deferred
4. **Test all code paths** - Test with different deps that create different tools
5. **Use for real needs** - Don't defer just because you can

## Common Patterns

### Permission-Based Access

```python
@agent.tool_deferred
async def make_admin_tools(ctx: RunContext[UserContext]) -> list[Tool]:
    tools = [basic_tool]  # Everyone gets this
    if ctx.deps.is_admin:
        tools.append(admin_tool)  # Only admins get this
    return tools
```

### Data-Driven Tools

```python
@agent.tool_deferred
async def make_product_tools(ctx: RunContext[Database]) -> list[Tool]:
    # Create a tool for each product category
    categories = await ctx.deps.get_categories()
    return [create_category_tool(cat) for cat in categories]
```

## Next Steps

After mastering deferred tools, proceed to:
- **Module 02**: Multi-agent architectures
- **Module 03**: Integration patterns (MCP, web UI)
