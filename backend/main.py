from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # <-- таблицы создаются на старте
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def read_root() -> dict:
    return {"message": "hello world"}
