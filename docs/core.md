# Core GA

The genetic algorithm lives in `backend/app/core/` and is used directly by the backend.

## Key modules

- `backend/app/core/ga/genetic_scheduler.py` provides `GeneticScheduler`.
- `backend/app/core/io/data_service.py` loads classes, teachers, and subjects.
- `backend/app/core/export/pdf_exporter.py` formats results (PDF).
- `backend/app/core/timetable_generation.py` exposes `generate_timetable` for API runs.

## Core dependencies

Python 3.11 is the primary implementation language, chosen for clarity and for
its solid ecosystem around web APIs and data handling. The project relies on the
following core libraries:

- FastAPI: HTTP API layer.
- Pydantic / pydantic-settings: settings and payload validation.
- SQLModel + SQLAlchemy: ORM and database access.
- psycopg: PostgreSQL driver.
- Uvicorn: ASGI server for local development.
- ReportLab: PDF generation for schedules.
- openpyxl: Excel dataset ingestion (`.xlsx`).

## How it is called

The backend uses `backend/app/core/timetable_generation.py`:

- `DataService(payload=...)` for in-memory datasets
- `GeneticScheduler.generate_schedule(verbose=False)`

The generator normalizes the output into a JSON payload with statistics and can export a PDF.
