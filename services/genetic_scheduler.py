import random
import copy
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from services.data_service import DataService
from services.fitness_metrics import (
    count_teacher_conflicts,
    count_teacher_gaps,
    count_class_gaps,
    count_early_gaps,
    calculate_daily_imbalance,
    count_total_lessons,
    count_min_daily_lessons_deficit,
)
from services.schedule_compaction import compact_mutation, compact_schedule_full


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
        
        # Bias: ensure at least 2 lessons per day per class where possible
        for cls in self.classes:
            class_id = cls['id']
            for day in self.DAYS:
                # count current lessons for this class/day
                current_lessons = [l for l in range(1, self.LESSONS_PER_DAY + 1)
                                   if schedule[day][l].get(class_id) is not None]
                missing = max(0, 2 - len(current_lessons))
                if missing <= 0:
                    continue
                # Try to add up to 'missing' lessons in free/feasible slots
                tries = 0
                while missing > 0 and tries < self.LESSONS_PER_DAY * 2:
                    tries += 1
                    slot = random.randint(1, self.LESSONS_PER_DAY)
                    if schedule[day][slot].get(class_id) is not None:
                        continue  # already has lesson
                    # pick a random subject
                    subject = random.choice(self.subjects)
                    available_teachers = self.teachers_by_subject.get(subject['id'], [])
                    # find teacher not already assigned in this slot
                    teacher_in_slot = {tup[0] for tup in
                                       [v for v in schedule[day][slot].values() if v is not None]}
                    free_teachers = [t for t in available_teachers if t['id'] not in teacher_in_slot]
                    if not free_teachers:
                        continue
                    teacher = random.choice(free_teachers)
                    schedule[day][slot][class_id] = (teacher['id'], subject['id'])
                    missing -= 1
        
        return schedule
    
    def calculate_fitness(self, schedule: Dict) -> float:
        """
        Calculate fitness score for a schedule.
        Higher score = better schedule.
        Score is reduced by penalties for constraint violations.
        """
        score = 1000.0  # Start with perfect score
        
        # Hard constraint penalties
        teacher_conflicts = count_teacher_conflicts(
            schedule, self.teachers_by_id, self.DAYS, self.LESSONS_PER_DAY
        )
        score -= teacher_conflicts * 100  # Heavy penalty for teacher conflicts
        
        # Soft constraint penalties
        teacher_gaps = count_teacher_gaps(
            schedule, self.teachers, self.DAYS, self.LESSONS_PER_DAY
        )
        score -= teacher_gaps * 2  # Penalty for teacher gaps
        
        class_gaps = count_class_gaps(
            schedule, self.classes, self.DAYS, self.LESSONS_PER_DAY
        )
        score -= class_gaps * 10  # Very strong penalty for gaps between lessons
        
        early_gaps = count_early_gaps(
            schedule, self.classes, self.DAYS, self.LESSONS_PER_DAY
        )
        score -= early_gaps * 15  # Very strong penalty for empty slots before first lesson
        
        imbalance = calculate_daily_imbalance(
            schedule, self.classes, self.DAYS, self.LESSONS_PER_DAY
        )
        score -= imbalance * 1  # Penalty for uneven distribution
        
        # Bonus for having lessons
        total_lessons = count_total_lessons(
            schedule, self.DAYS, self.LESSONS_PER_DAY
        )
        score += total_lessons * 0.5  # Small bonus for each lesson
        
        # Hard-ish constraint: minimum 2 lessons per day for each class
        min_daily_deficit = count_min_daily_lessons_deficit(
            schedule, self.classes, self.DAYS, self.LESSONS_PER_DAY, min_lessons_per_day=2
        )
        score -= min_daily_deficit * 80  # Heavy penalty per missing lesson toward minimum
        
        return max(0, score)  # Ensure non-negative score
    
    
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
        60% chance to use compaction mutation (shift lessons to start of day).
        """
        mutated = copy.deepcopy(schedule)
        
        # 60% chance to use compaction mutation (increased for better compactness)
        if random.random() < 0.6:
            mutated = compact_mutation(
                mutated, self.DAYS, self.LESSONS_PER_DAY, self.classes
            )
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
        
        # Post-processing: Fully compact the best schedule
        if verbose:
            print(f"\nApplying final compaction to remove all gaps...")
        
        best_schedule = compact_schedule_full(
            best_schedule, self.DAYS, self.LESSONS_PER_DAY, self.classes
        )
        best_fitness = self.calculate_fitness(best_schedule)
        
        if verbose:
            print(f"\nEvolution complete!")
            print(f"Best fitness (after compaction): {best_fitness:.2f}")
            print(f"Found at generation: {best_generation}")
        
        return best_schedule, best_fitness, best_generation

