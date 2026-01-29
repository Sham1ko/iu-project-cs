from __future__ import annotations

import logging

from sqlmodel import Session, select

from app.config import get_settings
from app.db.models import Dataset
from app.core.io.data_service import DataService

logger = logging.getLogger(__name__)


def ensure_seed_dataset(session: Session) -> None:
    existing = session.exec(select(Dataset.id)).first()
    if existing is not None:
        return

    settings = get_settings()
    data_service = DataService(data_dir=settings.data_dir)
    payload = {
        "subjects": data_service.load_subjects(),
        "teachers": data_service.load_teachers(),
        "classes": data_service.load_classes(),
        "meta": {
            "source": "data/*.json",
            "teachers_file": data_service.teachers_file,
        },
    }

    dataset = Dataset(name="default", payload=payload)
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    logger.info("Seed dataset created id=%s", dataset.id)
