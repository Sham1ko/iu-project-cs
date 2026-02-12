import copy
import random
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..io.data_service import DataService

from .fitness_metrics import calculate_schedule_fitness
from .schedule_compaction import compact_mutation


def get_next_version_dir(base_dir: str = "data") -> Path:
    """
    Find the next version directory (v1, v2, v3, ...).
    Returns the path to the next version directory.
    """
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    version_dirs = [
        d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("v")
    ]

    if not version_dirs:
        next_version = 1
    else:
        versions = []
        for d in version_dirs:
            try:
                version_num = int(d.name[1:])
                versions.append(version_num)
            except ValueError:
                continue

        next_version = max(versions) + 1 if versions else 1

    return base_path / f"v{next_version}"


class GeneticScheduler:
    """Timetable scheduler with strict class-contiguity constraints."""

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    LESSONS_PER_DAY = 7

    POPULATION_SIZE = 50
    GENERATIONS = 200
    MUTATION_RATE = 0.1
    TOURNAMENT_SIZE = 5

    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.teachers = data_service.load_teachers()
        self.classes = data_service.load_classes()
        self.subjects = data_service.load_subjects()

        self.teachers_by_id = {self._coerce_int(t.get("id")): t for t in self.teachers}
        self.classes_by_id = {self._coerce_int(c.get("id")): c for c in self.classes}
        self.subjects_by_id = {self._coerce_int(s.get("id")): s for s in self.subjects}

        self.class_name_to_id = {
            self._normalize_class_name(cls.get("name")): cls_id
            for cls_id, cls in self.classes_by_id.items()
            if cls_id is not None
        }

        self.teacher_subject_ids: Dict[int, set[int]] = {}
        self.teacher_allowed_classes: Dict[int, set[int] | None] = {}
        for teacher_id, teacher in self.teachers_by_id.items():
            if teacher_id is None:
                continue
            subject_ids: set[int] = set()
            for raw_subject_id in teacher.get("subjects", []) or []:
                subject_id = self._coerce_int(raw_subject_id)
                if subject_id is not None:
                    subject_ids.add(subject_id)
            self.teacher_subject_ids[teacher_id] = subject_ids
            self.teacher_allowed_classes[teacher_id] = self._parse_teacher_groups(teacher)

        self.teachers_by_subject = {
            subject_id: [
                teacher
                for teacher_id, teacher in self.teachers_by_id.items()
                if teacher_id is not None and subject_id in self.teacher_subject_ids.get(teacher_id, set())
            ]
            for subject_id in self.subjects_by_id
            if subject_id is not None
        }

        self.teachers_by_subject_and_class: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
        for class_id in self.classes_by_id:
            if class_id is None:
                continue
            for subject_id in self.subjects_by_id:
                if subject_id is None:
                    continue
                candidates: List[Dict[str, Any]] = []
                for teacher_id, teacher in self.teachers_by_id.items():
                    if teacher_id is None:
                        continue
                    if subject_id not in self.teacher_subject_ids.get(teacher_id, set()):
                        continue
                    allowed_classes = self.teacher_allowed_classes.get(teacher_id)
                    if allowed_classes is not None and class_id not in allowed_classes:
                        continue
                    candidates.append(teacher)
                self.teachers_by_subject_and_class[(class_id, subject_id)] = candidates

        self.required_hours_by_class = self._build_required_hours_by_class()
        self.daily_lessons_by_class = self._build_daily_lesson_targets()

        max_daily_load = 0
        for loads in self.daily_lessons_by_class.values():
            if loads:
                max_daily_load = max(max_daily_load, max(loads))
        self.LESSONS_PER_DAY = max(self.LESSONS_PER_DAY, max_daily_load)

        self.total_week_slots = len(self.DAYS) * self.LESSONS_PER_DAY
        self.teacher_capacity_by_id: Dict[int, int] = {}
        for teacher_id, teacher in self.teachers_by_id.items():
            if teacher_id is None:
                continue
            max_hours = self._coerce_int(
                teacher.get("max_weekly_hours", teacher.get("max_hours"))
            )
            if max_hours is None or max_hours <= 0:
                max_hours = self.total_week_slots
            self.teacher_capacity_by_id[teacher_id] = max_hours

        for class_id, subject_hours in self.required_hours_by_class.items():
            for subject_id, hours in subject_hours.items():
                if hours <= 0:
                    continue
                if not self.teachers_by_subject_and_class.get((class_id, subject_id)):
                    class_name = self.classes_by_id[class_id].get("name", class_id)
                    subject_name = self.subjects_by_id[subject_id].get("name", subject_id)
                    raise ValueError(
                        f"No qualified teacher for subject '{subject_name}' in class '{class_name}'."
                    )

    @staticmethod
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

    @staticmethod
    def _normalize_class_name(name: Any) -> str:
        if name is None:
            return ""
        text = str(name).strip()
        return "".join(text.split()).lower()

    def _resolve_class_key(self, class_key: Any) -> int | None:
        class_id = self._coerce_int(class_key)
        if class_id is not None and class_id in self.classes_by_id:
            return class_id
        normalized = self._normalize_class_name(class_key)
        return self.class_name_to_id.get(normalized)

    def _parse_teacher_groups(self, teacher: Dict[str, Any]) -> set[int] | None:
        raw_groups = teacher.get("groups")
        if not isinstance(raw_groups, list) or not raw_groups:
            return None

        groups: set[int] = set()
        for group in raw_groups:
            class_id = self._resolve_class_key(group)
            if class_id is not None:
                groups.add(class_id)

        return groups if groups else None

    def _extract_subject_hours_for_class(
        self,
        subject: Dict[str, Any],
        class_id: int,
        class_grade: int,
    ) -> int | None:
        by_class = subject.get("weekly_hours_by_class")
        if isinstance(by_class, dict):
            resolved: Dict[int, int] = {}
            for class_key, raw_hours in by_class.items():
                resolved_class_id = self._resolve_class_key(class_key)
                if resolved_class_id is None:
                    continue
                hours = self._coerce_int(raw_hours)
                if hours is None:
                    continue
                resolved[resolved_class_id] = max(0, int(hours))
            return resolved.get(class_id, 0)

        by_grade = subject.get("weekly_hours_by_grade")
        if isinstance(by_grade, dict):
            grade_hours: Dict[int, int] = {}
            for grade_key, raw_hours in by_grade.items():
                grade = self._coerce_int(grade_key)
                hours = self._coerce_int(raw_hours)
                if grade is None or hours is None:
                    continue
                grade_hours[int(grade)] = max(0, int(hours))
            return grade_hours.get(class_grade, 0)

        for key in ("weekly_hours", "hours_per_week", "hours"):
            if key not in subject:
                continue
            hours = self._coerce_int(subject.get(key))
            if hours is None:
                return 0
            return max(0, int(hours))

        return None

    def _build_required_hours_by_class(self) -> Dict[int, Dict[int, int]]:
        required: Dict[int, Dict[int, int]] = {}
        for class_id, cls in self.classes_by_id.items():
            if class_id is None:
                continue
            class_grade = self._coerce_int(cls.get("grade")) or 0
            class_subject_hours: Dict[int, int] = {}
            has_explicit_hours = False

            for subject_id, subject in self.subjects_by_id.items():
                if subject_id is None:
                    continue
                hours = self._extract_subject_hours_for_class(subject, class_id, class_grade)
                if hours is None:
                    continue
                has_explicit_hours = True
                if hours > 0:
                    class_subject_hours[subject_id] = hours

            if not has_explicit_hours:
                for subject_id in self.subjects_by_id:
                    if subject_id is None:
                        continue
                    class_subject_hours[subject_id] = 1

            required[class_id] = class_subject_hours

        return required

    def _build_daily_lesson_targets(self) -> Dict[int, List[int]]:
        targets: Dict[int, List[int]] = {}
        day_count = len(self.DAYS)

        for class_id, subject_hours in self.required_hours_by_class.items():
            total = sum(max(0, int(hours)) for hours in subject_hours.values())
            base = total // day_count
            remainder = total % day_count
            loads = [base for _ in range(day_count)]
            for idx in range(remainder):
                loads[idx] += 1
            targets[class_id] = loads

        return targets

    def _build_empty_schedule(self) -> Dict[str, Dict[int, Dict[int, Optional[Tuple[int, int]]]]]:
        schedule: Dict[str, Dict[int, Dict[int, Optional[Tuple[int, int]]]]] = {}
        class_ids = [class_id for class_id in self.classes_by_id if class_id is not None]

        for day in self.DAYS:
            schedule[day] = {}
            for lesson in range(1, self.LESSONS_PER_DAY + 1):
                schedule[day][lesson] = {class_id: None for class_id in class_ids}

        return schedule

    def calculate_fitness(self, schedule: Dict) -> float:
        return calculate_schedule_fitness(
            schedule,
            days=self.DAYS,
            lessons_per_day=self.LESSONS_PER_DAY,
            teachers=self.teachers,
            classes=self.classes,
            teachers_by_id=self.teachers_by_id,
        )

    def selection(self, population: List[Tuple[Dict, float]]) -> Dict:
        """Tournament selection: pick best from random sample."""
        tournament = random.sample(
            population, min(self.TOURNAMENT_SIZE, len(population))
        )
        return max(tournament, key=lambda x: x[1])[0]

    def crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """
        Single-point crossover: exchange days between parents.
        """
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)

        crossover_point = random.randint(1, len(self.DAYS) - 1)

        for i in range(crossover_point, len(self.DAYS)):
            day = self.DAYS[i]
            child1[day], child2[day] = child2[day], child1[day]

        return child1, child2

    def mutate(self, schedule: Dict) -> Dict:
        """
        Mutate schedule by randomly changing some lessons.
        60% chance to use compaction mutation (shift lessons to start of day).
        """
        mutated = copy.deepcopy(schedule)

        if random.random() < 0.6:
            mutated = compact_mutation(
                mutated, self.DAYS, self.LESSONS_PER_DAY, self.classes
            )
        else:
            num_mutations = random.randint(1, 5)

            for _ in range(num_mutations):
                day = random.choice(self.DAYS)
                lesson = random.randint(1, self.LESSONS_PER_DAY)
                cls = random.choice(self.classes)

                class_id = self._coerce_int(cls.get("id"))
                if class_id is None:
                    continue

                if random.random() < 0.5:
                    mutated[day][lesson][class_id] = None
                else:
                    subject = random.choice(self.subjects)
                    subject_id = self._coerce_int(subject.get("id"))
                    if subject_id is None:
                        continue

                    available_teachers = self.teachers_by_subject_and_class.get(
                        (class_id, subject_id), []
                    )
                    if available_teachers:
                        teacher = random.choice(available_teachers)
                        teacher_id = self._coerce_int(teacher.get("id"))
                        if teacher_id is None:
                            continue
                        mutated[day][lesson][class_id] = (teacher_id, subject_id)

        return mutated

    def _active_classes_at(self, day_index: int, lesson: int) -> List[int]:
        active: List[int] = []
        for class_id, loads in self.daily_lessons_by_class.items():
            if day_index < len(loads) and lesson <= loads[day_index]:
                active.append(class_id)
        return active

    def _class_slots_after(self, class_id: int, day_index: int, lesson: int) -> int:
        slots = 0
        for idx in range(day_index, len(self.DAYS)):
            load = self.daily_lessons_by_class[class_id][idx]
            start = lesson + 1 if idx == day_index else 1
            if load >= start:
                slots += load - start + 1
        return slots

    def _count_pairs_for_class_day(
        self,
        schedule: Dict[str, Dict[int, Dict[int, Optional[Tuple[int, int]]]]],
        *,
        day: str,
        class_id: int,
        up_to_lesson: int,
    ) -> int:
        pairs = 0
        last_subject: int | None = None
        for slot in range(1, up_to_lesson + 1):
            assignment = schedule[day][slot].get(class_id)
            subject_id = assignment[1] if assignment is not None else None
            if subject_id is not None and last_subject == subject_id:
                pairs += 1
            last_subject = subject_id
        return pairs

    def _slot_options_for_class(
        self,
        class_id: int,
        *,
        day: str,
        day_index: int,
        lesson: int,
        schedule: Dict[str, Dict[int, Dict[int, Optional[Tuple[int, int]]]]],
        remaining: Dict[int, Dict[int, int]],
        teacher_remaining: Dict[int, int],
        teacher_busy: set[int],
    ) -> List[Tuple[int, int]]:
        scored: List[Tuple[float, int, int]] = []

        subject_ids = list(remaining[class_id].keys())
        random.shuffle(subject_ids)

        previous_assignment = (
            schedule[day][lesson - 1].get(class_id) if lesson > 1 else None
        )
        previous_subject = previous_assignment[1] if previous_assignment is not None else None
        existing_pairs_today = self._count_pairs_for_class_day(
            schedule, day=day, class_id=class_id, up_to_lesson=max(lesson - 1, 0)
        )

        for subject_id in subject_ids:
            if remaining[class_id][subject_id] <= 0:
                continue
            candidates = self.teachers_by_subject_and_class.get((class_id, subject_id), [])
            if not candidates:
                continue

            shuffled_candidates = candidates[:]
            random.shuffle(shuffled_candidates)
            for teacher in shuffled_candidates:
                teacher_id = self._coerce_int(teacher.get("id"))
                if teacher_id is None:
                    continue
                if teacher_id in teacher_busy:
                    continue
                if teacher_remaining.get(teacher_id, 0) <= 0:
                    continue
                score = float(remaining[class_id][subject_id]) * 5.0
                score += float(teacher_remaining.get(teacher_id, 0)) * 0.05

                # Prefer creating exactly one pair per day.
                if previous_subject == subject_id:
                    if existing_pairs_today == 0:
                        score += 100.0
                    else:
                        score -= 50.0

                scored.append((score, subject_id, teacher_id))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [(subject_id, teacher_id) for _, subject_id, teacher_id in scored]

    def _assign_single_timeslot(
        self,
        *,
        day_index: int,
        day: str,
        lesson: int,
        active_classes: List[int],
        schedule: Dict[str, Dict[int, Dict[int, Optional[Tuple[int, int]]]]],
        remaining: Dict[int, Dict[int, int]],
        teacher_remaining: Dict[int, int],
    ) -> bool:
        teacher_busy: set[int] = set()
        assignments: Dict[int, Tuple[int, int]] = {}

        def backtrack(unassigned: List[int]) -> bool:
            if not unassigned:
                return True

            best_class_id: int | None = None
            best_options: List[Tuple[int, int]] | None = None

            for class_id in unassigned:
                options = self._slot_options_for_class(
                    class_id,
                    day=day,
                    day_index=day_index,
                    lesson=lesson,
                    schedule=schedule,
                    remaining=remaining,
                    teacher_remaining=teacher_remaining,
                    teacher_busy=teacher_busy,
                )
                if not options:
                    return False
                if best_options is None or len(options) < len(best_options):
                    best_options = options
                    best_class_id = class_id

            if best_class_id is None or best_options is None:
                return False

            remaining_unassigned = [
                class_id for class_id in unassigned if class_id != best_class_id
            ]

            for subject_id, teacher_id in best_options:
                assignments[best_class_id] = (teacher_id, subject_id)
                teacher_busy.add(teacher_id)
                remaining[best_class_id][subject_id] -= 1
                teacher_remaining[teacher_id] -= 1

                remaining_for_class = sum(remaining[best_class_id].values())
                can_finish = (
                    remaining_for_class
                    <= self._class_slots_after(best_class_id, day_index, lesson)
                )

                if can_finish and backtrack(remaining_unassigned):
                    return True

                teacher_remaining[teacher_id] += 1
                remaining[best_class_id][subject_id] += 1
                teacher_busy.remove(teacher_id)
                assignments.pop(best_class_id, None)

            return False

        if not backtrack(active_classes):
            return False

        for class_id, assignment in assignments.items():
            schedule[day][lesson][class_id] = assignment

        return True

    def _generate_schedule_attempt(
        self,
    ) -> Dict[str, Dict[int, Dict[int, Optional[Tuple[int, int]]]]] | None:
        schedule = self._build_empty_schedule()
        remaining = {
            class_id: dict(subject_hours)
            for class_id, subject_hours in self.required_hours_by_class.items()
        }
        teacher_remaining = dict(self.teacher_capacity_by_id)

        for day_index, day in enumerate(self.DAYS):
            for lesson in range(1, self.LESSONS_PER_DAY + 1):
                active_classes = self._active_classes_at(day_index, lesson)
                if not active_classes:
                    continue

                if not self._assign_single_timeslot(
                    day_index=day_index,
                    day=day,
                    lesson=lesson,
                    active_classes=active_classes,
                    schedule=schedule,
                    remaining=remaining,
                    teacher_remaining=teacher_remaining,
                ):
                    return None

        for class_id, subject_hours in remaining.items():
            if any(hours > 0 for hours in subject_hours.values()):
                return None

        return schedule

    def generate_schedule(
        self,
        verbose: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[Dict, float, int]:
        """
        Build a schedule that respects curriculum hours, teacher constraints,
        contiguous daily lessons, and synchronized class starts.
        """
        attempts = max(1, int(self.GENERATIONS))

        best_schedule: Dict | None = None
        best_fitness = -1.0
        best_generation = 0

        for generation in range(attempts):
            if progress_callback is not None:
                progress_callback(generation + 1, attempts)

            candidate = self._generate_schedule_attempt()
            if candidate is None:
                continue

            fitness = self.calculate_fitness(candidate)
            if fitness > best_fitness:
                best_schedule = candidate
                best_fitness = fitness
                best_generation = generation

        if best_schedule is None:
            raise ValueError(
                "Unable to generate a feasible schedule for the provided dataset and constraints."
            )

        if verbose:
            print("Schedule generation complete.")
            print(f"Best fitness: {best_fitness:.2f}")
            print(f"Found at generation: {best_generation}")

        return best_schedule, best_fitness, best_generation
