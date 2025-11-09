from services.data_service import DataService


def main():
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


if __name__ == "__main__":
    main()

