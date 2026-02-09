from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from openpyxl import load_workbook


_SHEET_ALIASES = {
    "subjects": ("subjects", "subject"),
    "teachers": ("teachers", "teacher"),
    "classes": ("classes", "class"),
    "hours": ("hours", "hour"),
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


def _find_sheet_by_name(workbook, target: str):
    target_norm = target.strip().lower()
    for sheet_name in workbook.sheetnames:
        if sheet_name.strip().lower() == target_norm:
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


def _parse_hours_sheet(hours_ws) -> tuple[List[Dict[str, Any]], List[int]]:
    rows = list(hours_ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Excel sheet 'hours' is empty.")

    header = list(rows[0])
    grade_headers: List[int] = []
    for cell in header[1:]:
        grade = _parse_optional_int(cell)
        if grade is None:
            continue
        grade_headers.append(grade)

    if not grade_headers:
        raise ValueError("Excel sheet 'hours' must define grade headers in row 1.")

    subjects: List[Dict[str, Any]] = []
    next_id = 1
    for row in rows[1:]:
        if not row or (row[0] is None or str(row[0]).strip() == ""):
            continue
        name = str(row[0]).strip()
        hours_by_grade: Dict[int, int] = {}
        for idx, grade in enumerate(grade_headers, start=1):
            value = row[idx] if idx < len(row) else None
            hours = _parse_optional_int(value)
            if hours is None:
                continue
            hours_by_grade[int(grade)] = int(hours)
        subject = {"id": next_id, "name": name, "weekly_hours_by_grade": hours_by_grade}
        if hours_by_grade and len(set(hours_by_grade.values())) == 1:
            subject["weekly_hours"] = next(iter(hours_by_grade.values()))
        subjects.append(subject)
        next_id += 1
    return subjects, grade_headers


def _parse_matrix_format(workbook) -> Dict[str, List[Dict[str, Any]]]:
    hours_ws = _find_sheet(workbook, "hours")
    if hours_ws is None:
        raise ValueError("Excel file does not contain required 'hours' sheet.")

    subjects, _ = _parse_hours_sheet(hours_ws)
    subject_name_to_id = {s["name"].lower(): s["id"] for s in subjects}

    classes_map: Dict[str, Dict[str, Any]] = {}
    teachers_map: Dict[str, Dict[str, Any]] = {}

    for subject in subjects:
        subject_name = subject["name"]
        subject_ws = _find_sheet_by_name(workbook, subject_name)
        if subject_ws is None:
            continue

        rows = list(subject_ws.iter_rows(values_only=True))
        if not rows:
            continue

        header = rows[0]
        class_names = []
        for cell in header[1:]:
            if cell is None or str(cell).strip() == "":
                continue
            class_name = str(cell).strip()
            class_names.append(class_name)
            if class_name not in classes_map:
                match = re.match(r"^(\\d+)", class_name)
                if not match:
                    raise ValueError(
                        f"Class '{class_name}' must start with a numeric grade (e.g., 9A)."
                    )
                grade = int(match.group(1))
                classes_map[class_name] = {
                    "id": len(classes_map) + 1,
                    "name": class_name,
                    "grade": grade,
                }

        for row in rows[1:]:
            if not row:
                continue
            teacher_name = row[0]
            if teacher_name is None or str(teacher_name).strip() == "":
                continue
            teacher_name = str(teacher_name).strip()
            if teacher_name not in teachers_map:
                teachers_map[teacher_name] = {
                    "id": len(teachers_map) + 1,
                    "name": teacher_name,
                    "subjects": [],
                }
            teacher_entry = teachers_map[teacher_name]
            subject_id = subject_name_to_id[subject_name.lower()]
            if subject_id not in teacher_entry["subjects"]:
                teacher_entry["subjects"].append(subject_id)

    return {
        "subjects": subjects,
        "classes": list(classes_map.values()),
        "teachers": list(teachers_map.values()),
    }


def load_dataset_from_excel(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    workbook = load_workbook(filename=path, data_only=True)

    subjects_ws = _find_sheet(workbook, "subjects")
    classes_ws = _find_sheet(workbook, "classes")
    teachers_ws = _find_sheet(workbook, "teachers")

    if subjects_ws and classes_ws and teachers_ws:
        subjects_rows = _iter_rows(subjects_ws)
        classes_rows = _iter_rows(classes_ws)
        teachers_rows = _iter_rows(teachers_ws)

        subjects = _parse_subjects(subjects_rows)
        classes = _parse_classes(classes_rows)
        subject_name_to_id = {s["name"].lower(): s["id"] for s in subjects}
        teachers = _parse_teachers(teachers_rows, subject_name_to_id)

        return {"subjects": subjects, "classes": classes, "teachers": teachers}

    hours_ws = _find_sheet(workbook, "hours")
    if hours_ws is not None:
        return _parse_matrix_format(workbook)

    raise ValueError(
        "Excel file must contain either sheets named: subjects, classes, teachers "
        "or the matrix format with an 'hours' sheet and subject sheets."
    )
