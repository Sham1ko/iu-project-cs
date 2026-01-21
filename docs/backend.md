# Backend

FastAPI backend that manages timetable generation and persistence.

## Stack

- FastAPI
- SQLModel (Postgres)
- BackgroundTasks for async generation

## Key folders

- `backend/app/api` API routers
- `backend/app/services` service layer
- `backend/app/db` models and session
- `backend/app/core_ga_adapter` core GA integration

## Configuration

`backend/.env` example:

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/iu_project
DATA_DIR=/path/to/data
```

If `DATABASE_URL` is missing, it is built from `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`.

## Database

- Tables are created automatically on startup with `SQLModel.metadata.create_all`.
- JSONB is used for dataset payloads and results.

## Main endpoints

- `POST /api/v1/timetables/generate`
- `GET  /api/v1/timetables/runs/{run_id}`
- `GET  /api/v1/timetables/runs/{run_id}/result`
- `GET/POST/PUT /api/v1/datasets`

## Seed data

On startup, a default Dataset is inserted from `data/*.json` if the datasets table is empty.
