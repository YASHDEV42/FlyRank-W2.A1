# main.py - a tiny FastAPI app
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    # Say hello so we know the server is running
    return {"message": "Hello, world!"}
