import os
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/iu_project")

engine = create_engine(
    DATABASE_URL,
    echo=False,          # True если хочешь видеть SQL в логах
    pool_pre_ping=True,  # помогает при разрывах соединения
)

def init_db() -> None:
    # Импортируем модели, чтобы они зарегистрировались в метаданных перед create_all
    from app.db import models  # noqa: F401
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
