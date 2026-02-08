"""Lesson 01.6: Output Validators with Dependencies.

This example demonstrates:
- Using dependencies in output validators
- Validating agent output against external data
- Retrying with ModelRetry when validation fails
- Real-world content moderation patterns
"""

import asyncio
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import logfire
from pydantic_ai import Agent, ModelRetry, RunContext

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings

# Get structured logger
log = get_logger(__name__)

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Configure Logfire
logfire.configure()
logfire.instrument_pydantic_ai()


@dataclass
class ValidationDeps:
    """Dependencies for output validation.
    
    In a real application, these might be API clients,
    database connections, or configuration objects.
    """
    
    banned_words: list[str]
    max_length: int
    require_greeting: bool = False
    user_language: str = "en"


# Simple content moderation agent
content_agent = Agent[ValidationDeps, str](
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a helpful customer service assistant. "
        "Provide friendly and professional responses to customer inquiries."
    ),
)


@content_agent.output_validator
async def validate_content(ctx: RunContext[ValidationDeps], output: str) -> str:
    """Validate agent output against content policies.
    
    This validator checks:
    1. Length constraints
    2. Banned words
    3. Required elements (like greetings)
    
    If validation fails, raise ModelRetry to have the agent try again.
    """
    log.info("validating_output", length=len(output))
    
    # Check length
    if len(output) > ctx.deps.max_length:
        log.warning("output_too_long", length=len(output), max=ctx.deps.max_length)
        raise ModelRetry(
            f"Response is too long ({len(output)} characters). "
            f"Please keep it under {ctx.deps.max_length} characters."
        )
    
    # Check for banned words
    output_lower = output.lower()
    for banned_word in ctx.deps.banned_words:
        if banned_word.lower() in output_lower:
            log.warning("banned_word_found", word=banned_word)
            raise ModelRetry(
                f"Your response contains inappropriate content. "
                f"Please rephrase without using '{banned_word}'."
            )
    
    # Check for required greeting
    if ctx.deps.require_greeting:
        greetings = ["hello", "hi", "hey", "greetings", "welcome"]
        has_greeting = any(greeting in output_lower for greeting in greetings)
        if not has_greeting:
            log.warning("missing_greeting")
            raise ModelRetry(
                "Please start your response with a friendly greeting."
            )
    
    log.info("validation_passed")
    return output


async def example_length_validation():
    """Example: Enforce maximum response length."""
    print("=== Example 1: Length Validation ===\n")
    
    deps = ValidationDeps(
        banned_words=[],
        max_length=100,  # Very short limit to trigger retry
    )
    
    result = await content_agent.run(
        "Tell me about your company's history and achievements.",
        deps=deps,
    )
    
    print(f"User: Tell me about your company's history and achievements.")
    print(f"Agent: {result.output}")
    print(f"Length: {len(result.output)} characters (max: {deps.max_length})\n")


async def example_content_moderation():
    """Example: Filter inappropriate content."""
    print("=== Example 2: Content Moderation ===\n")
    
    deps = ValidationDeps(
        banned_words=["spam", "advertisement", "promotion"],
        max_length=500,
    )
    
    # This should work fine
    result = await content_agent.run(
        "Can you help me with my order?",
        deps=deps,
    )
    
    print(f"User: Can you help me with my order?")
    print(f"Agent: {result.output}\n")


async def example_required_greeting():
    """Example: Enforce greeting requirement."""
    print("=== Example 3: Required Greeting ===\n")
    
    deps = ValidationDeps(
        banned_words=[],
        max_length=500,
        require_greeting=True,
    )
    
    result = await content_agent.run(
        "What are your business hours?",
        deps=deps,
    )
    
    print(f"User: What are your business hours?")
    print(f"Agent: {result.output}\n")


async def example_multi_constraint():
    """Example: Multiple validation constraints."""
    print("=== Example 4: Multiple Constraints ===\n")
    
    deps = ValidationDeps(
        banned_words=["competitor", "other company"],
        max_length=200,
        require_greeting=True,
    )
    
    result = await content_agent.run(
        "Why should I choose your service?",
        deps=deps,
    )
    
    print(f"User: Why should I choose your service?")
    print(f"Agent: {result.output}")
    print(f"✓ Validated: greeting included, no banned words, under {deps.max_length} chars\n")


@dataclass
class DatabaseValidationDeps:
    """Dependencies that use actual data lookups for validation."""
    
    valid_product_ids: set[int]
    valid_order_statuses: set[str]


order_agent = Agent[DatabaseValidationDeps, str](
    "openai:gpt-4o-mini",
    system_prompt="You are an order management assistant. Provide order status updates.",
)


@order_agent.output_validator
async def validate_order_info(ctx: RunContext[DatabaseValidationDeps], output: str) -> str:
    """Validate that output only references valid products and order statuses.
    
    In a real application, this might check against a database or API.
    """
    log.info("validating_order_info")
    
    # Check if output mentions invalid product IDs
    # Simple check: look for "product [ID]" pattern
    
    product_mentions = re.findall(r'product\s+(\d+)', output.lower())
    for product_id_str in product_mentions:
        product_id = int(product_id_str)
        if product_id not in ctx.deps.valid_product_ids:
            log.warning("invalid_product_id", product_id=product_id)
            raise ModelRetry(
                f"Product ID {product_id} does not exist. "
                f"Please only reference valid products."
            )
    
    # Check for valid order statuses
    status_mentions = re.findall(
        r'status[:\s]+(\w+)', 
        output.lower()
    )
    for status in status_mentions:
        if status not in ctx.deps.valid_order_statuses:
            log.warning("invalid_status", status=status)
            raise ModelRetry(
                f"'{status}' is not a valid order status. "
                f"Use one of: {', '.join(ctx.deps.valid_order_statuses)}"
            )
    
    log.info("order_validation_passed")
    return output


async def example_data_validation():
    """Example: Validate against data constraints."""
    print("=== Example 5: Data Validation ===\n")
    
    deps = DatabaseValidationDeps(
        valid_product_ids={1, 2, 3, 10, 20},
        valid_order_statuses={"pending", "processing", "shipped", "delivered"},
    )
    
    result = await order_agent.run(
        "What's the status of my order for product 2?",
        deps=deps,
    )
    
    print(f"User: What's the status of my order for product 2?")
    print(f"Agent: {result.output}")
    print(f"✓ Validated: references valid product and status\n")


async def main():
    """Run all output validator examples."""
    print("\n" + "=" * 80)
    print("OUTPUT VALIDATORS WITH DEPENDENCIES")
    print("=" * 80 + "\n")
    
    print("Output validators allow you to:")
    print("1. Enforce constraints on agent responses")
    print("2. Validate against external data sources")
    print("3. Automatically retry when validation fails")
    print("4. Implement content moderation policies\n")
    
    await example_length_validation()
    await example_content_moderation()
    await example_required_greeting()
    await example_multi_constraint()
    await example_data_validation()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- Output validators can access dependencies via RunContext")
    print("- Use ModelRetry to request a corrected response")
    print("- Validators enable policy enforcement and data validation")
    print("- Multiple constraints can be combined in a single validator")
    print("\nCheck Logfire to see validation attempts and retries!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
