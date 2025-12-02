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
    Create a random schedule (chromosome).
    Structure: {day: {lesson: {class_id: (teacher_id, subject_id) or None}}}
    This version avoids teacher conflicts during initialization.
    """
    schedule: Dict[str, Dict[int, Dict[Any, Optional[Tuple[Any, Any]]]]] = {}

    for day in days:
        schedule[day] = {}
        for lesson in range(1, lessons_per_day + 1):
            schedule[day][lesson] = {}

            # Track which teachers are already assigned in this time slot
            assigned_teachers = set()

            for cls in classes:
                # Randomly decide if this slot has a lesson (70% chance)
                if random.random() < 0.7:
                    # Pick a random subject
                    subject = random.choice(subjects)
                    # Get teachers who can teach this subject
                    available_teachers = teachers_by_subject.get(subject["id"], [])

                    # Filter out teachers who are already assigned in this slot
                    free_teachers = [
                        t
                        for t in available_teachers
                        if t["id"] not in assigned_teachers
                    ]

                    if free_teachers:
                        teacher = random.choice(free_teachers)
                        schedule[day][lesson][cls["id"]] = (
                            teacher["id"],
                            subject["id"],
                        )
                        assigned_teachers.add(teacher["id"])
                    else:
                        # No available teacher, leave slot empty
                        schedule[day][lesson][cls["id"]] = None
                else:
                    schedule[day][lesson][cls["id"]] = None

    # Bias: ensure at least 2 lessons per day per class where possible
    for cls in classes:
        class_id = cls["id"]
        for day in days:
            # count current lessons for this class/day
            current_lessons = [
                lesson_num
                for lesson_num in range(1, lessons_per_day + 1)
                if schedule[day][lesson_num].get(class_id) is not None
            ]
            missing = max(0, 2 - len(current_lessons))
            if missing <= 0:
                continue
            # Try to add up to 'missing' lessons in free/feasible slots
            tries = 0
            while missing > 0 and tries < lessons_per_day * 2:
                tries += 1
                slot = random.randint(1, lessons_per_day)
                if schedule[day][slot].get(class_id) is not None:
                    continue  # already has lesson
                # pick a random subject
                subject = random.choice(subjects)
                available_teachers = teachers_by_subject.get(subject["id"], [])
                # find teacher not already assigned in this slot
                teacher_in_slot = {
                    tup[0]
                    for tup in [
                        v for v in schedule[day][slot].values() if v is not None
                    ]
                }
                free_teachers = [
                    t for t in available_teachers if t["id"] not in teacher_in_slot
                ]
                if not free_teachers:
                    continue
                teacher = random.choice(free_teachers)
                schedule[day][slot][class_id] = (teacher["id"], subject["id"])
                missing -= 1

    return schedule
