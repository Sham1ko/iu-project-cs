from sqlmodel import SQLModel

from app.db.session import engine, get_session


def init_db() -> None:
    from app.db import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
