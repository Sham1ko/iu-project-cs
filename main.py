from services.data_service import DataService
from services.genetic_scheduler import GeneticScheduler, get_next_version_dir
from services.schedule_exporter import export_schedule_json, export_to_csv
from validate_data import DataValidator

# Global variable for selected teachers file
CURRENT_TEACHERS_FILE = "teachers.json"


def show_data_info():
    """Display information about available data."""
    global CURRENT_TEACHERS_FILE
    service = DataService(teachers_file=CURRENT_TEACHERS_FILE)
    
    print("=== Subjects ===")
    subjects = service.load_subjects()
    for subject in subjects:
        print(f"{subject['id']}: {subject['name']}")
    
    print("\n=== Teachers ===")
    teachers = service.load_teachers()
    for teacher in teachers:
        subjects_names = [service.get_subject_by_id(sid)['name'] for sid in teacher['subjects']]
        print(f"{teacher['id']}: {teacher['name']} - Subjects: {', '.join(subjects_names)}")
    
    print("\n=== Classes ===")
    classes = service.load_classes()
    for cls in classes:
        print(f"{cls['id']}: {cls['name']} ({cls['grade']} grade)")
    
    print("\n=== Math Teachers ===")
    math_teachers = service.get_teachers_by_subject(1)
    for teacher in math_teachers:
        print(f"- {teacher['name']}")
    
    print("\n=== 7th Grade Classes ===")
    grade_7_classes = service.get_classes_by_grade(7)
    for cls in grade_7_classes:
        print(f"- {cls['name']}")


def select_teachers_file():
    """Select which teachers file to use."""
    global CURRENT_TEACHERS_FILE
    
    print("=" * 60)
    print("SELECT TEACHERS FILE")
    print("=" * 60)
    print("\nAvailable teacher sets:")
    print("  1. teachers.json - Basic set (16 teachers)")
    print("  2. teachers_extended.json - Extended set (28 teachers)")
    print()
    print(f"Current: {CURRENT_TEACHERS_FILE}")
    print()
    
    while True:
        choice = input("Select option (1-2, or Enter to keep current): ").strip()
        
        if choice == "":
            print(f"Keeping current: {CURRENT_TEACHERS_FILE}")
            break
        elif choice == "1":
            CURRENT_TEACHERS_FILE = "teachers.json"
            print(f"✓ Selected: {CURRENT_TEACHERS_FILE}")
            break
        elif choice == "2":
            CURRENT_TEACHERS_FILE = "teachers_extended.json"
            print(f"✓ Selected: {CURRENT_TEACHERS_FILE}")
            break
        else:
            print("Invalid option. Please select 1 or 2.")


def validate_data():
    """Run data validation checks."""
    global CURRENT_TEACHERS_FILE
    try:
        validator = DataValidator(teachers_file=CURRENT_TEACHERS_FILE)
        validator.validate_all()
    except Exception as e:
        print(f"Error during validation: {e}")


def generate_schedule():
    """Generate school schedule using genetic algorithm."""
    global CURRENT_TEACHERS_FILE
    print("=" * 60)
    print("SCHOOL SCHEDULE GENERATOR - GENETIC ALGORITHM")
    print("=" * 60)
    print(f"Using teachers file: {CURRENT_TEACHERS_FILE}")
    print()
    
    # Initialize services
    data_service = DataService(teachers_file=CURRENT_TEACHERS_FILE)
    scheduler = GeneticScheduler(data_service)
    
    print(f"Configuration:")
    print(f"  - Days per week: {len(scheduler.DAYS)}")
    print(f"  - Lessons per day: {scheduler.LESSONS_PER_DAY}")
    print(f"  - Number of classes: {len(scheduler.classes)}")
    print(f"  - Number of teachers: {len(scheduler.teachers)}")
    print(f"  - Number of subjects: {len(scheduler.subjects)}")
    print(f"\nGenetic Algorithm Parameters:")
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
    export_to_csv(
        best_schedule,
        output_dir=str(version_dir),
        days=scheduler.DAYS,
        lessons_per_day=scheduler.LESSONS_PER_DAY,
        teachers=scheduler.teachers,
        classes=scheduler.classes,
        teachers_by_id=scheduler.teachers_by_id,
        subjects_by_id=scheduler.subjects_by_id,
        classes_by_id=scheduler.classes_by_id,
    )
    
    print("\n" + "=" * 60)
    print("SCHEDULE GENERATION COMPLETE!")
    print(f"Results saved to: {version_dir}")
    print("=" * 60)


def main():
    """Main menu."""
    global CURRENT_TEACHERS_FILE
    
    def print_menu():
        print("\n" + "=" * 60)
        print("SCHOOL SCHEDULE MANAGEMENT SYSTEM")
        print("=" * 60)
        print(f"Current teachers file: {CURRENT_TEACHERS_FILE}")
        print("\nOptions:")
        print("  1. Generate new schedule (Genetic Algorithm)")
        print("  2. Validate data (Check teacher availability)")
        print("  3. Select teachers file")
        print("  4. Show data information")
        print("  5. Exit")
        print()
    
    print_menu()
    
    while True:
        choice = input("Select option (1-5): ").strip()
        
        if choice == "1":
            generate_schedule()
            print("\nPress Enter to return to menu...")
            input()
            print_menu()
        elif choice == "2":
            validate_data()
            print("\nPress Enter to return to menu...")
            input()
            print_menu()
        elif choice == "3":
            select_teachers_file()
            print("\nPress Enter to return to menu...")
            input()
            print_menu()
        elif choice == "4":
            show_data_info()
            print("\nPress Enter to return to menu...")
            input()
            print_menu()
        elif choice == "5":
            print("\nGoodbye!")
            break
        else:
            print("Invalid option. Please select 1, 2, 3, 4, or 5.")


if __name__ == "__main__":
    main()

