# Frontend

This folder describes the React UI that talks to the FastAPI backend.

## Stack

- React + TypeScript
- Vite dev server
- ESLint + Prettier

## Key files

- `frontend/src/config.ts` reads `VITE_API_BASE_URL` from env.
- `frontend/src/api` contains the typed API client.
- `frontend/src/pages/GeneratePage.tsx` handles run creation + polling.
- `frontend/src/pages/DatasetsPage.tsx` shows dataset list + create form.

## Environment

Create `frontend/.env` with:

```
VITE_API_BASE_URL=http://localhost:8000
```

In dev, Vite proxies `/api` to this base URL, so the UI can call `/api/v1/...`.

## UI flow

- Generate page sends `POST /api/v1/timetables/generate`.
- It polls `GET /api/v1/timetables/runs/{run_id}` every ~1.5s.
- When status is `done`, it fetches `GET /api/v1/timetables/runs/{run_id}/result`.
- Errors are shown inline.
