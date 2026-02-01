# Core GA

The genetic algorithm lives in `backend/app/core/` and is used directly by the backend.

## Key modules

- `backend/app/core/ga/genetic_scheduler.py` provides `GeneticScheduler`.
- `backend/app/core/io/data_service.py` loads classes, teachers, and subjects.
- `backend/app/core/export/schedule_exporter.py` formats results (JSON/PDF).
- `backend/app/core/timetable_generation.py` exposes `generate_timetable` for API runs.

## How it is called

The backend uses `backend/app/core/timetable_generation.py`:

- `DataService(payload=...)` for in-memory datasets
- `GeneticScheduler.generate_schedule(verbose=False)`

The generator normalizes the output into a JSON payload with statistics and can export a PDF.
