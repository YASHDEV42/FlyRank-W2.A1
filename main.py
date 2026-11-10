# main.py - a tiny to-do Task API built with FastAPI
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    # Basic info about the API
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    # Simple check that the server is alive
    return {"status": "ok"}
