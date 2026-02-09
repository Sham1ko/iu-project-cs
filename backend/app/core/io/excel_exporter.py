from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Iterable, List

from openpyxl import Workbook


def _coerce_weekly_hours(subject: Dict[str, Any]) -> int | None:
    hours = subject.get("weekly_hours")
    if hours is not None:
        return int(hours)
    hours_by_grade = subject.get("weekly_hours_by_grade")
    if isinstance(hours_by_grade, dict) and hours_by_grade:
        values = {int(v) for v in hours_by_grade.values() if v is not None}
        if len(values) == 1:
            return next(iter(values))
    return None


def _join_subjects(subjects: Iterable[Any]) -> str:
    return ",".join(str(item) for item in subjects if item is not None)


def export_dataset_to_excel_bytes(payload: Dict[str, Any]) -> bytes:
    subjects: List[Dict[str, Any]] = payload.get("subjects") or []
    teachers: List[Dict[str, Any]] = payload.get("teachers") or []
    classes: List[Dict[str, Any]] = payload.get("classes") or []

    wb = Workbook()

    ws_subjects = wb.active
    ws_subjects.title = "subjects"
    ws_subjects.append(["id", "name", "weekly_hours"])
    for subject in subjects:
        ws_subjects.append(
            [
                subject.get("id"),
                subject.get("name"),
                _coerce_weekly_hours(subject),
            ]
        )

    ws_teachers = wb.create_sheet("teachers")
    ws_teachers.append(["id", "name", "subjects", "max_weekly_hours"])
    for teacher in teachers:
        ws_teachers.append(
            [
                teacher.get("id"),
                teacher.get("name"),
                _join_subjects(teacher.get("subjects", [])),
                teacher.get("max_weekly_hours"),
            ]
        )

    ws_classes = wb.create_sheet("classes")
    ws_classes.append(["id", "name", "grade"])
    for cls in classes:
        ws_classes.append([cls.get("id"), cls.get("name"), cls.get("grade")])

    output = BytesIO()
    wb.save(output)
    return output.getvalue()
