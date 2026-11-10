# main.py - a tiny to-do Task API built with FastAPI
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
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
