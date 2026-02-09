from io import BytesIO
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.db.models import Dataset
from app.db.session import get_session
from app.schemas.datasets import DatasetRead, DatasetUpdate
from app.core.io.excel_exporter import export_dataset_to_excel_bytes
from app.core.io.excel_loader import load_dataset_from_excel_bytes

router = APIRouter(prefix="/datasets")


@router.post("/upload", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def upload_dataset_excel(
    name: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> Dataset:
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    content = file.file.read()
    try:
        payload = load_dataset_from_excel_bytes(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    dataset = Dataset(name=name, payload=payload)
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset


@router.get("", response_model=List[DatasetRead])
def list_datasets(session: Session = Depends(get_session)) -> List[Dataset]:
    datasets = session.exec(select(Dataset).order_by(Dataset.created_at.desc())).all()
    return datasets


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, session: Session = Depends(get_session)) -> Dataset:
    dataset = session.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset


@router.get("/{dataset_id}/excel")
def download_dataset_excel(
    dataset_id: int, session: Session = Depends(get_session)
):
    dataset = session.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    content = export_dataset_to_excel_bytes(dataset.payload)
    filename = f"dataset_{dataset.id}.xlsx"
    return StreamingResponse(
        BytesIO(content),
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.put("/{dataset_id}", response_model=DatasetRead)
def update_dataset(
    dataset_id: int,
    payload: DatasetUpdate,
    session: Session = Depends(get_session),
) -> Dataset:
    dataset = session.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    if payload.name is not None:
        dataset.name = payload.name
    if payload.payload is not None:
        dataset.payload = payload.payload

    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset
