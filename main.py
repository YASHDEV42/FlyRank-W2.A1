# main.py - a tiny to-do Task API built with FastAPI
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, StrictBool, StrictStr, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="Task API", version="1.0", description="A simple in-memory to-do CRUD API.")

# Our "database": a plain Python list that lives in memory (RAM)
tasks = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Write the README", "done": False},
    {"id": 3, "title": "Buy milk", "done": True},
]


# ---------- Models (they also drive the Swagger UI schemas) ----------

def clean_title(value):
    # Shared rule: title must be a non-empty string (spaces are trimmed)
    if value is None:
        raise ValueError("must be a string")
    if not value.strip():
        raise ValueError("must not be empty")
    return value.strip()


class Task(BaseModel):
    id: int
    title: str
    done: bool


class Error(BaseModel):
    error: str = Field(examples=["Task 99 not found"])


class TaskCreate(BaseModel):
    title: StrictStr = Field(examples=["Buy milk"])  # StrictStr: numbers etc. are rejected

    _check_title = field_validator("title")(clean_title)


class TaskUpdate(BaseModel):
    # Both fields are optional: only the ones sent will be changed
    title: StrictStr | None = Field(None, examples=["Buy oat milk"])
    done: StrictBool | None = Field(None, examples=[True])  # StrictBool: only true/false

    _check_title = field_validator("title")(clean_title)

    @field_validator("done")
    def check_done(cls, value):
        # Runs only if "done" was sent; reject an explicit null
        if value is None:
            raise ValueError("must be true or false")
        return value


# Response codes shown in Swagger for each route
BAD_REQUEST = {400: {"model": Error, "description": "Invalid request body"}}
NOT_FOUND = {404: {"model": Error, "description": "Task not found"}}


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


def find_task(task_id: int):
    # Return the task with this id, or raise a 404 error
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---------- Endpoints ----------

@app.get("/", tags=["info"], summary="API info", description="Name, version and endpoints of the API.",
         responses={200: {"description": "API info"}})
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", tags=["info"], summary="Health check", description="Returns ok if the server is running.",
         responses={200: {"description": "Server is healthy"}})
def health():
    return {"status": "ok"}


@app.get("/tasks", tags=["tasks"], summary="List tasks", description="Return every task.",
         response_model=list[Task], responses={200: {"description": "All tasks"}})
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}", tags=["tasks"], summary="Get a task", description="Return one task by its id.",
         response_model=Task, responses={200: {"description": "The task"}, **BAD_REQUEST, **NOT_FOUND})
def get_task(task_id: int):
    return find_task(task_id)


@app.post("/tasks", status_code=201, tags=["tasks"], summary="Create a task",
          description="Create a task from a title; it starts with done=false.",
          response_model=Task, responses={201: {"description": "Task created"}, **BAD_REQUEST})
def create_task(body: TaskCreate):
    # Next id = biggest existing id + 1 (or 1 if the list is empty)
    new_id = max((t["id"] for t in tasks), default=0) + 1
    task = {"id": new_id, "title": body.title, "done": False}
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", tags=["tasks"], summary="Update a task",
         description="Change the title and/or done status; fields you leave out stay the same.",
         response_model=Task, responses={200: {"description": "Task updated"}, **BAD_REQUEST, **NOT_FOUND})
def update_task(task_id: int, body: TaskUpdate):
    task = find_task(task_id)
    changes = body.model_dump(exclude_unset=True)  # only fields that were sent
    if not changes:
        raise HTTPException(status_code=400, detail="Provide at least one of: title, done")
    task.update(changes)
    return task


@app.delete("/tasks/{task_id}", status_code=204, tags=["tasks"], summary="Delete a task",
            description="Remove a task; the response has an empty body.",
            responses={204: {"description": "Task deleted (empty body)"}, **BAD_REQUEST, **NOT_FOUND})
def delete_task(task_id: int):
    tasks.remove(find_task(task_id))
    return Response(status_code=204)  # 204 = success, empty body


# ---------- Swagger: hide FastAPI's automatic 422 (we return 400 instead) ----------

default_openapi = app.openapi


def openapi_without_422():
    schema = default_openapi()
    for path in schema["paths"].values():
        for operation in path.values():
            operation["responses"].pop("422", None)
    for name in ("HTTPValidationError", "ValidationError"):
        schema["components"]["schemas"].pop(name, None)
    return schema


app.openapi = openapi_without_422
