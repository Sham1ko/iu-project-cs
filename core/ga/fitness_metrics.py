from typing import Any, Dict, List


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
            imbalance += variance**0.5
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


def count_min_daily_lessons_deficit(
    schedule: Dict,
    classes: List[Dict[str, Any]],
    days: List[str],
    lessons_per_day: int,
    min_lessons_per_day: int = 2,
) -> int:
    """
    Count how many lessons are missing to reach min_lessons_per_day for each class and day.
    Example: if a class has 0 lessons on a day and min=2 -> deficit 2.
    """
    deficit = 0
    for cls in classes:
        class_id = cls["id"]
        for day in days:
            day_count = 0
            for lesson in range(1, lessons_per_day + 1):
                if schedule[day][lesson].get(class_id) is not None:
                    day_count += 1
            if day_count < min_lessons_per_day:
                deficit += min_lessons_per_day - day_count
    return deficit


def calculate_schedule_fitness(
    schedule: Dict,
    *,
    days: List[str],
    lessons_per_day: int,
    teachers: List[Dict[str, Any]],
    classes: List[Dict[str, Any]],
    teachers_by_id: Dict[int, Dict[str, Any]],
    min_lessons_per_day: int = 2,
) -> float:
    """
    Calculate fitness score for a schedule.
    Higher score = better schedule.
    Score is reduced by penalties for constraint violations.
    """
    score = 1000.0  # Start with perfect score

    # Hard constraint penalties
    teacher_conflicts = count_teacher_conflicts(
        schedule, teachers_by_id, days, lessons_per_day
    )
    score -= teacher_conflicts * 100  # Heavy penalty for teacher conflicts

    # Soft constraint penalties
    teacher_gaps = count_teacher_gaps(schedule, teachers, days, lessons_per_day)
    score -= teacher_gaps * 2  # Penalty for teacher gaps

    imbalance = calculate_daily_imbalance(schedule, classes, days, lessons_per_day)
    score -= imbalance * 1  # Penalty for uneven distribution

    # Bonus for having lessons
    total_lessons = count_total_lessons(schedule, days, lessons_per_day)
    score += total_lessons * 0.5  # Small bonus for each lesson

    # Hard-ish constraint: minimum lessons per day for each class
    min_daily_deficit = count_min_daily_lessons_deficit(
        schedule,
        classes,
        days,
        lessons_per_day,
        min_lessons_per_day=min_lessons_per_day,
    )
    score -= min_daily_deficit * 80  # Heavy penalty per missing lesson toward minimum

    return max(0, score)  # Ensure non-negative score
