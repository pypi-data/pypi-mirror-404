#!/usr/bin/env python3
"""Sample FastAPI server for testing gmcp."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Sample API",
    description="A sample FastAPI server to demonstrate gmcp",
    version="1.0.0"
)

# In-memory data store
users_db = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
}
next_user_id = 3

todos_db = {
    1: {"id": 1, "title": "Buy groceries", "completed": False},
    2: {"id": 2, "title": "Write documentation", "completed": True},
}
next_todo_id = 3


# Models
class User(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


class Todo(BaseModel):
    title: str
    completed: bool = False


class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool


# User endpoints
@app.get("/", summary="Root endpoint")
async def root():
    """Welcome message."""
    return {"message": "Welcome to Sample API. Visit /docs for API documentation."}


@app.get("/users", response_model=list[UserResponse], summary="List all users")
async def list_users():
    """Get a list of all users."""
    return list(users_db.values())


@app.get("/users/{user_id}", response_model=UserResponse, summary="Get a user by ID")
async def get_user(user_id: int):
    """Retrieve a specific user by their ID."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]


@app.post("/users", response_model=UserResponse, summary="Create a new user")
async def create_user(user: User):
    """Create a new user with the provided name and email."""
    global next_user_id
    user_id = next_user_id
    next_user_id += 1

    new_user = {"id": user_id, "name": user.name, "email": user.email}
    users_db[user_id] = new_user
    return new_user


@app.put("/users/{user_id}", response_model=UserResponse, summary="Update a user")
async def update_user(user_id: int, user: User):
    """Update an existing user's information."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    users_db[user_id].update({"name": user.name, "email": user.email})
    return users_db[user_id]


@app.delete("/users/{user_id}", summary="Delete a user")
async def delete_user(user_id: int):
    """Delete a user by ID."""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    del users_db[user_id]
    return {"message": f"User {user_id} deleted"}


# Todo endpoints
@app.get("/todos", response_model=list[TodoResponse], summary="List all todos")
async def list_todos(completed: bool | None = None):
    """Get a list of all todos, optionally filtered by completion status."""
    todos = list(todos_db.values())
    if completed is not None:
        todos = [t for t in todos if t["completed"] == completed]
    return todos


@app.get("/todos/{todo_id}", response_model=TodoResponse, summary="Get a todo by ID")
async def get_todo(todo_id: int):
    """Retrieve a specific todo by its ID."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todos_db[todo_id]


@app.post("/todos", response_model=TodoResponse, summary="Create a new todo")
async def create_todo(todo: Todo):
    """Create a new todo item."""
    global next_todo_id
    todo_id = next_todo_id
    next_todo_id += 1

    new_todo = {"id": todo_id, "title": todo.title, "completed": todo.completed}
    todos_db[todo_id] = new_todo
    return new_todo


@app.patch("/todos/{todo_id}", response_model=TodoResponse, summary="Toggle todo completion")
async def toggle_todo(todo_id: int):
    """Toggle the completion status of a todo."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")

    todos_db[todo_id]["completed"] = not todos_db[todo_id]["completed"]
    return todos_db[todo_id]


@app.delete("/todos/{todo_id}", summary="Delete a todo")
async def delete_todo(todo_id: int):
    """Delete a todo by ID."""
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")

    del todos_db[todo_id]
    return {"message": f"Todo {todo_id} deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
