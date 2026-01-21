import csv
import json
from pathlib import Path
from typing import Any, Dict, List

from core.ga.fitness_metrics import (
    count_teacher_conflicts,
    count_teacher_gaps,
    count_total_lessons,
)


def _generate_statistics(
    schedule: Dict,
    days: List[str],
    lessons_per_day: int,
    teachers_by_id: Dict[int, Dict[str, Any]],
    teachers: List[Dict[str, Any]],
    classes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total_lessons = count_total_lessons(schedule, days, lessons_per_day)
    teacher_conflicts = count_teacher_conflicts(
        schedule, teachers_by_id, days, lessons_per_day
    )
    teacher_gaps = count_teacher_gaps(schedule, teachers, days, lessons_per_day)
    return {
        "total_lessons": total_lessons,
        "teacher_conflicts": teacher_conflicts,
        "teacher_gaps": teacher_gaps,
    }


def export_schedule_json(
    schedule: Dict,
    fitness: float,
    generation: int,
    output_path: str,
    *,
    days: List[str],
    lessons_per_day: int,
    classes_by_id: Dict[int, Dict[str, Any]],
    teachers_by_id: Dict[int, Dict[str, Any]],
    subjects_by_id: Dict[int, Dict[str, Any]],
    teachers: List[Dict[str, Any]],
    classes: List[Dict[str, Any]],
) -> None:
    """
    Export schedule to a readable JSON file with basic statistics.
    """
    output = {
        "schedule": {},
        "fitness_score": round(fitness, 2),
        "generation": generation,
        "statistics": _generate_statistics(
            schedule, days, lessons_per_day, teachers_by_id, teachers, classes
        ),
    }
    for day in days:
        output["schedule"][day] = {}
        for lesson in range(1, lessons_per_day + 1):
            output["schedule"][day][str(lesson)] = {}
            for class_id, assignment in schedule[day][lesson].items():
                class_name = classes_by_id[class_id]["name"]
                if assignment is not None:
                    teacher_id, subject_id = assignment
                    teacher_name = teachers_by_id[teacher_id]["name"]
                    subject_name = subjects_by_id[subject_id]["name"]
                    output["schedule"][day][str(lesson)][class_name] = {
                        "teacher": teacher_name,
                        "subject": subject_name,
                    }
                else:
                    output["schedule"][day][str(lesson)][class_name] = None
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path_obj, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSchedule saved to: {output_path_obj}")


def export_to_csv(
    schedule: Dict,
    output_dir: str,
    *,
    days: List[str],
    lessons_per_day: int,
    teachers: List[Dict[str, Any]],
    classes: List[Dict[str, Any]],
    teachers_by_id: Dict[int, Dict[str, Any]],
    subjects_by_id: Dict[int, Dict[str, Any]],
    classes_by_id: Dict[int, Dict[str, Any]],
) -> None:
    """
    Export schedule to CSV:
      - Full schedule across all days
      - Per-day CSVs
      - Per-class CSVs
      - Teacher schedule CSV
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Full schedule
    _export_full_schedule_csv(
        schedule,
        output_path / "schedule_full.csv",
        days,
        lessons_per_day,
        classes,
        teachers_by_id,
        subjects_by_id,
    )
    # 2. Per-day
    _export_per_day_csv(
        schedule,
        output_path,
        days,
        lessons_per_day,
        classes,
        teachers_by_id,
        subjects_by_id,
    )
    # 3. Per-class
    _export_per_class_csv(
        schedule,
        output_path,
        days,
        lessons_per_day,
        classes,
        teachers_by_id,
        subjects_by_id,
    )
    # 4. Teacher schedule
    _export_teacher_schedule_csv(
        schedule,
        output_path / "schedule_teachers.csv",
        days,
        lessons_per_day,
        teachers,
        classes_by_id,
        subjects_by_id,
    )

    print(f"\nCSV files saved to: {output_path}/")
    print("  - schedule_full.csv (complete overview)")
    print("  - schedule_monday.csv to schedule_friday.csv (daily)")
    print("  - schedule_class_*.csv (per class)")
    print("  - schedule_teachers.csv (teacher schedules)")


def _export_full_schedule_csv(
    schedule: Dict,
    filepath: Path,
    days: List[str],
    lessons_per_day: int,
    classes: List[Dict[str, Any]],
    teachers_by_id: Dict[int, Dict[str, Any]],
    subjects_by_id: Dict[int, Dict[str, Any]],
) -> None:
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        header = ["Class"]
        for day in days:
            for lesson in range(1, lessons_per_day + 1):
                header.append(f"{day[:3]} {lesson}")
        writer.writerow(header)
        for cls in classes:
            row = [cls["name"]]
            for day in days:
                for lesson in range(1, lessons_per_day + 1):
                    assignment = schedule[day][lesson].get(cls["id"])
                    if assignment is not None:
                        teacher_id, subject_id = assignment
                        teacher_name = teachers_by_id[teacher_id]["name"]
                        subject_name = subjects_by_id[subject_id]["name"]
                        cell = f"{subject_name} ({teacher_name})"
                    else:
                        cell = ""
                    row.append(cell)
            writer.writerow(row)


def _export_per_day_csv(
    schedule: Dict,
    output_dir: Path,
    days: List[str],
    lessons_per_day: int,
    classes: List[Dict[str, Any]],
    teachers_by_id: Dict[int, Dict[str, Any]],
    subjects_by_id: Dict[int, Dict[str, Any]],
) -> None:
    for day in days:
        filepath = output_dir / f"schedule_{day.lower()}.csv"
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            header = ["Class"] + [f"Lesson {i}" for i in range(1, lessons_per_day + 1)]
            writer.writerow(header)
            for cls in classes:
                row = [cls["name"]]
                for lesson in range(1, lessons_per_day + 1):
                    assignment = schedule[day][lesson].get(cls["id"])
                    if assignment is not None:
                        teacher_id, subject_id = assignment
                        teacher_name = teachers_by_id[teacher_id]["name"]
                        subject_name = subjects_by_id[subject_id]["name"]
                        cell = f"{subject_name}\n{teacher_name}"
                    else:
                        cell = "-"
                    row.append(cell)
                writer.writerow(row)


def _export_per_class_csv(
    schedule: Dict,
    output_dir: Path,
    days: List[str],
    lessons_per_day: int,
    classes: List[Dict[str, Any]],
    teachers_by_id: Dict[int, Dict[str, Any]],
    subjects_by_id: Dict[int, Dict[str, Any]],
) -> None:
    for cls in classes:
        filepath = output_dir / f"schedule_class_{cls['name']}.csv"
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            header = ["Lesson"] + days
            writer.writerow(header)
            for lesson in range(1, lessons_per_day + 1):
                row = [f"Lesson {lesson}"]
                for day in days:
                    assignment = schedule[day][lesson].get(cls["id"])
                    if assignment is not None:
                        teacher_id, subject_id = assignment
                        teacher_name = teachers_by_id[teacher_id]["name"]
                        subject_name = subjects_by_id[subject_id]["name"]
                        cell = f"{subject_name}\n{teacher_name}"
                    else:
                        cell = "-"
                    row.append(cell)
                writer.writerow(row)


def _export_teacher_schedule_csv(
    schedule: Dict,
    filepath: Path,
    days: List[str],
    lessons_per_day: int,
    teachers: List[Dict[str, Any]],
    classes_by_id: Dict[int, Dict[str, Any]],
    subjects_by_id: Dict[int, Dict[str, Any]],
) -> None:
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        header = ["Teacher"]
        for day in days:
            for lesson in range(1, lessons_per_day + 1):
                header.append(f"{day[:3]} {lesson}")
        writer.writerow(header)
        for teacher in teachers:
            row = [teacher["name"]]
            for day in days:
                for lesson in range(1, lessons_per_day + 1):
                    teaching = None
                    for class_id, assignment in schedule[day][lesson].items():
                        if assignment is not None and assignment[0] == teacher["id"]:
                            class_name = classes_by_id[class_id]["name"]
                            subject_name = subjects_by_id[assignment[1]]["name"]
                            teaching = f"{subject_name} ({class_name})"
                            break
                    row.append(teaching if teaching else "")
            writer.writerow(row)
