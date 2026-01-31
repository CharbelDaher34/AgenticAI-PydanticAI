# Lesson 3: System Prompts and Configuration

## Overview

System prompts are crucial for defining your agent's behavior, personality, and capabilities. In this lesson, you'll learn:
- How to add system prompts to agents
- Dynamic prompts based on context
- Static vs dynamic system prompts
- Best practices for prompt engineering

## Basic System Prompts

### Static System Prompt

Add a system prompt when creating an agent:

```python
from pydantic_ai import Agent

agent = Agent(
    'openai:gpt-4',
    system_prompt='You are a helpful assistant specialized in Python programming.'
)

result = agent.run_sync('How do I create a list?')
print(result.data)
# Response will be focused on Python
```

### Multi-line System Prompt

Use triple quotes for longer prompts:

```python
from pydantic_ai import Agent

system_prompt = """
You are a professional Python coding assistant with the following traits:
- You provide clear, concise explanations
- You include code examples for every concept
- You follow PEP 8 style guidelines
- You suggest best practices and warn about common pitfalls
- You are patient and encouraging with beginners
"""

agent = Agent('openai:gpt-4', system_prompt=system_prompt)

result = agent.run_sync('Explain list comprehensions.')
print(result.data)
```

## Dynamic System Prompts

System prompts can be dynamic, computed at runtime based on context.

### Using Decorators

The most powerful way to create dynamic prompts:

```python
from pydantic_ai import Agent, RunContext

# Define an agent with dependencies
agent = Agent(
    'openai:gpt-4',
    deps_type=str  # The dependency type (user role in this case)
)

@agent.system_prompt
def get_system_prompt(ctx: RunContext[str]) -> str:
    """Generate system prompt based on user role."""
    role = ctx.deps
    
    prompts = {
        'beginner': 'You are a patient teacher. Explain concepts simply with lots of examples.',
        'intermediate': 'You are a mentor. Provide detailed explanations with best practices.',
        'expert': 'You are a peer. Be concise and focus on advanced topics.'
    }
    
    return prompts.get(role, prompts['intermediate'])

# Use the agent with different user roles
result_beginner = agent.run_sync(
    'Explain decorators',
    deps='beginner'
)
print("Beginner response:", result_beginner.data)

result_expert = agent.run_sync(
    'Explain decorators',
    deps='expert'
)
print("Expert response:", result_expert.data)
```

### Context-Based Prompts

Access runtime context in your prompts:

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserContext:
    name: str
    timezone: str
    preferences: dict

agent = Agent(
    'openai:gpt-4',
    deps_type=UserContext
)

@agent.system_prompt
def personalized_prompt(ctx: RunContext[UserContext]) -> str:
    user = ctx.deps
    current_time = datetime.now()
    
    return f"""
    You are a personal assistant for {user.name}.
    
    Current context:
    - User timezone: {user.timezone}
    - Current time: {current_time.strftime('%Y-%m-%d %H:%M')}
    - User preferences: {user.preferences}
    
    Tailor your responses to be helpful and personal.
    """

# Create user context
user = UserContext(
    name='Alice',
    timezone='America/New_York',
    preferences={'language': 'Python', 'framework': 'FastAPI'}
)

result = agent.run_sync(
    'What should I work on today?',
    deps=user
)
print(result.data)
```

## Multiple System Prompts

You can register multiple system prompt functions:

```python
from pydantic_ai import Agent, RunContext

agent = Agent('openai:gpt-4', deps_type=str)

@agent.system_prompt
def base_prompt(ctx: RunContext[str]) -> str:
    return "You are a helpful coding assistant."

@agent.system_prompt
def additional_context(ctx: RunContext[str]) -> str:
    language = ctx.deps
    return f"You specialize in {language} programming."

# Both prompts will be combined
result = agent.run_sync(
    'How do I handle errors?',
    deps='Python'
)
print(result.data)
```

## Prompt Templates

Create reusable prompt templates:

```python
from pydantic_ai import Agent, RunContext

def create_role_prompt(
    role: str,
    expertise: str,
    tone: str = 'professional'
) -> str:
    """Template for creating role-based prompts."""
    return f"""
    You are a {role} with expertise in {expertise}.
    Your communication style is {tone}.
    
    Guidelines:
    - Be accurate and helpful
    - Provide examples when relevant
    - Ask clarifying questions when needed
    """

# Create different agents from template
support_agent = Agent(
    'openai:gpt-4',
    system_prompt=create_role_prompt(
        role='customer support specialist',
        expertise='technical troubleshooting',
        tone='friendly and empathetic'
    )
)

sales_agent = Agent(
    'openai:gpt-4',
    system_prompt=create_role_prompt(
        role='sales consultant',
        expertise='product features and pricing',
        tone='professional and persuasive'
    )
)
```

## Real-World Example: Customer Support Bot

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from typing import Optional

@dataclass
class SupportContext:
    user_id: str
    user_name: str
    account_tier: str  # 'free', 'pro', 'enterprise'
    has_active_ticket: bool
    previous_issues: list[str]

agent = Agent(
    'openai:gpt-4',
    deps_type=SupportContext
)

@agent.system_prompt
def support_prompt(ctx: RunContext[SupportContext]) -> str:
    context = ctx.deps
    
    prompt = f"""
    You are a customer support agent for TechCorp.
    
    Customer Information:
    - Name: {context.user_name}
    - Account Tier: {context.account_tier}
    - Has Active Ticket: {context.has_active_ticket}
    """
    
    if context.previous_issues:
        issues_list = '\n  - '.join(context.previous_issues)
        prompt += f"\n\nPrevious Issues:\n  - {issues_list}"
    
    prompt += """
    
    Your Guidelines:
    1. Be professional and empathetic
    2. Provide clear, step-by-step solutions
    3. Escalate to human agent if the issue is complex
    4. Thank the customer for their patience
    """
    
    if context.account_tier == 'enterprise':
        prompt += "\n5. This is an enterprise customer - prioritize their request"
    
    return prompt

# Use the support bot
support_context = SupportContext(
    user_id='USR-12345',
    user_name='John Doe',
    account_tier='pro',
    has_active_ticket=False,
    previous_issues=[
        'Login issues (resolved)',
        'Billing question (resolved)'
    ]
)

result = agent.run_sync(
    "I can't access the dashboard",
    deps=support_context
)
print(result.data)
```

