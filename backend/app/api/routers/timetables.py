from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app.db.models import Dataset, GenerationRun, GenerationStatus, TimetableResult
from app.db.session import get_session
from app.schemas.timetables import (
    GenerationRequest,
    GenerationResponse,
    GenerationRunListItem,
    GenerationRunRead,
)
from app.services.generation_service import run_generation, start_generation
from app.services.run_files import get_run_pdf_path

router = APIRouter(prefix="/timetables")


@router.post(
    "/generate",
    response_model=GenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_timetable(
    payload: GenerationRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> GenerationResponse:
    try:
        run = start_generation(session, payload.dataset_id, payload.params)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    background_tasks.add_task(run_generation, run.id)
    return GenerationResponse(run_id=run.id, status=run.status)


@router.get("/runs/{run_id}", response_model=GenerationRunRead)
def get_run_status(run_id: int, session: Session = Depends(get_session)) -> GenerationRun:
    run = session.get(GenerationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return run


@router.get("/runs", response_model=list[GenerationRunListItem])
def list_runs(session: Session = Depends(get_session)):
    rows = session.exec(
        select(GenerationRun, Dataset.name)
        .join(Dataset, Dataset.id == GenerationRun.dataset_id, isouter=True)
        .order_by(GenerationRun.created_at.desc())
    ).all()
    items: list[GenerationRunListItem] = []
    for run, dataset_name in rows:
        items.append(
            GenerationRunListItem(
                id=run.id,
                status=run.status,
                created_at=run.created_at,
                finished_at=run.finished_at,
                dataset_id=run.dataset_id,
                dataset_name=dataset_name,
                has_pdf=get_run_pdf_path(run.id).exists(),
            )
        )
    return items


@router.get("/runs/{run_id}/result")
def get_run_result(run_id: int, session: Session = Depends(get_session)):
    run = session.get(GenerationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    if run.status != GenerationStatus.done:
        detail = (
            f"Result not ready. Status={run.status}."
            if run.status != GenerationStatus.failed
            else f"Run failed: {run.error_message or 'unknown error'}."
        )
        raise HTTPException(status_code=409, detail=detail)

    result = session.exec(
        select(TimetableResult).where(TimetableResult.run_id == run_id)
    ).first()
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found.")
    return result.payload


@router.get("/runs/{run_id}/pdf")
def get_run_pdf(run_id: int):
    pdf_path = get_run_pdf_path(run_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found.")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"schedule_{run_id}.pdf",
    )


@router.delete("/runs/{run_id}/pdf", status_code=status.HTTP_204_NO_CONTENT)
def delete_run_pdf(run_id: int):
    pdf_path = get_run_pdf_path(run_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found.")
    pdf_path.unlink()
    try:
        parent = pdf_path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    except OSError:
        pass
    return None


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: int, session: Session = Depends(get_session)):
    run = session.get(GenerationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    result = session.exec(
        select(TimetableResult).where(TimetableResult.run_id == run_id)
    ).first()
    if result is not None:
        session.delete(result)

    session.delete(run)
    session.commit()

    pdf_path = get_run_pdf_path(run_id)
    if pdf_path.exists():
        pdf_path.unlink()
    try:
        parent = pdf_path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    except OSError:
        pass

    return None
