from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlmodel import Session

from app.api import api_router
from app.db import session as db_session
from app.db.database import init_db
from app.services.seed_service import ensure_seed_dataset

# Ensure repo root is importable for the core package.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_db()
        with Session(db_session.engine) as session:
            ensure_seed_dataset(session)
    except Exception as exc:
        logger.warning("Seed dataset skipped: %s", exc)
    yield


app = FastAPI(lifespan=lifespan, title="IU Project API", version="1.0.0")
app.include_router(api_router)


@app.get("/health")
def health():
    return {"ok": True}
