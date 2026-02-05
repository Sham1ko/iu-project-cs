# Excel Dataset Input

The backend can load datasets from an Excel file (`.xlsx`). This is optional and
is used only when `DATA_EXCEL_FILE` is set (or when `data/dataset.xlsx` exists).

## Expected workbook structure

Your workbook must contain three sheets:

- `subjects`
- `teachers`
- `classes`

Sheet names are case-insensitive. The first row in each sheet is the header.

### subjects sheet

Required columns:

- `id` (optional, integer; auto-assigned if missing)
- `name` (required)
- `weekly_hours` (optional, integer; curriculum hours per week)

Example:

| id | name |
| --- | --- |
| 1 | Math |
| 2 | English |

### classes sheet

Required columns:

- `id` (optional, integer; auto-assigned if missing)
- `name` (required)
- `grade` (required, integer)

Example:

| id | name | grade |
| --- | --- | --- |
| 1 | 5A | 5 |
| 2 | 5B | 5 |

### teachers sheet

Required columns:

- `id` (optional, integer; auto-assigned if missing)
- `name` (required)
- `subjects` (required)
- `max_weekly_hours` (optional, integer; capacity per week)

`subjects` can be:

- Comma/semicolon separated subject **IDs** (e.g., `1,3,5`)
- A single subject **name** that matches the `subjects` sheet (e.g., `Math`)
- Space-separated numeric IDs (e.g., `1 3 5`)

Example:

| id | name | subjects |
| --- | --- | --- |
| 1 | John Doe | 1,2 |
| 2 | Jane Doe | Math |

## Configuration

Set the environment variable:

```
DATA_EXCEL_FILE=dataset.xlsx
```

If the path is relative, it is resolved against `DATA_DIR`.
