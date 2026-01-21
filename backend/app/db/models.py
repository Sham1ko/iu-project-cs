from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class GenerationStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class Dataset(SQLModel, table=True):
    __tablename__ = "datasets"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    payload: Dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GenerationRun(SQLModel, table=True):
    __tablename__ = "generation_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    status: GenerationStatus = Field(
        sa_column=Column(String, nullable=False),
        default=GenerationStatus.queued,
    )
    progress: int = Field(default=0)
    params: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    dataset_id: Optional[int] = Field(default=None, foreign_key="datasets.id")


class TimetableResult(SQLModel, table=True):
    __tablename__ = "timetable_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("generation_runs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        )
    )
    payload: Dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
