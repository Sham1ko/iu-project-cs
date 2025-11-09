from typing import Dict, List, Tuple, Any


def count_teacher_conflicts(
    schedule: Dict,
    teachers_by_id: Dict[int, Dict[str, Any]],
    days: List[str],
    lessons_per_day: int,
) -> int:
    """Count how many times a teacher has to be in two places at once or teaches a subject they don't handle."""
    conflicts = 0
    for day in days:
        for lesson in range(1, lessons_per_day + 1):
            teacher_assignments: Dict[int, int] = {}
            for class_id, assignment in schedule[day][lesson].items():
                if assignment is None:
                    continue
                teacher_id, subject_id = assignment

                teacher = teachers_by_id[teacher_id]
                if subject_id not in teacher["subjects"]:
                    conflicts += 1  # Wrong subject for teacher

                if teacher_id in teacher_assignments:
                    conflicts += 1  # Teacher conflict (double-booked)
                else:
                    teacher_assignments[teacher_id] = class_id
    return conflicts


def count_teacher_gaps(
    schedule: Dict,
    teachers: List[Dict[str, Any]],
    days: List[str],
    lessons_per_day: int,
) -> int:
    """Count gaps (free lessons between classes) in teacher schedules."""
    gaps = 0
    for teacher in teachers:
        teacher_id = teacher["id"]
        for day in days:
            lessons_taught: List[int] = []
            for lesson in range(1, lessons_per_day + 1):
                for class_id, assignment in schedule[day][lesson].items():
                    if assignment is not None and assignment[0] == teacher_id:
                        lessons_taught.append(lesson)
                        break
            if len(lessons_taught) > 1:
                lessons_taught.sort()
                for i in range(len(lessons_taught) - 1):
                    gap = lessons_taught[i + 1] - lessons_taught[i] - 1
                    gaps += gap
    return gaps


def count_class_gaps(
    schedule: Dict,
    classes: List[Dict[str, Any]],
    days: List[str],
    lessons_per_day: int,
) -> int:
    """Count gaps (free lessons) in class schedules."""
    gaps = 0
    for cls in classes:
        class_id = cls["id"]
        for day in days:
            lessons: List[int] = []
            for lesson in range(1, lessons_per_day + 1):
                if schedule[day][lesson].get(class_id) is not None:
                    lessons.append(lesson)
            if len(lessons) > 1:
                lessons.sort()
                for i in range(len(lessons) - 1):
                    gap = lessons[i + 1] - lessons[i] - 1
                    gaps += gap
    return gaps


def count_early_gaps(
    schedule: Dict,
    classes: List[Dict[str, Any]],
    days: List[str],
    lessons_per_day: int,
) -> int:
    """Count empty slots before the first lesson of the day for each class."""
    early_gaps = 0
    for cls in classes:
        class_id = cls["id"]
        for day in days:
            first_lesson = None
            for lesson in range(1, lessons_per_day + 1):
                if schedule[day][lesson].get(class_id) is not None:
                    first_lesson = lesson
                    break
            if first_lesson is not None and first_lesson > 1:
                early_gaps += (first_lesson - 1)
    return early_gaps


def calculate_daily_imbalance(
    schedule: Dict,
    classes: List[Dict[str, Any]],
    days: List[str],
    lessons_per_day: int,
) -> float:
    """Calculate how unevenly lessons are distributed across days (sum of per-class std dev)."""
    imbalance = 0.0
    for cls in classes:
        class_id = cls["id"]
        daily_counts: List[int] = []
        for day in days:
            count = sum(
                1
                for lesson in range(1, lessons_per_day + 1)
                if schedule[day][lesson].get(class_id) is not None
            )
            daily_counts.append(count)
        if daily_counts:
            mean = sum(daily_counts) / len(daily_counts)
            variance = sum((x - mean) ** 2 for x in daily_counts) / len(daily_counts)
            imbalance += variance ** 0.5
    return imbalance


def count_total_lessons(
    schedule: Dict,
    days: List[str],
    lessons_per_day: int,
) -> int:
    """Count total number of lessons in the schedule."""
    count = 0
    for day in days:
        for lesson in range(1, lessons_per_day + 1):
            for class_id, assignment in schedule[day][lesson].items():
                if assignment is not None:
                    count += 1
    return count


