"""
Data Validation Script
Checks if there are enough teachers for all classes and subjects.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class DataValidator:
    """Validates school schedule data for feasibility."""
    
    DAYS_PER_WEEK = 5
    LESSONS_PER_DAY = 6
    MAX_LESSONS_PER_WEEK = DAYS_PER_WEEK * LESSONS_PER_DAY
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.load_data()
    
    def load_data(self):
        """Load all data files."""
        with open(self.data_dir / "classes.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.classes = data['classes'] if 'classes' in data else data
        
        with open(self.data_dir / "teachers.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.teachers = data['teachers'] if 'teachers' in data else data
        
        with open(self.data_dir / "subjects.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.subjects = data['subjects'] if 'subjects' in data else data
        
        # Create lookup dictionaries
        self.teachers_by_id = {t['id']: t for t in self.teachers}
        self.classes_by_id = {c['id']: c for c in self.classes}
        self.subjects_by_id = {s['id']: s for s in self.subjects}
    
    def validate_all(self):
        """Run all validation checks and display results."""
        print("=" * 70)
        print("DATA VALIDATION REPORT")
        print("=" * 70)
        print()
        
        # Basic statistics
        self._print_basic_stats()
        print()
        
        # Validation checks
        checks = [
            ("1. Teachers per Subject", self._check_teachers_per_subject),
            ("2. Subject Coverage", self._check_subject_coverage),
            ("3. Teacher Workload Analysis", self._check_teacher_workload),
            ("4. Class Requirements vs Teacher Availability", self._check_class_requirements),
            ("5. Potential Scheduling Conflicts", self._check_potential_conflicts),
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            print(f"\n{check_name}")
            print("-" * 70)
            passed = check_func()
            if not passed:
                all_passed = False
            print()
        
        # Final verdict
        print("=" * 70)
        if all_passed:
            print("✓ ALL CHECKS PASSED - Data is valid for scheduling")
        else:
            print("✗ SOME CHECKS FAILED - Review issues above")
        print("=" * 70)
    
    def _print_basic_stats(self):
        """Print basic statistics about the data."""
        print("BASIC STATISTICS")
        print("-" * 70)
        print(f"Total Classes:    {len(self.classes)}")
        print(f"Total Teachers:   {len(self.teachers)}")
        print(f"Total Subjects:   {len(self.subjects)}")
        print(f"Max lessons/week: {self.MAX_LESSONS_PER_WEEK} ({self.DAYS_PER_WEEK} days × {self.LESSONS_PER_DAY} lessons)")
    
    def _check_teachers_per_subject(self) -> bool:
        """Check how many teachers can teach each subject."""
        # Count teachers per subject
        teachers_per_subject = defaultdict(list)
        for teacher in self.teachers:
            for subject_id in teacher['subjects']:
                teachers_per_subject[subject_id].append(teacher)
        
        all_ok = True
        
        for subject in self.subjects:
            subject_id = subject['id']
            subject_name = subject['name']
            teacher_count = len(teachers_per_subject.get(subject_id, []))
            
            status = "✓" if teacher_count > 0 else "✗"
            if teacher_count == 0:
                all_ok = False
                print(f"{status} {subject_name}: {teacher_count} teachers - NO TEACHERS AVAILABLE!")
            elif teacher_count == 1:
                teacher_name = teachers_per_subject[subject_id][0]['name']
                print(f"{status} {subject_name}: {teacher_count} teacher ({teacher_name}) - LIMITED")
            else:
                teacher_names = [t['name'] for t in teachers_per_subject[subject_id]]
                print(f"{status} {subject_name}: {teacher_count} teachers ({', '.join(teacher_names)})")
        
        return all_ok
    
    def _check_subject_coverage(self) -> bool:
        """Check if all subjects have at least one teacher."""
        subjects_without_teachers = []
        teachers_without_subjects = []
        
        # Find subjects without teachers
        for subject in self.subjects:
            has_teacher = any(subject['id'] in t['subjects'] for t in self.teachers)
            if not has_teacher:
                subjects_without_teachers.append(subject['name'])
        
        # Find teachers without subjects
        for teacher in self.teachers:
            if not teacher['subjects']:
                teachers_without_subjects.append(teacher['name'])
        
        all_ok = True
        
        if subjects_without_teachers:
            all_ok = False
            print(f"✗ Subjects without teachers ({len(subjects_without_teachers)}):")
            for subject in subjects_without_teachers:
                print(f"  - {subject}")
        else:
            print("✓ All subjects have at least one teacher")
        
        if teachers_without_subjects:
            print(f"\n⚠ Teachers without assigned subjects ({len(teachers_without_subjects)}):")
            for teacher in teachers_without_subjects:
                print(f"  - {teacher}")
        else:
            print("✓ All teachers have assigned subjects")
        
        return all_ok
    
    def _check_teacher_workload(self) -> bool:
        """Analyze potential teacher workload."""
        print("Maximum theoretical lessons per teacher:")
        print(f"(Assuming each teacher works all {self.MAX_LESSONS_PER_WEEK} time slots)\n")
        
        # Calculate potential demand per subject
        subject_demand = defaultdict(int)
        for cls in self.classes:
            # Estimate: each class might have 3-5 lessons per subject per week
            # For simplicity, assume 4 lessons average per subject
            for subject in self.subjects:
                subject_demand[subject['id']] += 4
        
        # Calculate teacher capacity
        teachers_per_subject = defaultdict(list)
        for teacher in self.teachers:
            for subject_id in teacher['subjects']:
                teachers_per_subject[subject_id].append(teacher)
        
        all_ok = True
        
        for subject in self.subjects:
            subject_id = subject['id']
            subject_name = subject['name']
            teachers = teachers_per_subject.get(subject_id, [])
            teacher_count = len(teachers)
            
            if teacher_count == 0:
                print(f"✗ {subject_name}: NO TEACHERS - Cannot schedule!")
                all_ok = False
            else:
                total_capacity = teacher_count * self.MAX_LESSONS_PER_WEEK
                estimated_demand = subject_demand[subject_id]
                utilization = (estimated_demand / total_capacity * 100) if total_capacity > 0 else 0
                
                status = "✓" if utilization <= 80 else "⚠" if utilization <= 100 else "✗"
                
                print(f"{status} {subject_name}:")
                print(f"   Teachers: {teacher_count}, Capacity: {total_capacity} lessons/week")
                print(f"   Estimated demand: {estimated_demand} lessons/week")
                print(f"   Utilization: {utilization:.1f}%")
                
                if utilization > 100:
                    print(f"   WARNING: Demand exceeds capacity!")
                    all_ok = False
                elif utilization > 80:
                    print(f"   WARNING: High utilization - scheduling might be difficult")
        
        return all_ok
    
    def _check_class_requirements(self) -> bool:
        """Check if classes can get all their required subjects."""
        print("Checking if each class can potentially receive all subjects:\n")
        
        all_ok = True
        
        for cls in self.classes:
            class_name = cls['name']
            impossible_subjects = []
            
            for subject in self.subjects:
                # Check if there's at least one teacher who can teach this subject
                has_teacher = any(subject['id'] in t['subjects'] for t in self.teachers)
                if not has_teacher:
                    impossible_subjects.append(subject['name'])
            
            if impossible_subjects:
                print(f"✗ Class {class_name}: Cannot get {len(impossible_subjects)} subjects:")
                for subj in impossible_subjects:
                    print(f"  - {subj}")
                all_ok = False
            else:
                print(f"✓ Class {class_name}: Can potentially get all subjects")
        
        return all_ok
    
    def _check_potential_conflicts(self) -> bool:
        """Check for potential scheduling conflicts."""
        print("Analyzing potential scheduling bottlenecks:\n")
        
        # Find subjects with only one teacher
        single_teacher_subjects = []
        teachers_per_subject = defaultdict(list)
        
        for teacher in self.teachers:
            for subject_id in teacher['subjects']:
                teachers_per_subject[subject_id].append(teacher)
        
        for subject in self.subjects:
            if len(teachers_per_subject[subject['id']]) == 1:
                teacher = teachers_per_subject[subject['id']][0]
                single_teacher_subjects.append((subject['name'], teacher['name']))
        
        if single_teacher_subjects:
            print(f"⚠ Subjects with only one teacher ({len(single_teacher_subjects)}):")
            print("  (These may cause scheduling conflicts)")
            for subj_name, teacher_name in single_teacher_subjects:
                print(f"  - {subj_name} → {teacher_name}")
            print()
        
        # Find teachers teaching many subjects
        multi_subject_teachers = []
        for teacher in self.teachers:
            if len(teacher['subjects']) >= 4:
                subject_names = [self.subjects_by_id[s]['name'] for s in teacher['subjects']]
                multi_subject_teachers.append((teacher['name'], len(teacher['subjects']), subject_names))
        
        if multi_subject_teachers:
            print(f"⚠ Teachers with many subjects ({len(multi_subject_teachers)}):")
            print("  (These teachers will be in high demand)")
            for teacher_name, count, subjects in multi_subject_teachers:
                print(f"  - {teacher_name}: {count} subjects")
                print(f"    ({', '.join(subjects)})")
            print()
        
        # Calculate if total lessons fit in schedule
        total_classes = len(self.classes)
        total_slots = total_classes * self.MAX_LESSONS_PER_WEEK
        estimated_lessons = len(self.subjects) * len(self.classes) * 4  # 4 lessons per subject per class
        
        print(f"Capacity Analysis:")
        print(f"  Total available slots: {total_slots}")
        print(f"  Estimated lessons needed: {estimated_lessons}")
        print(f"  Capacity utilization: {(estimated_lessons / total_slots * 100):.1f}%")
        
        if estimated_lessons > total_slots:
            print(f"  ✗ WARNING: Not enough slots for all lessons!")
            return False
        elif estimated_lessons > total_slots * 0.9:
            print(f"  ⚠ WARNING: Very tight schedule - might be difficult to optimize")
        else:
            print(f"  ✓ Sufficient capacity available")
        
        return True


def main():
    """Run validation."""
    try:
        validator = DataValidator()
        validator.validate_all()
    except FileNotFoundError as e:
        print(f"Error: Could not find data file - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in data file - {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

