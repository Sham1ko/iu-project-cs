# IU Project - Timetable Generator

A full stack timetable generator based on a genetic algorithm (GA).

This repo contains:

- `backend/app/core/` - GA engine and data loaders
- `backend/` - FastAPI API + SQLModel + Postgres
- `frontend/` - React UI (Vite + TypeScript)
- `data/` - sample input data and generated schedules
- `docs/` - simple documentation (architecture, logic, deployment)

## Quick start

Prereqs: Python 3.11+, Node 18+, Docker.

### Option A: Docker (all services)

Prereqs: Docker.

1. Create env file (repo root)

```
cp .env.example .env
```

2. Update `DATA_DIR` in `.env`

The example uses a Windows path; set a valid local path or delete `DATA_DIR`
to use the default `./data`.

3. Build and run everything

```
docker compose up --build
```

Optional: enable Compose Watch (auto-sync/rebuild on file changes)

```
docker compose up --watch
```

Open http://localhost:5173 (frontend) and http://localhost:8000 (backend).

### Option B: Local dev (backend + frontend)

Prereqs: Python 3.11+, Node 18+, Docker.

1. Start Postgres only

```
docker compose up -d db
```

2. Create env file (repo root)

```
cp .env.example .env
```

3. Update `DATA_DIR` in `.env`

The example uses a Windows path; set a valid local path or delete `DATA_DIR`
to use the default `./data`.

4. Run backend

```
cd backend
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload
```

5. Run frontend

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Environment variables

Repo `.env` (root):

- `DATABASE_URL` (preferred)
- or `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`
- `DATA_DIR` (optional path to `data/`, defaults to `./data`; update the
  Windows example if you copy `.env.example`)
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
PYTHONPATH=backend python -m app.core.main
```

## Docs

- `docs/architecture.md`
- `docs/backend.md`
- `docs/frontend.md`
- `docs/core.md`
- `docs/logic.md`
- `docs/deployment.md`
- `docs/CSV_GUIDE.md`
