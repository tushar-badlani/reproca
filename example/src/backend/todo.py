from msgspec import UNSET, UnsetType
from reproca.method import method

from .models import Todo

todos: list[Todo] = []


@method
async def create_todo(title: str, description: str) -> str:
    """Create a new todo item with the given title and description.

    Args:
    ----
        title: The title of the todo item.
        description: The description of the todo item.

    Returns:
    -------
        The ID of the newly created todo item.

    """
    todo = Todo(
        title=title,
        description=description,
        done=False,
    )
    todos.append(todo)
    return todo.id


@method
async def get_todos() -> list[Todo]:
    return todos


@method
async def update_todo(
    todo_id: str,
    title: str | UnsetType = UNSET,
    description: str | UnsetType = UNSET,
    done: bool | UnsetType = UNSET,
) -> None:
    todo = next((todo for todo in todos if todo.id == todo_id), None)
    if todo is None:
        return
    if title is not UNSET:
        todo.title = title
    if description is not UNSET:
        todo.description = description
    if done is not UNSET:
        todo.done = done


@method
async def delete_todo(todo_id: str) -> None:
    todo_index = next(
        (index for index, todo in enumerate(todos) if todo.id == todo_id), None
    )
    if todo_index is None:
        return
    del todos[todo_index]
