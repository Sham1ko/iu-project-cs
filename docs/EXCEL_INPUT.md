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

## Format B (matrix-based, by class/group)

This format is useful when you store weekly hours directly per class/group and
teacher eligibility per group.

Required sheets:

- `hours`
- `teachers`

### hours sheet

Recommended columns:

- `ID` (optional)
- `Subject name` (required)
- one column per class/group (e.g., `9A`, `9B`, `10A`, ...)

Each class/group cell is the weekly hours for that subject and class.

Example:

| ID | Subject name | 9A | 9B | 10A |
| --- | --- | --- | --- | --- |
| 1 | Algebra | 4 | 4 | 4 |
| 2 | Geometry | 4 | 4 | 4 |

### teachers sheet

Required columns:

- `ID` (optional)
- `name` (required)
- `subjects` (required)
- `groups` (required for group-specific teachers)
- `max_hours` or `max_weekly_hours` (optional)

`subjects` supports:

- comma/semicolon lists (`1,2`)
- dot-separated numeric values (`1.2`) for locale-specific Excel input
- subject names (if they match `Subject name`)

`groups` is a comma/semicolon-separated list of class names (`9A, 10A, 11A`) or class ids.

## Legacy matrix variant

The older variant with `hours` by grade (`9`, `10`, `11`) + one sheet per subject is still supported.

## Configuration

Set the environment variable:

```
DATA_EXCEL_FILE=dataset.xlsx
```

If the path is relative, it is resolved against `DATA_DIR`. Alternatively, place
`dataset.xlsx` directly inside `DATA_DIR` (default is `./data`).
