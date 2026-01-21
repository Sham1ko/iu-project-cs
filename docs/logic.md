# Logic

This document explains the timetable generation flow and state changes.

## Generation state machine

- queued -> running -> done
- queued -> running -> failed

## Service flow

1) `start_generation` creates a GenerationRun with status `queued`.
2) Background task `run_generation` sets status `running` and progress `5`.
3) The dataset payload is passed to the core GA adapter.
4) On success, TimetableResult is stored and status becomes `done` with progress `100`.
5) On error, status becomes `failed` with `error_message`.

## Result access

- If a run is not `done`, the result endpoint returns HTTP 409.
- If a run has failed, the error message is returned in the status endpoint.
