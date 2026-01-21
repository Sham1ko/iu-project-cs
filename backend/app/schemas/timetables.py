from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import SQLModel

from app.db.models import GenerationStatus


class GenerationRequest(SQLModel):
    dataset_id: Optional[int] = None
    params: Optional[Dict[str, Any]] = None


class GenerationResponse(SQLModel):
    run_id: int
    status: GenerationStatus


class GenerationRunRead(SQLModel):
    id: int
    status: GenerationStatus
    progress: int
    params: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    dataset_id: Optional[int]
