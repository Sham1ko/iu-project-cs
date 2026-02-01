from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from .export.pdf_exporter import export_schedule_pdf
from .ga.fitness_metrics import (
    count_teacher_conflicts,
    count_teacher_gaps,
    count_total_lessons,
)
from .ga.genetic_scheduler import GeneticScheduler
from .io.data_service import DataService

logger = logging.getLogger(__name__)


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
    output_dir = config.get("output_dir")
    pdf_title = config.get("pdf_title")
    pdf_filename = config.get("pdf_filename")

    data_service = DataService(payload=input_data)
    scheduler = GeneticScheduler(data_service)
    _apply_ga_config(scheduler, config)

    start_time = time.perf_counter()
    schedule, fitness, generation = scheduler.generate_schedule(verbose=False)
    duration = time.perf_counter() - start_time

    result = _build_result_payload(schedule, scheduler, fitness, generation)
    if output_dir:
        try:
            export_schedule_pdf(
                schedule,
                output_dir=str(output_dir),
                days=scheduler.DAYS,
                lessons_per_day=scheduler.LESSONS_PER_DAY,
                classes=scheduler.classes,
                classes_by_id=scheduler.classes_by_id,
                teachers_by_id=scheduler.teachers_by_id,
                subjects_by_id=scheduler.subjects_by_id,
                title=pdf_title or f"Schedule - run {run_id}",
                filename=str(pdf_filename) if pdf_filename else None,
            )
        except Exception as exc:
            logger.exception("PDF export failed run_id=%s error=%s", run_id, exc)
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
