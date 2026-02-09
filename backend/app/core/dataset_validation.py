from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

_SUBJECT_HOUR_KEYS = ("weekly_hours", "hours_per_week", "hours")
_TEACHER_MAX_HOUR_KEYS = ("max_weekly_hours", "max_hours", "weekly_hours")


def _normalize_name(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text.strip())
    return text.lower()


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if text == "":
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _check_duplicate_ids(
    items: Iterable[Dict[str, Any]], label: str, errors: List[str]
) -> None:
    seen: set[int] = set()
    for item in items:
        raw_id = item.get("id")
        item_id = _coerce_int(raw_id)
        if item_id is None:
            errors.append(f"{label} has missing or invalid id: {raw_id!r}.")
            continue
        if item_id in seen:
            errors.append(f"{label} has duplicate id: {item_id}.")
        seen.add(item_id)


def _check_duplicate_names(
    items: Iterable[Dict[str, Any]],
    label: str,
    errors: List[str],
    warnings: List[str],
) -> None:
    normalized: defaultdict[str, List[str]] = defaultdict(list)
    for item in items:
        raw_name = item.get("name")
        if raw_name is None or str(raw_name).strip() == "":
            errors.append(f"{label} has missing name.")
            continue
        normalized[_normalize_name(raw_name)].append(str(raw_name).strip())

    for norm, variants in normalized.items():
        unique_variants = sorted(set(variants))
        if len(variants) > 1 and len(unique_variants) == 1:
            warnings.append(f"{label} has duplicate name: '{unique_variants[0]}'.")
        elif len(unique_variants) > 1:
            warnings.append(
                f"{label} has inconsistent naming variants: {', '.join(unique_variants)}."
            )


def _extract_subject_hours(subject: Dict[str, Any]) -> Tuple[bool, int | None, str | None]:
    for key in _SUBJECT_HOUR_KEYS:
        if key in subject:
            value = subject.get(key)
            hours = _coerce_int(value)
            return True, hours, key
    return False, None, None


def _extract_teacher_max_hours(teacher: Dict[str, Any]) -> int | None:
    for key in _TEACHER_MAX_HOUR_KEYS:
        if key in teacher:
            return _coerce_int(teacher.get(key))
    return None


