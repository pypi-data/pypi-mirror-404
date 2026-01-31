from typing import Dict, List, Literal, TypedDict


class TodoItem:
    """A single todo item."""
    id: str
    content: str
    status: Literal["pending", "in_progress", "completed"]
    priority: Literal["high", "medium", "low"]


class TodoListManager:
    """Manages todo lists for orchestrator agent.

    Provides structured task tracking to help organize complex workflows
    and display progress to users.
    """

    def __init__(self):
        """Initialize empty todo list."""
        self.todos: Dict[str, TodoItem] = {}
        self._next_id = 1

    def add_todo(
        self,
        content: str,
        priority: Literal["high", "medium", "low"] = "medium",
        status: Literal["pending", "in_progress", "completed"] = "pending"
    ) -> TodoItem:
        """Add a new todo item.

        Args:
            content: Description of the task
            priority: Task priority (high, medium, low)
            status: Initial status

        Returns:
            The created todo item
        """
        todo_id = str(self._next_id)
        self._next_id += 1

        todo: TodoItem = {
            "id": todo_id,
            "content": content,
            "status": status,
            "priority": priority
        }

        self.todos[todo_id] = todo
        return todo

    def update_todo(
        self,
        todo_id: str,
        content: str = None,
        status: Literal["pending", "in_progress", "completed"] = None,
        priority: Literal["high", "medium", "low"] = None
    ) -> TodoItem:
        """Update an existing todo item.

        Args:
            todo_id: ID of todo to update
            content: New content (optional)
            status: New status (optional)
            priority: New priority (optional)

        Returns:
            The updated todo item

        Raises:
            KeyError: If todo_id not found
        """
        if todo_id not in self.todos:
            raise KeyError(f"Todo {todo_id} not found")

        todo = self.todos[todo_id]

        if content is not None:
            todo["content"] = content
        if status is not None:
            todo["status"] = status
        if priority is not None:
            todo["priority"] = priority

        return todo

    def remove_todo(self, todo_id: str) -> None:
        """Remove a todo item.

        Args:
            todo_id: ID of todo to remove

        Raises:
            KeyError: If todo_id not found
        """
        if todo_id not in self.todos:
            raise KeyError(f"Todo {todo_id} not found")

        del self.todos[todo_id]

    def get_todos(
        self,
        status: Literal["pending", "in_progress", "completed"] = None,
        priority: Literal["high", "medium", "low"] = None
    ) -> List[TodoItem]:
        """Get todo items, optionally filtered.

        Args:
            status: Filter by status (optional)
            priority: Filter by priority (optional)

        Returns:
            List of matching todo items
        """
        todos = list(self.todos.values())

        if status is not None:
            todos = [t for t in todos if t["status"] == status]

        if priority is not None:
            todos = [t for t in todos if t["priority"] == priority]

        # Sort by priority (high -> medium -> low), then by id
        priority_order = {"high": 0, "medium": 1, "low": 2}
        todos.sort(key=lambda t: (priority_order[t["priority"]], int(t["id"])))

        return todos

    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics of todos.

        Returns:
            Dictionary with counts by status
        """
        summary = {
            "total": len(self.todos),
            "pending": 0,
            "in_progress": 0,
            "completed": 0
        }

        for todo in self.todos.values():
            summary[todo["status"]] += 1

        return summary

    def clear_completed(self) -> int:
        """Remove all completed todos.

        Returns:
            Number of todos removed
        """
        completed_ids = [
            todo_id for todo_id, todo in self.todos.items()
            if todo["status"] == "completed"
        ]

        for todo_id in completed_ids:
            del self.todos[todo_id]

        return len(completed_ids)

    def to_dict(self) -> List[TodoItem]:
        """Export all todos as a list of dictionaries.

        Returns:
            List of all todo items
        """
        return self.get_todos()


# Tool definition for adding to orchestrator tools
TODO_TOOL_DEFINITION = {
    "name": "manage_todo_list",
    "description": (
        "Manage a todo list to track tasks and progress. Use this to organize complex workflows, "
        "break down large tasks into smaller steps, and show the user your progress. "
        "This is especially useful for multi-step analyses or reports."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "update", "remove", "list", "summary", "clear_completed"],
                "description": "Action to perform on the todo list"
            },
            "todo_id": {
                "type": "string",
                "description": "ID of todo item (required for update/remove)"
            },
            "content": {
                "type": "string",
                "description": "Task description (required for add, optional for update)"
            },
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"],
                "description": "Task status"
            },
            "priority": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Task priority"
            },
            "filter_status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"],
                "description": "Filter todos by status (for list action)"
            },
            "filter_priority": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Filter todos by priority (for list action)"
            }
        },
        "required": ["action"]
    }
}
