# Excel Dataset Input

The backend loads datasets from an Excel file (`.xlsx`) when running from the
filesystem. JSON input files are not used for loading datasets.

## Expected workbook structure

Your workbook can use one of two formats.

Format A (table-based) with three sheets:

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

## Format B (matrix-based)

This format is useful when you store hours by grade and list teachers per subject.

Required sheets:

- `hours`
- One sheet per subject (sheet name must match the subject name)

### hours sheet

Row 1 contains grade headers (e.g., `9`, `10`, `11`). Column A contains subject names.
Each cell is the weekly hours for that subject and grade.

Example:

|   | 9 | 10 | 11 |
| --- | --- | --- | --- |
| Algebra | 4 | 4 | 4 |
| Geometry | 4 | 4 | 4 |

### subject sheets (e.g., `Algebra`)

Row 1 contains class names (e.g., `9A`, `9B`, `10A`). Column A contains teacher names.
Teachers listed on the sheet are treated as qualified to teach that subject. The
matrix cells are currently ignored by the loader.

## Configuration

Set the environment variable:

```
DATA_EXCEL_FILE=dataset.xlsx
```

If the path is relative, it is resolved against `DATA_DIR`. Alternatively, place
`dataset.xlsx` directly inside `DATA_DIR` (default is `./data`).
