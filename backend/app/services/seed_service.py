from __future__ import annotations

import logging
from pathlib import Path

from sqlmodel import Session, select

from app.config import ROOT_DIR, get_settings
from app.core.io.excel_loader import load_dataset_from_excel
from app.db.models import Dataset

logger = logging.getLogger(__name__)


def _resolve_excel_path(data_dir: Path, excel_file: str | None) -> Path:
    if not excel_file:
        return data_dir / "dataset.xlsx"

    candidate = Path(excel_file)
    if candidate.is_absolute():
        return candidate
    return data_dir / candidate


def _collect_seed_excel_files(data_dir: Path, excel_file: str | None) -> list[Path]:
    primary = _resolve_excel_path(data_dir, excel_file)
    fallback_root = ROOT_DIR / "dataset.xlsx"
    all_from_data_dir = sorted(data_dir.glob("*.xlsx")) if data_dir.exists() else []

    ordered = [primary, fallback_root, *all_from_data_dir]
    unique_existing: list[Path] = []
    seen: set[Path] = set()
    for path in ordered:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            unique_existing.append(resolved)
    return unique_existing


def _build_dataset_name(path: Path, used_names: set[str], is_first: bool) -> str:
    if is_first:
        base = "default"
    else:
        base = path.stem.strip() or "dataset"

    name = base
    index = 2
    while name in used_names:
        name = f"{base}-{index}"
        index += 1
    return name


def ensure_seed_dataset(session: Session) -> None:
    existing = session.exec(select(Dataset.id)).first()
    if existing is not None:
        return

    settings = get_settings()
    data_dir = Path(settings.data_dir)
    excel_files = _collect_seed_excel_files(data_dir, settings.data_excel_file)
    if not excel_files:
        raise FileNotFoundError(
            "No Excel files found for seed dataset. "
            "Place dataset.xlsx in DATA_DIR or set DATA_EXCEL_FILE."
        )

    used_names: set[str] = set()
    created_ids: list[int] = []

    for idx, excel_path in enumerate(excel_files):
        payload = load_dataset_from_excel(excel_path)
        payload["meta"] = {"source": str(excel_path)}
        name = _build_dataset_name(excel_path, used_names, is_first=(idx == 0))
        used_names.add(name)
        session.add(Dataset(name=name, payload=payload))

    session.commit()

    created = session.exec(select(Dataset).order_by(Dataset.id.asc())).all()
    for ds in created:
        if ds.id is not None:
            created_ids.append(ds.id)

    logger.info("Seed datasets created count=%s ids=%s", len(created_ids), created_ids)
