import random
from typing import Any, Dict, List, Optional, Tuple


def initialize_population(
    population_size: int,
    classes: List[Dict[str, Any]],
    subjects: List[Dict[str, Any]],
    teachers_by_subject: Dict[Any, List[Dict[str, Any]]],
    days: List[str],
    lessons_per_day: int,
) -> List[Dict[str, Any]]:
    """
    Initialize genetic algorithm population with random schedules.
    """
    population: List[Dict[str, Any]] = []

    for _ in range(population_size):
        schedule = create_random_schedule(
            classes,
            subjects,
            teachers_by_subject,
            days,
            lessons_per_day,
        )
        population.append(schedule)

    return population


def create_random_schedule(
    classes: List[Dict[str, Any]],
    subjects: List[Dict[str, Any]],
    teachers_by_subject: Dict[Any, List[Dict[str, Any]]],
    days: List[str],
    lessons_per_day: int,
) -> Dict[str, Dict[int, Dict[Any, Optional[Tuple[Any, Any]]]]]:
    """
    Create a random schedule (chromosome) with contiguous lessons per class/day.
    Structure: {day: {lesson: {class_id: (teacher_id, subject_id) or None}}}
    """
    schedule: Dict[str, Dict[int, Dict[Any, Optional[Tuple[Any, Any]]]]] = {}
    assigned_teachers: Dict[str, Dict[int, set[int]]] = {}

    for day in days:
        schedule[day] = {}
        assigned_teachers[day] = {}
        for lesson in range(1, lessons_per_day + 1):
            schedule[day][lesson] = {}
            assigned_teachers[day][lesson] = set()
            for cls in classes:
                schedule[day][lesson][cls["id"]] = None

    for cls in classes:
        class_id = cls["id"]
        for day in days:
            desired_lessons = sum(
                1 for _ in range(lessons_per_day) if random.random() < 0.7
            )
            desired_lessons = min(desired_lessons, lessons_per_day)
            slot = 1
            placed = 0

            while placed < desired_lessons and slot <= lessons_per_day:
                assignment = _assign_compact_lesson(
                    day,
                    slot,
                    subjects,
                    teachers_by_subject,
                    assigned_teachers,
                )

                if assignment is None:
                    break

                schedule[day][slot][class_id] = assignment
                assigned_teachers[day][slot].add(assignment[0])
                placed += 1
                slot += 1

    for cls in classes:
        class_id = cls["id"]
        for day in days:
            current_lessons = [
                lesson_num
                for lesson_num in range(1, lessons_per_day + 1)
                if schedule[day][lesson_num].get(class_id) is not None
            ]
            missing = max(0, 2 - len(current_lessons))
            if missing <= 0:
                continue

            next_slot = len(current_lessons) + 1
            while missing > 0 and next_slot <= lessons_per_day:
                if schedule[day][next_slot].get(class_id) is not None:
                    next_slot += 1
                    continue

                assignment = _assign_compact_lesson(
                    day,
                    next_slot,
                    subjects,
                    teachers_by_subject,
                    assigned_teachers,
                )

                if assignment is None:
                    break

                schedule[day][next_slot][class_id] = assignment
                assigned_teachers[day][next_slot].add(assignment[0])
                missing -= 1
                next_slot += 1

    return schedule


def _assign_compact_lesson(
    day: str,
    lesson: int,
    subjects: List[Dict[str, Any]],
    teachers_by_subject: Dict[Any, List[Dict[str, Any]]],
    assigned_teachers: Dict[str, Dict[int, set[int]]],
) -> Optional[Tuple[Any, Any]]:
    """
    Try to place a lesson at the specific day/lesson ensuring no teacher conflicts.
    """
    shuffled_subjects = subjects[:]
    random.shuffle(shuffled_subjects)

    for subject in shuffled_subjects:
        available_teachers = teachers_by_subject.get(subject["id"], [])
        if not available_teachers:
            continue

        free_teachers = [
            t
            for t in available_teachers
            if t["id"] not in assigned_teachers[day][lesson]
        ]
        if not free_teachers:
            continue

        teacher = random.choice(free_teachers)
        return teacher["id"], subject["id"]

    return None
