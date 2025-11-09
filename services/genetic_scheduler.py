import json
import random
import copy
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from services.data_service import DataService


def get_next_version_dir(base_dir: str = "data") -> Path:
    """
    Find the next version directory (v1, v2, v3, ...).
    Returns the path to the next version directory.
    """
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Find all existing version directories
    version_dirs = [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith('v')]
    
    if not version_dirs:
        next_version = 1
    else:
        # Extract version numbers
        versions = []
        for d in version_dirs:
            try:
                version_num = int(d.name[1:])  # Remove 'v' prefix
                versions.append(version_num)
            except ValueError:
                continue
        
        next_version = max(versions) + 1 if versions else 1
    
    return base_path / f"v{next_version}"


class GeneticScheduler:
    """Genetic Algorithm for School Schedule Generation"""
    
    # Constants
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    LESSONS_PER_DAY = 6
    
    # GA Parameters
    POPULATION_SIZE = 50
    GENERATIONS = 200
    MUTATION_RATE = 0.1
    TOURNAMENT_SIZE = 5
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.teachers = data_service.load_teachers()
        self.classes = data_service.load_classes()
        self.subjects = data_service.load_subjects()
        
        # Create lookup dictionaries for efficiency
        self.teachers_by_id = {t['id']: t for t in self.teachers}
        self.classes_by_id = {c['id']: c for c in self.classes}
        self.subjects_by_id = {s['id']: s for s in self.subjects}
        
        # Map subjects to available teachers
        self.teachers_by_subject = {}
        for subject in self.subjects:
            self.teachers_by_subject[subject['id']] = [
                t for t in self.teachers if subject['id'] in t['subjects']
            ]
    
    def create_random_schedule(self) -> Dict:
        """
        Create a random schedule (chromosome).
        Structure: {day: {lesson: {class_id: (teacher_id, subject_id) or None}}}
        This version avoids teacher conflicts during initialization.
        """
        schedule = {}
        
        for day in self.DAYS:
            schedule[day] = {}
            for lesson in range(1, self.LESSONS_PER_DAY + 1):
                schedule[day][lesson] = {}
                
                # Track which teachers are already assigned in this time slot
                assigned_teachers = set()
                
                for cls in self.classes:
                    # Randomly decide if this slot has a lesson (70% chance)
                    if random.random() < 0.7:
                        # Pick a random subject
                        subject = random.choice(self.subjects)
                        # Get teachers who can teach this subject
                        available_teachers = self.teachers_by_subject.get(subject['id'], [])
                        
                        # Filter out teachers who are already assigned in this slot
                        free_teachers = [t for t in available_teachers 
                                       if t['id'] not in assigned_teachers]
                        
                        if free_teachers:
                            teacher = random.choice(free_teachers)
                            schedule[day][lesson][cls['id']] = (teacher['id'], subject['id'])
                            assigned_teachers.add(teacher['id'])
                        else:
                            # No available teacher, leave slot empty
                            schedule[day][lesson][cls['id']] = None
                    else:
                        schedule[day][lesson][cls['id']] = None
        
        return schedule
    
    def calculate_fitness(self, schedule: Dict) -> float:
        """
        Calculate fitness score for a schedule.
        Higher score = better schedule.
        Score is reduced by penalties for constraint violations.
        """
        score = 1000.0  # Start with perfect score
        
        # Hard constraint penalties
        teacher_conflicts = self._count_teacher_conflicts(schedule)
        score -= teacher_conflicts * 100  # Heavy penalty for teacher conflicts
        
        # Soft constraint penalties
        teacher_gaps = self._count_teacher_gaps(schedule)
        score -= teacher_gaps * 2  # Penalty for teacher gaps
        
        class_gaps = self._count_class_gaps(schedule)
        score -= class_gaps * 3  # Penalty for class gaps
        
        early_gaps = self._count_early_gaps(schedule)
        score -= early_gaps * 5  # Strong penalty for empty slots before first lesson
        
        imbalance = self._calculate_daily_imbalance(schedule)
        score -= imbalance * 1  # Penalty for uneven distribution
        
        # Bonus for having lessons
        total_lessons = self._count_total_lessons(schedule)
        score += total_lessons * 0.5  # Small bonus for each lesson
        
        return max(0, score)  # Ensure non-negative score
    
    def _count_teacher_conflicts(self, schedule: Dict) -> int:
        """Count how many times a teacher has to be in two places at once."""
        conflicts = 0
        
        for day in self.DAYS:
            for lesson in range(1, self.LESSONS_PER_DAY + 1):
                teacher_assignments = {}
                
                for class_id, assignment in schedule[day][lesson].items():
                    if assignment is not None:
                        teacher_id, subject_id = assignment
                        
                        # Check if teacher can teach this subject
                        teacher = self.teachers_by_id[teacher_id]
                        if subject_id not in teacher['subjects']:
                            conflicts += 1  # Wrong subject for teacher
                        
                        # Check if teacher is already assigned
                        if teacher_id in teacher_assignments:
                            conflicts += 1  # Teacher conflict
                        else:
                            teacher_assignments[teacher_id] = class_id
        
        return conflicts
    
    def _count_teacher_gaps(self, schedule: Dict) -> int:
        """Count gaps (free lessons between classes) in teacher schedules."""
        gaps = 0
        
        for teacher in self.teachers:
            teacher_id = teacher['id']
            
            for day in self.DAYS:
                # Find all lessons for this teacher on this day
                lessons_taught = []
                for lesson in range(1, self.LESSONS_PER_DAY + 1):
                    for class_id, assignment in schedule[day][lesson].items():
                        if assignment is not None and assignment[0] == teacher_id:
                            lessons_taught.append(lesson)
                            break
                
                # Count gaps
                if len(lessons_taught) > 1:
                    lessons_taught.sort()
                    for i in range(len(lessons_taught) - 1):
                        gap = lessons_taught[i + 1] - lessons_taught[i] - 1
                        gaps += gap
        
        return gaps
    
    def _count_class_gaps(self, schedule: Dict) -> int:
        """Count gaps (free lessons) in class schedules."""
        gaps = 0
        
        for cls in self.classes:
            class_id = cls['id']
            
            for day in self.DAYS:
                # Find all lessons for this class on this day
                lessons = []
                for lesson in range(1, self.LESSONS_PER_DAY + 1):
                    if schedule[day][lesson].get(class_id) is not None:
                        lessons.append(lesson)
                
                # Count gaps
                if len(lessons) > 1:
                    lessons.sort()
                    for i in range(len(lessons) - 1):
                        gap = lessons[i + 1] - lessons[i] - 1
                        gaps += gap
        
        return gaps
    
    def _count_early_gaps(self, schedule: Dict) -> int:
        """Count empty slots before the first lesson of the day for each class."""
        early_gaps = 0
        
        for cls in self.classes:
            class_id = cls['id']
            
            for day in self.DAYS:
                # Find the first lesson for this class on this day
                first_lesson = None
                for lesson in range(1, self.LESSONS_PER_DAY + 1):
                    if schedule[day][lesson].get(class_id) is not None:
                        first_lesson = lesson
                        break
                
                # Count empty slots before the first lesson
                if first_lesson is not None and first_lesson > 1:
                    early_gaps += (first_lesson - 1)
        
        return early_gaps
    
    def _calculate_daily_imbalance(self, schedule: Dict) -> float:
        """Calculate how unevenly lessons are distributed across days."""
        imbalance = 0
        
        for cls in self.classes:
            class_id = cls['id']
            daily_counts = []
            
            for day in self.DAYS:
                count = sum(1 for lesson in range(1, self.LESSONS_PER_DAY + 1)
                           if schedule[day][lesson].get(class_id) is not None)
                daily_counts.append(count)
            
            # Calculate standard deviation
            if daily_counts:
                mean = sum(daily_counts) / len(daily_counts)
                variance = sum((x - mean) ** 2 for x in daily_counts) / len(daily_counts)
                imbalance += variance ** 0.5
        
        return imbalance
    
    def _count_total_lessons(self, schedule: Dict) -> int:
        """Count total number of lessons in the schedule."""
        count = 0
        for day in self.DAYS:
            for lesson in range(1, self.LESSONS_PER_DAY + 1):
                for class_id, assignment in schedule[day][lesson].items():
                    if assignment is not None:
                        count += 1
        return count
    
    def selection(self, population: List[Tuple[Dict, float]]) -> Dict:
        """Tournament selection: pick best from random sample."""
        tournament = random.sample(population, min(self.TOURNAMENT_SIZE, len(population)))
        return max(tournament, key=lambda x: x[1])[0]
    
    def crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """
        Single-point crossover: exchange days between parents.
        """
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)
        
        # Pick a random crossover point (day)
        crossover_point = random.randint(1, len(self.DAYS) - 1)
        
        # Exchange days after crossover point
        for i in range(crossover_point, len(self.DAYS)):
            day = self.DAYS[i]
            child1[day], child2[day] = child2[day], child1[day]
        
        return child1, child2
    
    def mutate(self, schedule: Dict) -> Dict:
        """
        Mutate schedule by randomly changing some lessons.
        30% chance to use compaction mutation (shift lessons to start of day).
        """
        mutated = copy.deepcopy(schedule)
        
        # 30% chance to use compaction mutation
        if random.random() < 0.3:
            mutated = self._compact_mutation(mutated)
        else:
            # Standard mutation: mutate a few random slots
            num_mutations = random.randint(1, 5)
            
            for _ in range(num_mutations):
                day = random.choice(self.DAYS)
                lesson = random.randint(1, self.LESSONS_PER_DAY)
                cls = random.choice(self.classes)
                
                # 50% chance to remove lesson, 50% to add/change
                if random.random() < 0.5:
                    mutated[day][lesson][cls['id']] = None
                else:
                    subject = random.choice(self.subjects)
                    available_teachers = self.teachers_by_subject.get(subject['id'], [])
                    
                    if available_teachers:
                        teacher = random.choice(available_teachers)
                        mutated[day][lesson][cls['id']] = (teacher['id'], subject['id'])
        
        return mutated
    
    def _compact_mutation(self, schedule: Dict) -> Dict:
        """
        Compact mutation: shift lessons to the start of the day for random classes.
        This helps eliminate empty slots before the first lesson.
        """
        mutated = copy.deepcopy(schedule)
        
        # Apply to 1-3 random classes
        num_classes = random.randint(1, min(3, len(self.classes)))
        selected_classes = random.sample(self.classes, num_classes)
        
        for cls in selected_classes:
            class_id = cls['id']
            
            # Apply to 1-2 random days
            num_days = random.randint(1, min(2, len(self.DAYS)))
            selected_days = random.sample(self.DAYS, num_days)
            
            for day in selected_days:
                # Collect all lessons for this class on this day
                lessons_data = []
                for lesson in range(1, self.LESSONS_PER_DAY + 1):
                    assignment = mutated[day][lesson].get(class_id)
                    if assignment is not None:
                        lessons_data.append((lesson, assignment))
                
                # If there are lessons, try to shift them to start from lesson 1
                if lessons_data:
                    # Clear current slots
                    for lesson in range(1, self.LESSONS_PER_DAY + 1):
                        mutated[day][lesson][class_id] = None
                    
                    # Check for teacher conflicts and place lessons starting from 1
                    new_lesson = 1
                    for original_lesson, assignment in lessons_data:
                        teacher_id, subject_id = assignment
                        
                        # Find next available slot without teacher conflict
                        placed = False
                        for slot in range(new_lesson, self.LESSONS_PER_DAY + 1):
                            # Check if teacher is already assigned in this slot
                            teacher_busy = False
                            for other_class_id, other_assignment in mutated[day][slot].items():
                                if other_assignment is not None and other_assignment[0] == teacher_id:
                                    teacher_busy = True
                                    break
                            
                            if not teacher_busy:
                                mutated[day][slot][class_id] = assignment
                                new_lesson = slot + 1
                                placed = True
                                break
                        
                        # If couldn't place, put back in original slot
                        if not placed:
                            mutated[day][original_lesson][class_id] = assignment
        
        return mutated
    
    def generate_schedule(self, verbose: bool = True) -> Tuple[Dict, float, int]:
        """
        Main genetic algorithm loop.
        Returns: (best_schedule, fitness_score, generation)
        """
        if verbose:
            print(f"Initializing population of {self.POPULATION_SIZE}...")
        
        # Initialize population
        population = []
        for _ in range(self.POPULATION_SIZE):
            schedule = self.create_random_schedule()
            fitness = self.calculate_fitness(schedule)
            population.append((schedule, fitness))
        
        best_schedule = None
        best_fitness = -1
        best_generation = 0
        
        # Evolution loop
        for generation in range(self.GENERATIONS):
            # Sort by fitness
            population.sort(key=lambda x: x[1], reverse=True)
            
            # Track best
            if population[0][1] > best_fitness:
                best_fitness = population[0][1]
                best_schedule = copy.deepcopy(population[0][0])
                best_generation = generation
            
            if verbose and generation % 20 == 0:
                print(f"Generation {generation}: Best fitness = {best_fitness:.2f}")
            
            # Create next generation
            next_population = []
            
            # Elitism: keep top 10%
            elite_size = self.POPULATION_SIZE // 10
            next_population.extend(population[:elite_size])
            
            # Generate offspring
            while len(next_population) < self.POPULATION_SIZE:
                # Selection
                parent1 = self.selection(population)
                parent2 = self.selection(population)
                
                # Crossover
                child1, child2 = self.crossover(parent1, parent2)
                
                # Mutation
                if random.random() < self.MUTATION_RATE:
                    child1 = self.mutate(child1)
                if random.random() < self.MUTATION_RATE:
                    child2 = self.mutate(child2)
                
                # Evaluate children
                fitness1 = self.calculate_fitness(child1)
                fitness2 = self.calculate_fitness(child2)
                
                next_population.append((child1, fitness1))
                if len(next_population) < self.POPULATION_SIZE:
                    next_population.append((child2, fitness2))
            
            population = next_population
        
        if verbose:
            print(f"\nEvolution complete!")
            print(f"Best fitness: {best_fitness:.2f}")
            print(f"Found at generation: {best_generation}")
        
        return best_schedule, best_fitness, best_generation
    
    def export_schedule(self, schedule: Dict, fitness: float, generation: int, 
                       output_path: str = "data/schedule.json") -> None:
        """
        Export schedule to JSON file in readable format.
        """
        output = {
            "schedule": {},
            "fitness_score": round(fitness, 2),
            "generation": generation,
            "statistics": self._generate_statistics(schedule)
        }
        
        # Convert schedule to readable format
        for day in self.DAYS:
            output["schedule"][day] = {}
            
            for lesson in range(1, self.LESSONS_PER_DAY + 1):
                output["schedule"][day][str(lesson)] = {}
                
                for class_id, assignment in schedule[day][lesson].items():
                    class_name = self.classes_by_id[class_id]['name']
                    
                    if assignment is not None:
                        teacher_id, subject_id = assignment
                        teacher_name = self.teachers_by_id[teacher_id]['name']
                        subject_name = self.subjects_by_id[subject_id]['name']
                        
                        output["schedule"][day][str(lesson)][class_name] = {
                            "teacher": teacher_name,
                            "subject": subject_name
                        }
                    else:
                        output["schedule"][day][str(lesson)][class_name] = None
        
        # Save to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\nSchedule saved to: {output_path}")
    
    def _generate_statistics(self, schedule: Dict) -> Dict:
        """Generate statistics about the schedule."""
        total_lessons = self._count_total_lessons(schedule)
        teacher_conflicts = self._count_teacher_conflicts(schedule)
        teacher_gaps = self._count_teacher_gaps(schedule)
        class_gaps = self._count_class_gaps(schedule)
        early_gaps = self._count_early_gaps(schedule)
        
        return {
            "total_lessons": total_lessons,
            "teacher_conflicts": teacher_conflicts,
            "teacher_gaps": teacher_gaps,
            "class_gaps": class_gaps,
            "early_gaps": early_gaps
        }
    
    def export_to_csv(self, schedule: Dict, fitness: float, generation: int,
                     output_dir: str = "data") -> None:
        """
        Export schedule to CSV files for easy viewing in Excel/Sheets.
        Creates three types of CSV files:
        1. Full schedule (all classes and days in one table)
        2. Per-day schedules (one file per day)
        3. Per-class schedules (one file per class)
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Full schedule - all classes, all days
        self._export_full_schedule_csv(schedule, output_path / "schedule_full.csv")
        
        # 2. Per-day schedules
        self._export_per_day_csv(schedule, output_path)
        
        # 3. Per-class schedules
        self._export_per_class_csv(schedule, output_path)
        
        # 4. Teacher schedule
        self._export_teacher_schedule_csv(schedule, output_path / "schedule_teachers.csv")
        
        print(f"\nCSV files saved to: {output_path}/")
        print(f"  - schedule_full.csv (complete overview)")
        print(f"  - schedule_monday.csv to schedule_friday.csv (daily)")
        print(f"  - schedule_class_*.csv (per class)")
        print(f"  - schedule_teachers.csv (teacher schedules)")
    
    def _export_full_schedule_csv(self, schedule: Dict, filepath: Path) -> None:
        """Export full schedule with classes as rows and time slots as columns."""
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # Header row
            header = ['Class']
            for day in self.DAYS:
                for lesson in range(1, self.LESSONS_PER_DAY + 1):
                    header.append(f"{day[:3]} {lesson}")
            writer.writerow(header)
            
            # Data rows - one per class
            for cls in self.classes:
                row = [cls['name']]
                
                for day in self.DAYS:
                    for lesson in range(1, self.LESSONS_PER_DAY + 1):
                        assignment = schedule[day][lesson].get(cls['id'])
                        
                        if assignment is not None:
                            teacher_id, subject_id = assignment
                            teacher_name = self.teachers_by_id[teacher_id]['name']
                            subject_name = self.subjects_by_id[subject_id]['name']
                            cell = f"{subject_name} ({teacher_name})"
                        else:
                            cell = ""
                        
                        row.append(cell)
                
                writer.writerow(row)
    
    def _export_per_day_csv(self, schedule: Dict, output_dir: Path) -> None:
        """Export one CSV file per day with classes and lessons."""
        for day in self.DAYS:
            filepath = output_dir / f"schedule_{day.lower()}.csv"
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # Header
                header = ['Class'] + [f"Lesson {i}" for i in range(1, self.LESSONS_PER_DAY + 1)]
                writer.writerow(header)
                
                # Data rows
                for cls in self.classes:
                    row = [cls['name']]
                    
                    for lesson in range(1, self.LESSONS_PER_DAY + 1):
                        assignment = schedule[day][lesson].get(cls['id'])
                        
                        if assignment is not None:
                            teacher_id, subject_id = assignment
                            teacher_name = self.teachers_by_id[teacher_id]['name']
                            subject_name = self.subjects_by_id[subject_id]['name']
                            cell = f"{subject_name}\n{teacher_name}"
                        else:
                            cell = "-"
                        
                        row.append(cell)
                    
                    writer.writerow(row)
    
    def _export_per_class_csv(self, schedule: Dict, output_dir: Path) -> None:
        """Export one CSV file per class with weekly schedule."""
        for cls in self.classes:
            filepath = output_dir / f"schedule_class_{cls['name']}.csv"
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # Header
                header = ['Lesson'] + self.DAYS
                writer.writerow(header)
                
                # Data rows - one per lesson number
                for lesson in range(1, self.LESSONS_PER_DAY + 1):
                    row = [f"Lesson {lesson}"]
                    
                    for day in self.DAYS:
                        assignment = schedule[day][lesson].get(cls['id'])
                        
                        if assignment is not None:
                            teacher_id, subject_id = assignment
                            teacher_name = self.teachers_by_id[teacher_id]['name']
                            subject_name = self.subjects_by_id[subject_id]['name']
                            cell = f"{subject_name}\n{teacher_name}"
                        else:
                            cell = "-"
                        
                        row.append(cell)
                    
                    writer.writerow(row)
    
    def _export_teacher_schedule_csv(self, schedule: Dict, filepath: Path) -> None:
        """Export teacher schedules - shows when each teacher is teaching."""
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # Header row
            header = ['Teacher']
            for day in self.DAYS:
                for lesson in range(1, self.LESSONS_PER_DAY + 1):
                    header.append(f"{day[:3]} {lesson}")
            writer.writerow(header)
            
            # Data rows - one per teacher
            for teacher in self.teachers:
                row = [teacher['name']]
                
                for day in self.DAYS:
                    for lesson in range(1, self.LESSONS_PER_DAY + 1):
                        # Find if this teacher teaches in this slot
                        teaching = None
                        for class_id, assignment in schedule[day][lesson].items():
                            if assignment is not None and assignment[0] == teacher['id']:
                                class_name = self.classes_by_id[class_id]['name']
                                subject_name = self.subjects_by_id[assignment[1]]['name']
                                teaching = f"{subject_name} ({class_name})"
                                break
                        
                        row.append(teaching if teaching else "")
                
                writer.writerow(row)
    

