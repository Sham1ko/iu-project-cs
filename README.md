# IU Project - Timetable Generator

A full stack timetable generator based on a genetic algorithm (GA).

This repo contains:

- `core/` - GA engine and data loaders
- `backend/` - FastAPI API + SQLModel + Postgres
- `frontend/` - React UI (Vite + TypeScript)
- `data/` - sample input data and generated schedules
- `docs/` - simple documentation (architecture, logic, deployment)

## Quick start (local)

Prereqs: Python 3.11+, Node 18+, Docker.

1. Start Postgres

```
cd backend
docker compose up -d
```

2. Run backend

```
cd backend
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

3. Run frontend

```
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173

## Environment variables

Backend (`backend/.env`):

- `DATABASE_URL` (preferred)
- or `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`
- `DATA_DIR` (path to `data/`)

Frontend (`frontend/.env`):

- `VITE_API_BASE_URL` (example: `http://localhost:8000`)

## API endpoints

- `POST /api/v1/timetables/generate`
- `GET  /api/v1/timetables/runs/{run_id}`
- `GET  /api/v1/timetables/runs/{run_id}/result`
- `GET/POST/PUT /api/v1/datasets`

On startup, the backend seeds a default Dataset from `data/*.json` if the datasets
table is empty.

## Manual check (curl)

```
# create dataset
curl -s -X POST http://localhost:8000/api/v1/datasets \
  -H "Content-Type: application/json" \
  -d '{"name":"demo","payload":{"subjects":[],"teachers":[],"classes":[]}}'

# generate run
curl -s -X POST http://localhost:8000/api/v1/timetables/generate \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "params": {"generations": 50}}'

# check status
curl -s http://localhost:8000/api/v1/timetables/runs/1

# get result
curl -s http://localhost:8000/api/v1/timetables/runs/1/result
```

## Optional: run core GA directly

```
python -m core.main
```

## Docs

- `docs/architecture.md`
- `docs/backend.md`
- `docs/frontend.md`
- `docs/core.md`
- `docs/logic.md`
- `docs/deployment.md`
