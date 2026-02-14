"""Lesson 02.4: Deferred Tools - Tools requiring approval or external execution.

This example demonstrates:
- Tools requiring human approval
- Conditional approval based on context
- External tool execution pattern
- Processing deferred tool results
- Real-world patterns for sensitive operations
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import logfire
from pydantic_ai import Agent, ApprovalRequired, CallDeferred, RunContext
from pydantic_ai.result import DeferredToolRequests, DeferredToolResults, ToolDenied

# Add common directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from common import get_logger, settings
from common.database import MockDatabase

# Set OpenAI API key from settings
os.environ["OPENAI_API_KEY"] = settings.openai_api_key

# Get logger from centralized configuration
log = get_logger(__name__)

# Configure Logfire
logfire.configure(console=False)
logfire.instrument_pydantic_ai()


@dataclass
class FileSystemContext:
    """Context for file system operations."""
    
    db: MockDatabase
    user_id: int
    is_admin: bool
    protected_files: list[str]


# Agent with tools requiring approval
approval_agent = Agent[FileSystemContext, str | DeferredToolRequests](
    "openai:gpt-4o-mini",
    system_prompt=(
        "You are a file system assistant. You can perform various file operations, "
        "but some operations require user approval."
    ),
)


# Example 1: Tool requiring automatic approval
# Use requires_approval=True to require approval for ALL calls to this tool
@approval_agent.tool_plain(requires_approval=True)
def delete_file(path: str) -> str:
    """Delete a file (requires approval).
    
    This tool ALWAYS requires approval before execution.
    
    Args:
        path: Path to the file to delete
    
    Returns:
        Success message
    """
    return f"File '{path}' has been deleted"


@approval_agent.tool_plain(requires_approval=True)
def modify_system_settings(setting: str, value: str) -> str:
    """Modify system settings (requires approval).
    
    Args:
        setting: Setting name
        value: New value
    
    Returns:
        Success message
    """
    return f"System setting '{setting}' changed to '{value}'"


# Example 2: Tool with conditional approval
# Use ApprovalRequired exception to request approval only in certain conditions
@approval_agent.tool
def update_file(ctx: RunContext[FileSystemContext], path: str, content: str) -> str:
    """Update a file's content.
    
    Requires approval only for protected files.
    
    Args:
        ctx: Run context
        path: File path
        content: New content
    
    Returns:
        Success message
    
    Raises:
        ApprovalRequired: If file is protected
    """
    # Check if this is a protected file
    if path in ctx.deps.protected_files:
        # Request approval only for protected files
        if not ctx.tool_call_approved:
            raise ApprovalRequired(
                metadata={
                    "reason": "protected_file",
                    "file": path,
                    "warning": "This is a critical system file",
                }
            )
    
    return f"File '{path}' updated successfully"


@approval_agent.tool
def create_user(ctx: RunContext[FileSystemContext], username: str) -> str:
    """Create a new user (admin only, requires approval).
    
    Args:
        ctx: Run context
        username: Username for the new user
    
    Returns:
        Success message
    
    Raises:
        ApprovalRequired: If user is not admin or not approved
    """
    if not ctx.deps.is_admin:
        return "Error: Only administrators can create users"
    
    # Even admins need approval for user creation
    if not ctx.tool_call_approved:
        raise ApprovalRequired(
            metadata={
                "reason": "user_creation",
                "username": username,
                "requester": ctx.deps.user_id,
            }
        )
    
    return f"User '{username}' created successfully"


# Example 3: External tool execution
# Use CallDeferred when tool execution happens outside the current process
external_agent = Agent[MockDatabase, str | DeferredToolRequests](
    "openai:gpt-4o-mini",
    system_prompt="You are an assistant that can queue long-running tasks.",
)

# Simulated external task storage
pending_tasks = {}
task_counter = 0


@external_agent.tool
async def run_background_analysis(
    ctx: RunContext[MockDatabase], data_type: str
) -> str:
    """Run a background analysis task.
    
    This tool queues the task for external execution.
    
    Args:
        ctx: Run context
        data_type: Type of data to analyze
    
    Returns:
        Task ID
    
    Raises:
        CallDeferred: Always, to signal external execution
    """
    global task_counter
    task_id = f"task_{task_counter}"
    task_counter += 1
    
    # Store task info
    pending_tasks[task_id] = {
        "type": "analysis",
        "data_type": data_type,
        "status": "pending",
    }
    
    # Signal that this will be executed externally
    raise CallDeferred(
        metadata={
            "task_id": task_id,
            "message": f"Analysis task queued with ID: {task_id}",
        }
    )


async def example_approval_flow():
    """Example: Complete approval flow for file deletion."""
    print("=== Example 1: Approval Flow ===\n")
    
    ctx = FileSystemContext(
        db=MockDatabase(),
        user_id=1,
        is_admin=False,
        protected_files=["/etc/config.conf", "/etc/passwd"],
    )
    
    # Step 1: Run agent - it will request approval
    print("Step 1: Agent requests file deletion")
    result = await approval_agent.run(
        "Delete the file /tmp/cache.txt",
        deps=ctx,
        output_type=[str, DeferredToolRequests],
    )
    
    # Check if we got deferred requests
    if isinstance(result.output, DeferredToolRequests):
        print(f"Step 2: Approval required for {len(result.output.approvals)} tool(s)\n")
        
        # Step 2: Review and approve/deny requests
        results = DeferredToolResults()
        
        for call in result.output.approvals:
            print(f"Tool: {call.tool_name}")
            print(f"Arguments: {call.args_json}")
            print(f"Decision: APPROVED (auto-approved for demo)")
            
            # Approve the call
            results.approvals[call.tool_call_id] = True
            # To deny: results.approvals[call.tool_call_id] = ToolDenied(reason="Not authorized")
        
        # Step 3: Continue with approvals
        print("\nStep 3: Continuing with approvals...\n")
        final_result = await approval_agent.run(
            message_history=result.all_messages(),
            deferred_tool_results=results,
            deps=ctx,
        )
        
        print(f"Final Result: {final_result.output}\n")
    else:
        print(f"No approval needed: {result.output}\n")


async def example_conditional_approval():
    """Example: Conditional approval for protected files."""
    print("=== Example 2: Conditional Approval ===\n")
    
    ctx = FileSystemContext(
        db=MockDatabase(),
        user_id=1,
        is_admin=True,
        protected_files=["/etc/config.conf", "/etc/passwd"],
    )
    
    # Try to update a non-protected file - no approval needed
    print("Scenario A: Regular file (no approval needed)")
    result = await approval_agent.run(
        "Update /tmp/log.txt with new log entry",
        deps=ctx,
        output_type=[str, DeferredToolRequests],
    )
    
    if isinstance(result.output, str):
        print(f"Result: {result.output}")
        print("(No approval was required)\n")
    
    # Try to update a protected file - approval needed
    print("Scenario B: Protected file (approval needed)")
    result = await approval_agent.run(
        "Update /etc/config.conf with new settings",
        deps=ctx,
        output_type=[str, DeferredToolRequests],
    )
    
    if isinstance(result.output, DeferredToolRequests):
        print(f"Approval required! File is protected.")
        print(f"Metadata: {result.output.approvals[0].metadata}\n")
        
        # Approve and continue
        results = DeferredToolResults()
        results.approvals[result.output.approvals[0].tool_call_id] = True
        
        final_result = await approval_agent.run(
            message_history=result.all_messages(),
            deferred_tool_results=results,
            deps=ctx,
        )
        
        print(f"After approval: {final_result.output}\n")


async def example_denied_approval():
    """Example: Denying an approval request."""
    print("=== Example 3: Denied Approval ===\n")
    
    ctx = FileSystemContext(
        db=MockDatabase(),
        user_id=1,
        is_admin=False,
        protected_files=[],
    )
    
    result = await approval_agent.run(
        "Delete the file /important/data.db",
        deps=ctx,
        output_type=[str, DeferredToolRequests],
    )
    
    if isinstance(result.output, DeferredToolRequests):
        print("Approval requested for file deletion")
        
        # Deny the request
        results = DeferredToolResults()
        results.approvals[result.output.approvals[0].tool_call_id] = ToolDenied(
            reason="Deletion of important data files is not allowed"
        )
        
        print("Decision: DENIED\n")
        
        final_result = await approval_agent.run(
            message_history=result.all_messages(),
            deferred_tool_results=results,
            deps=ctx,
        )
        
        print(f"Agent Response: {final_result.output}\n")


async def example_external_execution():
    """Example: External tool execution pattern."""
    print("=== Example 4: External Tool Execution ===\n")
    
    db = MockDatabase()
    
    # Step 1: Queue the task
    print("Step 1: Queue background analysis task")
    result = await external_agent.run(
        "Run a background analysis on sales data",
        deps=db,
        output_type=[str, DeferredToolRequests],
    )
    
    if isinstance(result.output, DeferredToolRequests):
        print(f"Task queued: {len(result.output.calls)} deferred call(s)\n")
        
        # Step 2: Simulate external processing
        print("Step 2: External system processes the task...")
        for call in result.output.calls:
            task_id = call.metadata.get("task_id")
            print(f"  Processing task: {task_id}")
            
            # Simulate task completion
            await asyncio.sleep(1)
            pending_tasks[task_id]["status"] = "completed"
            pending_tasks[task_id]["result"] = "Analysis complete: 1,234 records processed"
        
        # Step 3: Return results to agent
        print("\nStep 3: Sending results back to agent...\n")
        results = DeferredToolResults()
        
        for call in result.output.calls:
            task_id = call.metadata.get("task_id")
            task_result = pending_tasks[task_id]["result"]
            results.calls[call.tool_call_id] = task_result
        
        final_result = await external_agent.run(
            message_history=result.all_messages(),
            deferred_tool_results=results,
            deps=db,
        )
        
        print(f"Agent Final Response: {final_result.output}\n")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("DEFERRED TOOLS EXAMPLES")
    print("=" * 80 + "\n")
    
    print("Key Concepts:")
    print("1. requires_approval=True - Always require approval for a tool")
    print("2. ApprovalRequired - Request approval conditionally")
    print("3. CallDeferred - Signal external execution")
    print("4. DeferredToolResults - Provide results from approvals/external execution")
    print("5. ToolDenied - Deny approval requests\n")
    
    print("=" * 80 + "\n")
    
    await example_approval_flow()
    print("-" * 80 + "\n")
    
    await example_conditional_approval()
    print("-" * 80 + "\n")
    
    await example_denied_approval()
    print("-" * 80 + "\n")
    
    await example_external_execution()
    
    print("=" * 80)
    print("Key Takeaways:")
    print("- Deferred tools enable human-in-the-loop workflows")
    print("- ApprovalRequired allows conditional approval logic")
    print("- CallDeferred supports external/async tool execution")
    print("- DeferredToolResults reconnects deferred operations")
    print("- Critical for production systems with sensitive operations")
    print("\nCheck Logfire dashboard to see deferred tool flows!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
