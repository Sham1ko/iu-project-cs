from services.data_service import DataService
from services.genetic_scheduler import GeneticScheduler, get_next_version_dir
from validate_data import DataValidator


def show_data_info():
    """Display information about available data."""
    service = DataService()
    
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


def validate_data():
    """Run data validation checks."""
    try:
        validator = DataValidator()
        validator.validate_all()
    except Exception as e:
        print(f"Error during validation: {e}")


def generate_schedule():
    """Generate school schedule using genetic algorithm."""
    print("=" * 60)
    print("SCHOOL SCHEDULE GENERATOR - GENETIC ALGORITHM")
    print("=" * 60)
    print()
    
    # Initialize services
    data_service = DataService()
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
    scheduler.export_schedule(best_schedule, fitness, generation, 
                             output_path=str(version_dir / "schedule.json"))
    scheduler.export_to_csv(best_schedule, fitness, generation, 
                           output_dir=str(version_dir))
    
    print("\n" + "=" * 60)
    print("SCHEDULE GENERATION COMPLETE!")
    print(f"Results saved to: {version_dir}")
    print("=" * 60)


def main():
    """Main menu."""
    def print_menu():
        print("\n" + "=" * 60)
        print("SCHOOL SCHEDULE MANAGEMENT SYSTEM")
        print("=" * 60)
        print("\nOptions:")
        print("  1. Generate new schedule (Genetic Algorithm)")
        print("  2. Validate data (Check teacher availability)")
        print("  3. Show data information")
        print("  4. Exit")
        print()
    
    print_menu()
    
    while True:
        choice = input("Select option (1-4): ").strip()
        
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
            show_data_info()
            print("\nPress Enter to return to menu...")
            input()
            print_menu()
        elif choice == "4":
            print("\nGoodbye!")
            break
        else:
            print("Invalid option. Please select 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()

