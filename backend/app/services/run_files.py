from pathlib import Path

from app.config import get_settings


def get_runs_dir() -> Path:
    settings = get_settings()
    return Path(settings.data_dir) / "runs"


def get_run_pdf_path(run_id: int) -> Path:
    return get_runs_dir() / f"schedule_{run_id}.pdf"
