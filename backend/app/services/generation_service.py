from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Session, select

from app.core_ga_adapter.adapter import generate_timetable
from app.db import session as db_session
from app.db.models import Dataset, GenerationRun, GenerationStatus, TimetableResult

logger = logging.getLogger(__name__)


def _resolve_dataset_id(session: Session, dataset_id: Optional[int]) -> int:
    if dataset_id is not None:
        dataset = session.get(Dataset, dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} not found.")
        return dataset.id

    dataset = session.exec(select(Dataset).order_by(Dataset.created_at.desc())).first()
    if dataset is None:
        raise ValueError("No datasets available.")
    return dataset.id


def start_generation(
    session: Session, dataset_id: Optional[int], params: Optional[Dict[str, Any]]
) -> GenerationRun:
    resolved_dataset_id = _resolve_dataset_id(session, dataset_id)
    run = GenerationRun(
        status=GenerationStatus.queued,
        progress=0,
        params=params,
        dataset_id=resolved_dataset_id,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    logger.info("Generation queued run_id=%s dataset_id=%s", run.id, run.dataset_id)
    return run


def run_generation(run_id: int) -> None:
    logger.info("Generation started run_id=%s", run_id)
    try:
        with Session(db_session.engine) as session:
            run = session.get(GenerationRun, run_id)
            if run is None:
                logger.error("Generation run not found run_id=%s", run_id)
                return

            run.status = GenerationStatus.running
            run.progress = 5
            run.started_at = datetime.utcnow()
            session.add(run)
            session.commit()

            dataset = session.get(Dataset, run.dataset_id) if run.dataset_id else None
            if dataset is None:
                raise ValueError("Dataset not found for run.")

            config: Dict[str, Any] = {}
            if isinstance(run.params, dict):
                config.update(run.params)
            config["run_id"] = run_id

            start_time = time.perf_counter()
            result_payload = generate_timetable(dataset.payload, config)
            duration = time.perf_counter() - start_time

            run.progress = 90
            session.add(run)
            session.commit()

            result = TimetableResult(run_id=run.id, payload=result_payload)
            session.add(result)

            run.status = GenerationStatus.done
            run.progress = 100
            run.finished_at = datetime.utcnow()
            session.add(run)
            session.commit()

            logger.info(
                "Generation finished run_id=%s duration=%.2fs",
                run_id,
                duration,
            )
    except Exception as exc:
        logger.exception("Generation failed run_id=%s error=%s", run_id, exc)
        with Session(db_session.engine) as session:
            run = session.get(GenerationRun, run_id)
            if run is not None:
                run.status = GenerationStatus.failed
                run.error_message = str(exc)
                run.finished_at = datetime.utcnow()
                session.add(run)
                session.commit()
