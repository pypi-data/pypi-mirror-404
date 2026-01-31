"""Todo list tool for orchestrator agent task management."""

from typing import Dict, List, Literal

from pydantic_ai import FunctionToolset, RunContext

from lineage.agent.pydantic.tools.common import safe_tool
from lineage.agent.pydantic.types import AgentDeps
from lineage.backends.todos.todo_manager import TodoItem

todo_list_manager_toolset = FunctionToolset()

@todo_list_manager_toolset.tool
@safe_tool
async def add_todo(
    ctx: RunContext[AgentDeps],
    content: str,
    priority: Literal["high", "medium", "low"] = "medium",
    status: Literal["pending", "in_progress", "completed"] = "pending"
) -> TodoItem:
    """Add a new todo item."""
    return ctx.deps.todo_list_manager.add_todo(content, priority, status)

@todo_list_manager_toolset.tool
@safe_tool
async def update_todo(
    ctx: RunContext[AgentDeps],
    todo_id: str,
    content: str = None,
    status: Literal["pending", "in_progress", "completed"] = None,
    priority: Literal["high", "medium", "low"] = None
) -> TodoItem:
    """Update an existing todo item."""
    return ctx.deps.todo_list_manager.update_todo(todo_id, content, status, priority)

@todo_list_manager_toolset.tool
@safe_tool
async def remove_todo(
    ctx: RunContext[AgentDeps],
    todo_id: str
) -> None:
    """Remove an existing todo item."""
    return ctx.deps.todo_list_manager.remove_todo(todo_id)

@todo_list_manager_toolset.tool
@safe_tool
async def get_todos(
    ctx: RunContext[AgentDeps],
    status: Literal["pending", "in_progress", "completed"] = None,
    priority: Literal["high", "medium", "low"] = None
) -> List[TodoItem]:
    """Get all todo items."""
    return ctx.deps.todo_list_manager.get_todos(status, priority)

@todo_list_manager_toolset.tool
@safe_tool
async def get_summary(
    ctx: RunContext[AgentDeps]
) -> Dict[str, int]:
    """Get summary statistics of todos."""
    return ctx.deps.todo_list_manager.get_summary()

@todo_list_manager_toolset.tool
@safe_tool
async def clear_completed(
    ctx: RunContext[AgentDeps]
) -> int:
    """Clear all completed todos."""
    return ctx.deps.todo_list_manager.clear_completed()


# System prompt guidance for todo tool usage
TODO_SYSTEM_PROMPT_GUIDANCE = """
## Todo List Tool Usage

You have access to a todo list for organizing and tracking tasks.

**When to use:**
- Breaking down complex multi-step analyses
- Creating reports that require multiple queries
- Troubleshooting issues with several investigation steps
- Any task with 3+ distinct steps

**Best practices:**
- Create the todo list at the START of complex tasks
- Use descriptive task names
- Mark tasks as "in_progress" when you start them
- Mark tasks as "completed" immediately after finishing
- Update the list as you discover new subtasks
- Use priorities to indicate critical vs optional steps

**Example workflow:**
1. User asks for revenue analysis
2. Add todos: "Find revenue models", "Validate query", "Create visualizations"
3. Mark "Find revenue models" as in_progress
4. Complete and mark as completed
5. Move to next task

The todo list helps the user see your progress in real-time.
""".strip()