## Advanced: Conditional Prompts

```python
from pydantic_ai import Agent, RunContext
from typing import Optional

agent = Agent('openai:gpt-4', deps_type=dict)

@agent.system_prompt
def conditional_prompt(ctx: RunContext[dict]) -> str:
    config = ctx.deps
    
    base = "You are an AI assistant."
    
    if config.get('debug_mode'):
        base += "\n\nDEBUG MODE: Provide detailed explanations of your reasoning."
    
    if config.get('formal_tone'):
        base += "\n\nUse formal, professional language."
    else:
        base += "\n\nUse casual, friendly language."
    
    if expertise := config.get('expertise'):
        base += f"\n\nYou are an expert in: {expertise}"
    
    return base

# Different configurations
result1 = agent.run_sync(
    'Explain async programming',
    deps={'debug_mode': True, 'expertise': 'Python'}
)

result2 = agent.run_sync(
    'Explain async programming',
    deps={'formal_tone': True}
)
```

## Prompt Engineering Best Practices

### 1. Be Specific and Clear

```python
# ❌ Bad
system_prompt = "Help users with coding"

# ✅ Good
system_prompt = """
You are a Python programming assistant focused on:
- Writing clean, maintainable code
- Following PEP 8 guidelines
- Explaining concepts with examples
- Suggesting best practices
"""
```

### 2. Define Boundaries

```python
system_prompt = """
You are a financial advisor assistant.

You CAN:
- Provide general financial education
- Explain financial concepts
- Suggest resources for learning

You CANNOT:
- Give specific investment advice
- Make predictions about markets
- Access real-time financial data

Always remind users to consult licensed professionals for specific advice.
"""
```

### 3. Set Output Format

```python
system_prompt = """
You are a code reviewer.

For each code review, provide:
1. Summary: Brief overview of the code
2. Strengths: What's done well
3. Issues: Problems found (if any)
4. Suggestions: Improvements to consider
5. Rating: Score from 1-10

Use markdown formatting for readability.
"""
```

### 4. Include Examples

```python
system_prompt = """
You are a SQL query assistant.

When users ask questions, provide SQL queries in this format:

```sql
-- Description of what the query does
SELECT column1, column2
FROM table_name
WHERE condition
ORDER BY column1;
```

Example interaction:
User: "Show me all users registered this year"
Assistant: 
```sql
-- Get all users registered in current year
SELECT * 
FROM users 
WHERE YEAR(registration_date) = YEAR(CURRENT_DATE);
```
"""
```

## Testing System Prompts

```python
from pydantic_ai import Agent

def test_system_prompt():
    """Test that system prompt affects agent behavior."""
    
    # Agent without specific prompt
    generic_agent = Agent('openai:gpt-4')
    
    # Agent with Python focus
    python_agent = Agent(
        'openai:gpt-4',
        system_prompt='You are a Python expert. Only discuss Python.'
    )
    
    question = 'How do I create a variable?'
    
    generic_result = generic_agent.run_sync(question)
    python_result = python_agent.run_sync(question)
    
    print("Generic:", generic_result.data)
    print("Python-focused:", python_result.data)
    
    # Python agent should mention Python specifically
    assert 'python' in python_result.data.lower()

test_system_prompt()
```

## Common Patterns

### 1. Role-Based Prompts

```python
def get_role_prompt(role: str) -> str:
    return f"You are a {role}. Act accordingly."
```

### 2. Domain-Specific Prompts

```python
MEDICAL_PROMPT = "You are a medical information assistant. Always remind users to consult healthcare professionals."
LEGAL_PROMPT = "You are a legal information assistant. Always remind users to consult licensed attorneys."
```

### 3. Persona Prompts

```python
FRIENDLY_PROMPT = "You are friendly and casual. Use emojis and be enthusiastic!"
PROFESSIONAL_PROMPT = "You are professional and formal. Be concise and precise."
```

## Exercise

Create a tutoring agent that:
1. Adapts its explanation style based on the student's grade level
2. Uses dynamic system prompts to adjust complexity
3. Includes examples appropriate for the student's level
4. Encourages the student with positive reinforcement

Try implementing this with different grade levels (elementary, middle school, high school, college).

## What's Next?

In the next lesson, we'll explore:
- Dependency injection in PydanticAI
- Using dependencies for database access, API clients, and more
- Testing agents with mock dependencies

---

**Previous Lesson**: [Lesson 2: Creating Your First Agent](../lesson-02-first-agent/README.md)  
**Next Lesson**: [Lesson 4: Dependencies and Dependency Injection](../lesson-04-dependencies/README.md)
