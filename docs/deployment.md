# Deployment

This project is set up for local development first. Use these steps for a simple local run.

## Local Postgres

```
cd backend
docker compose up -d
```

## Backend

```
cd backend
cp .env.example .env
uvicorn app.main:app --reload
```

## Frontend

```
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Production notes

- Use a managed Postgres or Docker Compose with persistent volumes.
- Run the backend with a process manager (e.g., systemd or container runtime).
- Set `VITE_API_BASE_URL` to the backend public URL during frontend build.
