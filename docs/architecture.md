# Architecture

## High level

- Frontend (React) calls the backend API.
- Backend creates a GenerationRun and schedules GA execution in the background.
- Core GA produces a timetable payload that is stored in Postgres as JSONB.

## Components

- UI: `frontend/` (Generate + Datasets pages)
- API: `backend/app/api/routers`
- Services: `backend/app/services`
- Storage: Postgres with SQLModel models
- GA engine: `core/`

## Data flow

1) Client calls `POST /api/v1/timetables/generate`.
2) Backend inserts GenerationRun with status `queued`.
3) Background task sets `running`, invokes core GA, stores result.
4) Status is updated to `done` or `failed`.
5) Client polls status and fetches result when ready.
