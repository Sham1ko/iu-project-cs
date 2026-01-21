from fastapi import APIRouter

from app.api.routers import datasets, timetables

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(datasets.router, tags=["datasets"])
api_router.include_router(timetables.router, tags=["timetables"])
