from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db.models import GenerationRun, GenerationStatus, TimetableResult
from app.db.session import get_session
from app.schemas.timetables import GenerationRequest, GenerationResponse, GenerationRunRead
from app.services.generation_service import run_generation, start_generation

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
