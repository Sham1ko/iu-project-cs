from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from openpyxl import load_workbook


_SHEET_ALIASES = {
    "subjects": ("subjects", "subject"),
    "teachers": ("teachers", "teacher"),
    "classes": ("classes", "class"),
}


def _normalize_header(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _iter_rows(ws) -> List[Dict[str, Any]]:
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [_normalize_header(value) for value in rows[0]]
    output: List[Dict[str, Any]] = []
    for raw in rows[1:]:
        if raw is None:
            continue
        if all(cell is None or str(cell).strip() == "" for cell in raw):
            continue
        row: Dict[str, Any] = {}
        for idx, header in enumerate(headers):
            if not header:
                continue
            value = raw[idx] if idx < len(raw) else None
            row[header] = value
        output.append(row)
    return output


def _find_sheet(workbook, kind: str):
    aliases = _SHEET_ALIASES[kind]
    for sheet_name in workbook.sheetnames:
        normalized = sheet_name.strip().lower()
        if normalized in aliases:
            return workbook[sheet_name]
    return None


def _ensure_columns(rows: Iterable[Dict[str, Any]], required: Iterable[str], sheet: str) -> None:
    required_set = set(required)
    if not rows:
        raise ValueError(f"Excel sheet '{sheet}' is empty or missing required rows.")
    available = set(rows[0].keys())
    missing = [col for col in required_set if col not in available]
    if missing:
        raise ValueError(
            f"Excel sheet '{sheet}' is missing required columns: {', '.join(missing)}."
        )


def _parse_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if text == "":
        return None
    return int(float(text))


def _parse_subjects(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    _ensure_columns(rows, ["name"], "subjects")
    subjects: List[Dict[str, Any]] = []
    next_id = 1
    for row in rows:
        name = row.get("name")
        if name is None or str(name).strip() == "":
            raise ValueError("Subjects sheet requires a non-empty 'name' value.")
        subject_id = _parse_optional_int(row.get("id"))
        if subject_id is None:
            subject_id = next_id
        next_id = max(next_id, subject_id + 1)
        subject: Dict[str, Any] = {"id": subject_id, "name": str(name).strip()}
        for key in ("weekly_hours", "hours_per_week", "hours"):
            if key in row:
                subject["weekly_hours"] = _parse_optional_int(row.get(key))
                break
        subjects.append(subject)
    return subjects


def _parse_classes(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    _ensure_columns(rows, ["name", "grade"], "classes")
    classes: List[Dict[str, Any]] = []
    next_id = 1
    for row in rows:
        name = row.get("name")
        grade = row.get("grade")
        if name is None or str(name).strip() == "":
            raise ValueError("Classes sheet requires a non-empty 'name' value.")
        if grade is None or str(grade).strip() == "":
            raise ValueError("Classes sheet requires a non-empty 'grade' value.")
        class_id = _parse_optional_int(row.get("id"))
        if class_id is None:
            class_id = next_id
        next_id = max(next_id, class_id + 1)
        classes.append(
            {
                "id": class_id,
                "name": str(name).strip(),
                "grade": int(float(grade)),
            }
        )
    return classes


def _parse_subject_list(value: Any, subject_name_to_id: Dict[str, int]) -> List[int]:
    if value is None:
        return []
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [int(value)]

    text = str(value).strip()
    if text == "":
        return []

    if re.search(r"[;,]", text):
        parts = re.split(r"[;,]", text)
    else:
        tokens = text.split()
        if len(tokens) > 1 and all(token.isdigit() for token in tokens):
            parts = tokens
        else:
            parts = [text]

    subject_ids: List[int] = []
    for part in parts:
        cleaned = part.strip()
        if cleaned == "":
            continue
        if cleaned.isdigit():
            subject_ids.append(int(cleaned))
            continue
        key = cleaned.lower()
        if key not in subject_name_to_id:
            raise ValueError(f"Unknown subject '{cleaned}' in teachers sheet.")
        subject_ids.append(subject_name_to_id[key])

    return subject_ids


def _parse_teachers(
    rows: List[Dict[str, Any]], subject_name_to_id: Dict[str, int]
) -> List[Dict[str, Any]]:
    _ensure_columns(rows, ["name", "subjects"], "teachers")
    teachers: List[Dict[str, Any]] = []
    next_id = 1
    for row in rows:
        name = row.get("name")
        if name is None or str(name).strip() == "":
            raise ValueError("Teachers sheet requires a non-empty 'name' value.")
        teacher_id = _parse_optional_int(row.get("id"))
        if teacher_id is None:
            teacher_id = next_id
        next_id = max(next_id, teacher_id + 1)
        subjects = _parse_subject_list(row.get("subjects"), subject_name_to_id)
        teacher: Dict[str, Any] = {
            "id": teacher_id,
            "name": str(name).strip(),
            "subjects": subjects,
        }
        for key in ("max_weekly_hours", "max_hours", "weekly_hours"):
            if key in row:
                teacher["max_weekly_hours"] = _parse_optional_int(row.get(key))
                break
        teachers.append(teacher)
    return teachers


def load_dataset_from_excel(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    workbook = load_workbook(filename=path, data_only=True)

    subjects_ws = _find_sheet(workbook, "subjects")
    classes_ws = _find_sheet(workbook, "classes")
    teachers_ws = _find_sheet(workbook, "teachers")

    missing_sheets = [
        name
        for name, ws in (
            ("subjects", subjects_ws),
            ("classes", classes_ws),
            ("teachers", teachers_ws),
        )
        if ws is None
    ]
    if missing_sheets:
        raise ValueError(
            "Excel file must contain sheets named: subjects, classes, teachers. "
            f"Missing: {', '.join(missing_sheets)}."
        )

    subjects_rows = _iter_rows(subjects_ws)
    classes_rows = _iter_rows(classes_ws)
    teachers_rows = _iter_rows(teachers_ws)

    subjects = _parse_subjects(subjects_rows)
    classes = _parse_classes(classes_rows)
    subject_name_to_id = {s["name"].lower(): s["id"] for s in subjects}
    teachers = _parse_teachers(teachers_rows, subject_name_to_id)

    return {"subjects": subjects, "classes": classes, "teachers": teachers}