def validate_dataset_payload(
    payload: Dict[str, Any],
    *,
    days_per_week: int = 5,
    lessons_per_day: int = 6,
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    subjects = payload.get("subjects") or []
    teachers = payload.get("teachers") or []
    classes = payload.get("classes") or []

    if not subjects:
        errors.append("Dataset has no subjects.")
    if not teachers:
        errors.append("Dataset has no teachers.")
    if not classes:
        errors.append("Dataset has no classes.")

    _check_duplicate_ids(subjects, "Subject", errors)
    _check_duplicate_ids(teachers, "Teacher", errors)
    _check_duplicate_ids(classes, "Class", errors)

    _check_duplicate_names(teachers, "Teacher", errors, warnings)
    _check_duplicate_names(classes, "Class", errors, warnings)

    # Validate class grades
    for cls in classes:
        grade = _coerce_int(cls.get("grade"))
        if grade is None:
            errors.append(f"Class '{cls.get('name', 'unknown')}' has invalid grade.")
            continue
        if grade <= 0:
            errors.append(
                f"Class '{cls.get('name', 'unknown')}' has non-positive grade {grade}."
            )
        if grade > 12:
            warnings.append(
                f"Class '{cls.get('name', 'unknown')}' has atypical grade {grade}."
            )

    # Teacher coverage per subject (required subjects assumed to be all subjects)
    teachers_per_subject: defaultdict[int, List[Dict[str, Any]]] = defaultdict(list)
    for teacher in teachers:
        for subject_id in teacher.get("subjects", []) or []:
            subject_id_int = _coerce_int(subject_id)
            if subject_id_int is not None:
                teachers_per_subject[subject_id_int].append(teacher)

    subjects_without_teachers = []
    for subject in subjects:
        subject_id = _coerce_int(subject.get("id"))
        if subject_id is None:
            continue
        if not teachers_per_subject.get(subject_id):
            subjects_without_teachers.append(subject.get("name", f"id {subject_id}"))

    if subjects_without_teachers:
        errors.append(
            "No qualified teacher for required subjects: "
            + ", ".join(subjects_without_teachers)
            + "."
        )

    # Curriculum hours validation (optional)
    subject_hours: Dict[int, int] = {}
    subject_hours_by_grade: Dict[int, Dict[int, int]] = {}
    used_hour_keys: set[str] = set()
    has_hours_column = False

    for subject in subjects:
        subject_id = _coerce_int(subject.get("id"))
        if subject_id is None:
            continue

        hours_by_grade = subject.get("weekly_hours_by_grade")
        if isinstance(hours_by_grade, dict) and hours_by_grade:
            has_hours_column = True
            parsed: Dict[int, int] = {}
            for grade_key, value in hours_by_grade.items():
                grade = _coerce_int(grade_key)
                hours = _coerce_int(value)
                if grade is None:
                    errors.append(
                        f"Subject '{subject.get('name', subject_id)}' has invalid grade key {grade_key}."
                    )
                    continue
                if hours is None:
                    errors.append(
                        f"Subject '{subject.get('name', subject_id)}' has empty curriculum hours for grade {grade}."
                    )
                    continue
                if hours <= 0:
                    errors.append(
                        f"Subject '{subject.get('name', subject_id)}' has invalid hours {hours} for grade {grade}."
                    )
                    continue
                parsed[int(grade)] = int(hours)
            if parsed:
                subject_hours_by_grade[subject_id] = parsed
            continue

        present, hours, key = _extract_subject_hours(subject)
        if present:
            has_hours_column = True
            if key:
                used_hour_keys.add(key)
        if present:
            if hours is None:
                errors.append(
                    f"Subject '{subject.get('name', subject_id)}' has empty curriculum hours."
                )
            elif hours <= 0:
                errors.append(
                    f"Subject '{subject.get('name', subject_id)}' has invalid hours {hours}."
                )
            else:
                subject_hours[subject_id] = hours

    if has_hours_column and len(used_hour_keys) > 1:
        warnings.append(
            "Subjects use mixed hour columns: " + ", ".join(sorted(used_hour_keys)) + "."
        )
    if not has_hours_column:
        warnings.append(
            "Curriculum hours not provided; workload feasibility checks are approximate."
        )

    # Workload feasibility (only strict if hours provided)
    if (subject_hours or subject_hours_by_grade) and classes:
        total_slots = days_per_week * lessons_per_day
        classes_by_grade: Dict[int, int] = defaultdict(int)
        for cls in classes:
            grade = _coerce_int(cls.get("grade"))
            if grade is None:
                continue
            classes_by_grade[int(grade)] += 1

        for subject in subjects:
            subject_id = _coerce_int(subject.get("id"))
            if subject_id is None:
                continue
            if subject_id in subject_hours_by_grade:
                demand = 0
                for grade, hours in subject_hours_by_grade[subject_id].items():
                    demand += hours * classes_by_grade.get(int(grade), 0)
            elif subject_id in subject_hours:
                demand = subject_hours[subject_id] * len(classes)
            else:
                continue
            qualified_teachers = teachers_per_subject.get(subject_id, [])
            if not qualified_teachers:
                continue
            capacity = 0
            for teacher in qualified_teachers:
                max_hours = _extract_teacher_max_hours(teacher)
                capacity += max_hours if max_hours is not None else total_slots
            if demand > capacity:
                errors.append(
                    f"Subject '{subject.get('name', subject_id)}' demand "
                    f"{demand} exceeds teacher capacity {capacity}."
                )
            elif demand > capacity * 0.9:
                warnings.append(
                    f"Subject '{subject.get('name', subject_id)}' demand "
                    f"{demand} is close to capacity {capacity}."
                )

    return errors, warnings
