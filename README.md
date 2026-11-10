# Task API

A small to-do **CRUD REST API** built with FastAPI for the **FlyRank Internship – Backend Track, W2 A1**.
You can create, read, update and delete tasks (`{ "id", "title", "done" }`) over HTTP.
All data is kept **in memory** (a plain Python list in `main.py`). There is no database and no file storage.

## Install and run

Requires Python 3.10+.

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The server runs at http://localhost:8000.

## Endpoints

| Method | Path | Description | Success | Errors |
|--------|------|-------------|---------|--------|
| GET | `/` | API info (name, version, endpoints) | 200 | – |
| GET | `/health` | Health check, returns `{"status": "ok"}` | 200 | – |
| GET | `/tasks` | List all tasks | 200 | – |
| GET | `/tasks?done=true\|false` | Only done / only open tasks | 200 | 400 (done not true/false) |
| GET | `/tasks?search=milk` | Tasks whose title contains the word (case-insensitive); can be combined with `done` | 200 | – |
| GET | `/tasks/{id}` | Get one task | 200 | 400 (id not an integer), 404 |
| POST | `/tasks` | Create a task from `{"title": "..."}` | 201 | 400 |
| PUT | `/tasks/{id}` | Update `title` and/or `done` | 200 | 400, 404 |
| DELETE | `/tasks/{id}` | Delete a task (empty response body) | 204 | 400 (id not an integer), 404 |
| GET | `/stats` | Counts: `{"total": n, "done": n, "open": n}` | 200 | – |
| POST | `/reset` | Restore the 3 example tasks (discards all changes) | 200 | – |

Every error is JSON in the form `{ "error": "<message>" }`, for example `{"error": "Task 99 not found"}`.
Validation problems (missing or empty title, wrong types, empty body) return **400**, not FastAPI's default 422.

## Example (real output)

```
$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title": "Buy milk"}'
HTTP/1.1 201 Created
date: Tue, 10 Nov 2026 07:12:38 GMT
server: uvicorn
content-length: 40
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Swagger UI

Interactive docs are built in at http://localhost:8000/docs. Use "Try it out" to call any endpoint from the browser.

![Swagger UI](docs/swagger.png)

## Observation: data lives in memory

I created two tasks (ids 4 and 5) and restarted the server. After the restart, `GET /tasks` returned only the 3 example tasks, so the new ones were gone.
This happens because the tasks live only in a Python list in RAM, which is rebuilt from scratch every time the process starts. Storing them in a database (for example SQLite or PostgreSQL) would keep them across restarts.
