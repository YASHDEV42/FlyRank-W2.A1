# main.py - a tiny to-do Task API built with FastAPI
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StrictStr, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# Our "database": a plain Python list that lives in memory (RAM)
tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Write the README", "done": False},
    {"id": 3, "title": "Buy milk", "done": True},
]


# ---------- Error handling: always reply with {"error": "..."} ----------

@app.exception_handler(StarletteHTTPException)
def http_error(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
def validation_error(request: Request, exc: RequestValidationError):
    # Replace FastAPI's default 422 with a 400 and one readable message
    err = exc.errors()[0]
    field = err["loc"][-1] if len(err["loc"]) > 1 else "Request body"
    messages = {
        "missing": f"{field} is required",
        "value_error": f"{field} {err['msg'].removeprefix('Value error, ')}",
        "string_type": f"{field} must be a string",
        "bool_type": f"{field} must be true or false",
        "int_parsing": f"{field} must be an integer",
        "json_invalid": "Request body must be valid JSON",
        "model_attributes_type": "Request body must be a JSON object",
    }
    message = messages.get(err["type"], f"{field}: {err['msg']}")
    return JSONResponse(status_code=400, content={"error": message})


# ---------- Request body models ----------

def clean_title(value):
    # Shared rule: title must be a non-empty string (spaces are trimmed)
    if value is None or not value.strip():
        raise ValueError("must not be empty")
    return value.strip()


class TaskCreate(BaseModel):
    title: StrictStr  # StrictStr: numbers, lists etc. are rejected

    _check_title = field_validator("title")(clean_title)


# ---------- Helpers ----------

def find_task(task_id: int):
    # Return the task with this id, or raise a 404 error
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---------- Endpoints ----------

@app.get("/")
def root():
    # Basic info about the API
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    # Simple check that the server is alive
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    # Return every task
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    # Return one task (404 if it does not exist)
    return find_task(task_id)


@app.post("/tasks", status_code=201)
def create_task(body: TaskCreate):
    # Next id = biggest existing id + 1 (or 1 if the list is empty)
    new_id = max((t["id"] for t in tasks), default=0) + 1
    task = {"id": new_id, "title": body.title, "done": False}
    tasks.append(task)
    return task
