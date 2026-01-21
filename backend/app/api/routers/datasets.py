from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db.models import Dataset
from app.db.session import get_session
from app.schemas.datasets import DatasetCreate, DatasetRead, DatasetUpdate

router = APIRouter(prefix="/datasets")


@router.post("", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: DatasetCreate, session: Session = Depends(get_session)
) -> Dataset:
    dataset = Dataset(name=payload.name, payload=payload.payload)
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
