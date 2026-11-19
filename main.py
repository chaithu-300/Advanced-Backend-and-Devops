from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import functions

app = FastAPI(title="Todo List API", version="1.0.0")


# ---------- Request / response bodies (Pydantic) ----------
class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: bool = False


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None


class TodoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool


@app.get("/")
def hello():
    return {"message": "Todo List API. Docs at /docs"}


# ---------- Todos ----------
@app.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(data: TodoCreate):
    return functions.create_todo(title=data.title, description=data.description, completed=data.completed)


@app.get("/todos", response_model=List[TodoResponse])
def get_todos():
    return functions.get_todos()


@app.patch("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, data: TodoUpdate):
    changes = data.model_dump(exclude_none=True)  # keep only the fields that were sent

    if changes == {}:
        raise HTTPException(status_code=422, detail="Nothing to update")

    todo = functions.update_todo(todo_id=todo_id, changes=changes)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.delete("/delete_todos/{todo_id}")
def delete_todo(todo_id: int):
    if not functions.delete_todo(todo_id=todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted"}
