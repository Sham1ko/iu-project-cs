from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import SQLModel


class DatasetCreate(SQLModel):
    name: str
    payload: Dict[str, Any]


class DatasetRead(SQLModel):
    id: int
    name: str
    payload: Dict[str, Any]
    created_at: datetime


class DatasetUpdate(SQLModel):
    name: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
