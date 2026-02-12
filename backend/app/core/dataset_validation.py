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


def _normalize_class_name(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", "", text.strip())
    return text.lower()


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


def _parse_teacher_groups(
    teacher: Dict[str, Any],
    *,
    class_id_by_name: Dict[str, int],
    errors: List[str],
) -> set[int] | None:
    groups = teacher.get("groups")
    if not isinstance(groups, list) or not groups:
        return None

    allowed: set[int] = set()
    for group in groups:
        class_id = _coerce_int(group)
        if class_id is not None:
            allowed.add(class_id)
            continue
        class_name = _normalize_class_name(group)
        if class_name in class_id_by_name:
            allowed.add(class_id_by_name[class_name])
            continue
        errors.append(
            f"Teacher '{teacher.get('name', 'unknown')}' references unknown group '{group}'."
        )
    return allowed


def _required_classes_for_subject(
    subject_id: int,
    *,
    class_ids: set[int],
    class_by_id: Dict[int, Dict[str, Any]],
    subject_hours: Dict[int, int],
    subject_hours_by_grade: Dict[int, Dict[int, int]],
    subject_hours_by_class: Dict[int, Dict[int, int]],
) -> set[int]:
    if subject_id in subject_hours_by_class:
        return {
            class_id
            for class_id, hours in subject_hours_by_class[subject_id].items()
            if hours > 0
        }
    if subject_id in subject_hours_by_grade:
        required: set[int] = set()
        by_grade = subject_hours_by_grade[subject_id]
        for class_id in class_ids:
            cls = class_by_id.get(class_id)
            if cls is None:
                continue
            grade = _coerce_int(cls.get("grade"))
            if grade is None:
                continue
            if by_grade.get(int(grade), 0) > 0:
                required.add(class_id)
        return required
    if subject_id in subject_hours:
        return set(class_ids)
    return set(class_ids)


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

    class_by_id: Dict[int, Dict[str, Any]] = {}
    class_id_by_name: Dict[str, int] = {}
    class_ids: set[int] = set()

    # Validate class grades
    for cls in classes:
        class_id = _coerce_int(cls.get("id"))
        if class_id is not None:
            class_by_id[class_id] = cls
            class_ids.add(class_id)

        class_name = cls.get("name")
        if class_name is not None and str(class_name).strip():
            normalized = _normalize_class_name(class_name)
            if normalized:
                if normalized in class_id_by_name:
                    warnings.append(
                        f"Class name '{class_name}' is duplicated in normalized form."
                    )
                elif class_id is not None:
                    class_id_by_name[normalized] = class_id

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

    teacher_subject_ids: Dict[int, set[int]] = {}
    teacher_allowed_classes: Dict[int, set[int] | None] = {}

    for idx, teacher in enumerate(teachers):
        subject_set: set[int] = set()
        for subject_id in teacher.get("subjects", []) or []:
            subject_id_int = _coerce_int(subject_id)
            if subject_id_int is not None:
                subject_set.add(subject_id_int)
        teacher_subject_ids[idx] = subject_set
        teacher_allowed_classes[idx] = _parse_teacher_groups(
            teacher, class_id_by_name=class_id_by_name, errors=errors
        )

    # Teacher coverage per subject
    teachers_per_subject: defaultdict[int, List[Dict[str, Any]]] = defaultdict(list)
    for idx, teacher in enumerate(teachers):
        for subject_id_int in teacher_subject_ids[idx]:
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
    subject_hours_by_class: Dict[int, Dict[int, int]] = {}
    used_hour_keys: set[str] = set()
    has_hours_column = False

    for subject in subjects:
        subject_id = _coerce_int(subject.get("id"))
        if subject_id is None:
            continue

        hours_by_class = subject.get("weekly_hours_by_class")
        if isinstance(hours_by_class, dict) and hours_by_class:
            has_hours_column = True
            parsed_class_hours: Dict[int, int] = {}
            for class_key, value in hours_by_class.items():
                class_id = _coerce_int(class_key)
                if class_id is None:
                    class_id = class_id_by_name.get(_normalize_class_name(class_key))
                if class_id is None or class_id not in class_ids:
                    errors.append(
                        f"Subject '{subject.get('name', subject_id)}' has unknown class key {class_key}."
                    )
                    continue
                hours = _coerce_int(value)
                if hours is None:
                    errors.append(
                        f"Subject '{subject.get('name', subject_id)}' has empty curriculum hours for class {class_key}."
                    )
                    continue
                if hours <= 0:
                    errors.append(
                        f"Subject '{subject.get('name', subject_id)}' has invalid hours {hours} for class {class_key}."
                    )
                    continue
                parsed_class_hours[int(class_id)] = int(hours)
            if parsed_class_hours:
                subject_hours_by_class[subject_id] = parsed_class_hours
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

    # Ensure each required class-subject combination has a qualified teacher.
    for subject in subjects:
        subject_id = _coerce_int(subject.get("id"))
        if subject_id is None:
            continue

        required_class_ids = _required_classes_for_subject(
            subject_id,
            class_ids=class_ids,
            class_by_id=class_by_id,
            subject_hours=subject_hours,
            subject_hours_by_grade=subject_hours_by_grade,
            subject_hours_by_class=subject_hours_by_class,
        )

        for class_id in sorted(required_class_ids):
            class_name = class_by_id.get(class_id, {}).get("name", f"id {class_id}")
            has_qualified = False
            for idx, _teacher in enumerate(teachers):
                if subject_id not in teacher_subject_ids[idx]:
                    continue
                allowed_classes = teacher_allowed_classes[idx]
                if allowed_classes is not None and class_id not in allowed_classes:
                    continue
                has_qualified = True
                break
            if not has_qualified:
                errors.append(
                    f"No qualified teacher for subject '{subject.get('name', subject_id)}' in class '{class_name}'."
                )

    # Workload feasibility (only strict if hours provided)
    if (subject_hours or subject_hours_by_grade or subject_hours_by_class) and classes:
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
            required_class_ids = _required_classes_for_subject(
                subject_id,
                class_ids=class_ids,
                class_by_id=class_by_id,
                subject_hours=subject_hours,
                subject_hours_by_grade=subject_hours_by_grade,
                subject_hours_by_class=subject_hours_by_class,
            )

            if subject_id in subject_hours_by_class:
                demand = sum(subject_hours_by_class[subject_id].values())
            elif subject_id in subject_hours_by_grade:
                demand = 0
                for grade, hours in subject_hours_by_grade[subject_id].items():
                    demand += hours * classes_by_grade.get(int(grade), 0)
            elif subject_id in subject_hours:
                demand = subject_hours[subject_id] * len(classes)
            else:
                continue
            qualified_teachers = []
            for idx, teacher in enumerate(teachers):
                if subject_id not in teacher_subject_ids[idx]:
                    continue
                allowed_classes = teacher_allowed_classes[idx]
                if allowed_classes is not None and not (
                    allowed_classes & required_class_ids
                ):
                    continue
                qualified_teachers.append(teacher)
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
