from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure repo root is importable for the core package.
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from core.ga.fitness_metrics import (  # noqa: E402
    count_teacher_conflicts,
    count_teacher_gaps,
    count_total_lessons,
)
from core.ga.genetic_scheduler import GeneticScheduler  # noqa: E402

logger = logging.getLogger(__name__)


class DictDataService:
    def __init__(self, payload: Dict[str, Any]):
        self._subjects = payload.get("subjects")
        self._teachers = payload.get("teachers")
        self._classes = payload.get("classes")

        if self._subjects is None or self._teachers is None or self._classes is None:
            raise ValueError(
                "Dataset payload must include 'subjects', 'teachers', and 'classes'."
            )

    def load_subjects(self):
        return self._subjects

    def load_teachers(self):
        return self._teachers

    def load_classes(self):
        return self._classes


def _apply_ga_config(scheduler: GeneticScheduler, config: Dict[str, Any]) -> None:
    if "population_size" in config:
        scheduler.POPULATION_SIZE = int(config["population_size"])
    if "generations" in config:
        scheduler.GENERATIONS = int(config["generations"])
    if "mutation_rate" in config:
        scheduler.MUTATION_RATE = float(config["mutation_rate"])
    if "tournament_size" in config:
        scheduler.TOURNAMENT_SIZE = int(config["tournament_size"])


def _build_result_payload(
    schedule: Dict[str, Any],
    scheduler: GeneticScheduler,
    fitness: float,
    generation: int,
) -> Dict[str, Any]:
    statistics = {
        "total_lessons": count_total_lessons(
            schedule, scheduler.DAYS, scheduler.LESSONS_PER_DAY
        ),
        "teacher_conflicts": count_teacher_conflicts(
            schedule,
            scheduler.teachers_by_id,
            scheduler.DAYS,
            scheduler.LESSONS_PER_DAY,
        ),
        "teacher_gaps": count_teacher_gaps(
            schedule, scheduler.teachers, scheduler.DAYS, scheduler.LESSONS_PER_DAY
        ),
    }

    output: Dict[str, Any] = {
        "schedule": {},
        "fitness_score": round(fitness, 2),
        "generation": generation,
        "statistics": statistics,
    }

    for day in scheduler.DAYS:
        output["schedule"][day] = {}
        for lesson in range(1, scheduler.LESSONS_PER_DAY + 1):
            output["schedule"][day][str(lesson)] = {}
            day_schedule = schedule.get(day, {}).get(lesson, {})
            for class_id, assignment in day_schedule.items():
                class_name = scheduler.classes_by_id[class_id]["name"]
                if assignment is not None:
                    teacher_id, subject_id = assignment
                    output["schedule"][day][str(lesson)][class_name] = {
                        "teacher": scheduler.teachers_by_id[teacher_id]["name"],
                        "subject": scheduler.subjects_by_id[subject_id]["name"],
                    }
                else:
                    output["schedule"][day][str(lesson)][class_name] = None

    return output


def generate_timetable(
    input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    config = config or {}
    run_id = config.get("run_id")

    data_service = DictDataService(input_data)
    scheduler = GeneticScheduler(data_service)
    _apply_ga_config(scheduler, config)

    start_time = time.perf_counter()
    schedule, fitness, generation = scheduler.generate_schedule(verbose=False)
    duration = time.perf_counter() - start_time

    result = _build_result_payload(schedule, scheduler, fitness, generation)
    stats = result.get("statistics", {})
    logger.info(
        "GA completed run_id=%s duration=%.2fs fitness=%.2f conflicts=%s gaps=%s",
        run_id,
        duration,
        fitness,
        stats.get("teacher_conflicts"),
        stats.get("teacher_gaps"),
    )
    return result
