import json
from pathlib import Path
from typing import Any, Dict, List

from ..ga.fitness_metrics import (
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
