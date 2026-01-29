# Core GA

The genetic algorithm lives in `backend/app/core/` and is used by the backend adapter.

## Key modules

- `backend/app/core/ga/genetic_scheduler.py` provides `GeneticScheduler`.
- `backend/app/core/io/data_service.py` loads classes, teachers, and subjects.
- `backend/app/core/export/schedule_exporter.py` formats results (JSON/CSV/PDF).

## How it is called

The backend adapter (`backend/app/core_ga_adapter/adapter.py`) uses:

- `DictDataService` (in-memory payload)
- `GeneticScheduler.generate_schedule(verbose=False)`

The adapter normalizes the output into a JSON payload with statistics.
