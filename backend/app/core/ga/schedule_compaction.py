import copy
import random
from typing import Dict, List, Tuple, Any


def compact_mutation(
    schedule: Dict,
    days: List[str],
    lessons_per_day: int,
    classes: List[Dict[str, Any]],
) -> Dict:
    """
    Compact mutation: shift lessons to the start of the day for random classes and days.
    Mirrors GeneticScheduler._compact_mutation but without class dependencies.
    """
    mutated = copy.deepcopy(schedule)

    num_classes = random.randint(2, min(5, len(classes)))
    selected_classes = random.sample(classes, num_classes)

    for cls in selected_classes:
        class_id = cls["id"]

        num_days = random.randint(2, min(4, len(days)))
        selected_days = random.sample(days, num_days)

        for day in selected_days:
            lessons_data: List[Tuple[int, Tuple[int, int]]] = []
            for lesson in range(1, lessons_per_day + 1):
                assignment = mutated[day][lesson].get(class_id)
                if assignment is not None:
                    lessons_data.append((lesson, assignment))

            if lessons_data:
                for lesson in range(1, lessons_per_day + 1):
                    mutated[day][lesson][class_id] = None

                new_lesson = 1
                for original_lesson, assignment in lessons_data:
                    teacher_id, _ = assignment

                    placed = False
                    for slot in range(new_lesson, lessons_per_day + 1):
                        teacher_busy = False
                        for _, other_assignment in mutated[day][slot].items():
                            if other_assignment is not None and other_assignment[0] == teacher_id:
                                teacher_busy = True
                                break

                        if not teacher_busy:
                            mutated[day][slot][class_id] = assignment
                            new_lesson = slot + 1
                            placed = True
                            break

                    if not placed:
                        mutated[day][original_lesson][class_id] = assignment

    return mutated


def compact_schedule_full(
    schedule: Dict,
    days: List[str],
    lessons_per_day: int,
    classes: List[Dict[str, Any]],
) -> Dict:
    """
    Fully compact the schedule: remove gaps for all classes on all days using multiple passes.
    Mirrors GeneticScheduler._compact_schedule_full.
    """
    compacted = copy.deepcopy(schedule)

    for _ in range(3):  # multiple passes
        improved = False

        for cls in classes:
            class_id = cls["id"]

            for day in days:
                lessons_data: List[Tuple[int, Tuple[int, int]]] = []
                for lesson in range(1, lessons_per_day + 1):
                    assignment = compacted[day][lesson].get(class_id)
                    if assignment is not None:
                        lessons_data.append((lesson, assignment))

                if not lessons_data:
                    continue

                lesson_numbers = [l for l, _ in lessons_data]
                expected_compact = list(range(1, len(lessons_data) + 1))
                if lesson_numbers == expected_compact:
                    continue

                for lesson in range(1, lessons_per_day + 1):
                    compacted[day][lesson][class_id] = None

                lessons_data.sort(key=lambda x: x[0])

                best_placement: List[Tuple[int, Tuple[int, int]]] = []
                min_last_slot = lessons_per_day + 1

                placement = try_compact_placement(
                    compacted, day, class_id, lessons_data, lessons_per_day
                )
                if placement:
                    last_slot = max(slot for slot, _ in placement)
                    if last_slot < min_last_slot:
                        min_last_slot = last_slot
                        best_placement = placement

                lessons_data_rev = lessons_data[::-1]
                placement = try_compact_placement(
                    compacted, day, class_id, lessons_data_rev, lessons_per_day
                )
                if placement:
                    last_slot = max(slot for slot, _ in placement)
                    if last_slot < min_last_slot:
                        min_last_slot = last_slot
                        best_placement = placement

                if best_placement:
                    for slot, assignment in best_placement:
                        compacted[day][slot][class_id] = assignment
                    if min(best_placement)[0] < min(lesson_numbers):
                        improved = True
                else:
                    for lesson, assignment in lessons_data:
                        compacted[day][lesson][class_id] = assignment

        if not improved:
            break

    return compacted


def try_compact_placement(
    schedule: Dict,
    day: str,
    class_id: int,
    lessons_data: List[Tuple[int, Tuple[int, int]]],
    lessons_per_day: int,
) -> List[Tuple[int, Tuple[int, int]]]:
    """
    Try to place lessons compactly starting from slot 1 without teacher conflicts.
    Returns list of (slot, assignment) if successful, otherwise [].
    """
    placement: List[Tuple[int, Tuple[int, int]]] = []
    next_slot = 1

    for _, assignment in lessons_data:
        teacher_id, _ = assignment
        placed = False
        for slot in range(next_slot, lessons_per_day + 1):
            teacher_busy = False
            for other_class_id, other_assignment in schedule[day][slot].items():
                if other_class_id != class_id and other_assignment is not None:
                    if other_assignment[0] == teacher_id:
                        teacher_busy = True
                        break
            if not teacher_busy:
                placement.append((slot, assignment))
                next_slot = slot + 1
                placed = True
                break
        if not placed:
            return []

    return placement


