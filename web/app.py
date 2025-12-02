from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(title="IU Scheduler API", version="0.1.0")


@app.get("/", response_class=PlainTextResponse)
async def read_root() -> str:
    """Simple hello world endpoint to verify FastAPI is running."""
    return "Hello, World!"
