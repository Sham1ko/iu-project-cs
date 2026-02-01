from .export.pdf_exporter import export_schedule_pdf
from .export.schedule_exporter import export_schedule_json
from .ga.genetic_scheduler import GeneticScheduler, get_next_version_dir
from .io.data_service import DataService

DEFAULT_TEACHERS_FILE = "teachers.json"


def generate_schedule(teachers_file: str = DEFAULT_TEACHERS_FILE) -> None:
    """Generate school schedule using genetic algorithm."""
    print("=" * 60)
    print("SCHOOL SCHEDULE GENERATOR - GENETIC ALGORITHM")
    print("=" * 60)
    print(f"Using teachers file: {teachers_file}")
    print()

    # Initialize services
    data_service = DataService(teachers_file=teachers_file)
    scheduler = GeneticScheduler(data_service)

    print("Configuration:")
    print(f"  - Days per week: {len(scheduler.DAYS)}")
    print(f"  - Lessons per day: {scheduler.LESSONS_PER_DAY}")
    print(f"  - Number of classes: {len(scheduler.classes)}")
    print(f"  - Number of teachers: {len(scheduler.teachers)}")
    print(f"  - Number of subjects: {len(scheduler.subjects)}")
    print("\nGenetic Algorithm Parameters:")
    print(f"  - Population size: {scheduler.POPULATION_SIZE}")
    print(f"  - Generations: {scheduler.GENERATIONS}")
    print(f"  - Mutation rate: {scheduler.MUTATION_RATE}")
    print(f"  - Tournament size: {scheduler.TOURNAMENT_SIZE}")
    print()

    # Generate schedule
    print("Starting evolution...")
    print("-" * 60)
    best_schedule, fitness, generation = scheduler.generate_schedule(verbose=True)
    print("-" * 60)

    # Determine next version directory
    version_dir = get_next_version_dir("data")
    version_name = version_dir.name
    print(f"\nSaving results to version: {version_name}")

    # Export results to versioned directory
    export_schedule_json(
        best_schedule,
        fitness,
        generation,
        output_path=str(version_dir / "schedule.json"),
        days=scheduler.DAYS,
        lessons_per_day=scheduler.LESSONS_PER_DAY,
        classes_by_id=scheduler.classes_by_id,
        teachers_by_id=scheduler.teachers_by_id,
        subjects_by_id=scheduler.subjects_by_id,
        teachers=scheduler.teachers,
        classes=scheduler.classes,
    )
    export_schedule_pdf(
        best_schedule,
        output_dir=str(version_dir),
        days=scheduler.DAYS,
        lessons_per_day=scheduler.LESSONS_PER_DAY,
        classes=scheduler.classes,
        classes_by_id=scheduler.classes_by_id,
        teachers_by_id=scheduler.teachers_by_id,
        subjects_by_id=scheduler.subjects_by_id,
        title=f"Schedule - {version_name}",
    )

    print("\n" + "=" * 60)
    print("SCHEDULE GENERATION COMPLETE!")
    print(f"Results saved to: {version_dir}")
    print("=" * 60)


if __name__ == "__main__":
    generate_schedule()
