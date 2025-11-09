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
)


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
        This helps eliminate empty slots before the first lesson and between lessons.
        """
        mutated = copy.deepcopy(schedule)
        
        # Apply to 2-5 random classes (increased for better coverage)
        num_classes = random.randint(2, min(5, len(self.classes)))
        selected_classes = random.sample(self.classes, num_classes)
        
        for cls in selected_classes:
            class_id = cls['id']
            
            # Apply to 2-4 random days (increased for better coverage)
            num_days = random.randint(2, min(4, len(self.DAYS)))
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
    
    def _compact_schedule_full(self, schedule: Dict) -> Dict:
        """
        Fully compact the schedule: remove all gaps for all classes on all days.
        This is a post-processing step to ensure lessons start from lesson 1
        and have no gaps between them.
        Uses multiple passes to achieve better compaction.
        """
        compacted = copy.deepcopy(schedule)
        
        # Multiple passes to improve compaction
        for pass_num in range(3):  # 3 passes for better results
            improved = False
            
            for cls in self.classes:
                class_id = cls['id']
                
                for day in self.DAYS:
                    # Collect all lessons for this class on this day
                    lessons_data = []
                    for lesson in range(1, self.LESSONS_PER_DAY + 1):
                        assignment = compacted[day][lesson].get(class_id)
                        if assignment is not None:
                            lessons_data.append((lesson, assignment))
                    
                    # Skip if no lessons or already compact
                    if not lessons_data:
                        continue
                    
                    # Check if already compact
                    lesson_numbers = [l for l, _ in lessons_data]
                    expected_compact = list(range(1, len(lessons_data) + 1))
                    if lesson_numbers == expected_compact:
                        continue  # Already compact
                    
                    # Try to compact
                    # Clear current slots
                    for lesson in range(1, self.LESSONS_PER_DAY + 1):
                        compacted[day][lesson][class_id] = None
                    
                    # Sort lessons by their original position to try maintaining order
                    lessons_data.sort(key=lambda x: x[0])
                    
                    # Try multiple orderings to find best compaction
                    best_placement = None
                    min_last_slot = self.LESSONS_PER_DAY + 1
                    
                    # Try original order
                    placement = self._try_compact_placement(compacted, day, class_id, lessons_data)
                    if placement:
                        last_slot = max(slot for slot, _ in placement)
                        if last_slot < min_last_slot:
                            min_last_slot = last_slot
                            best_placement = placement
                    
                    # Try reversed order (sometimes helps with teacher conflicts)
                    lessons_data_rev = lessons_data[::-1]
                    placement = self._try_compact_placement(compacted, day, class_id, lessons_data_rev)
                    if placement:
                        last_slot = max(slot for slot, _ in placement)
                        if last_slot < min_last_slot:
                            min_last_slot = last_slot
                            best_placement = placement
                    
                    # Apply best placement
                    if best_placement:
                        for slot, assignment in best_placement:
                            compacted[day][slot][class_id] = assignment
                            if slot < lesson_numbers[0]:
                                improved = True
                    else:
                        # Restore original if no improvement possible
                        for lesson, assignment in lessons_data:
                            compacted[day][lesson][class_id] = assignment
            
            # If no improvements in this pass, we're done
            if not improved:
                break
        
        return compacted
    
    def _try_compact_placement(self, schedule: Dict, day: str, class_id: int, 
                               lessons_data: List[Tuple[int, Tuple[int, int]]]) -> List[Tuple[int, Tuple[int, int]]]:
        """
        Try to place lessons compactly starting from slot 1.
        Returns list of (slot, assignment) if successful, None otherwise.
        """
        placement = []
        next_slot = 1
        
        for _, assignment in lessons_data:
            teacher_id, subject_id = assignment
            
            # Find next available slot without teacher conflict
            placed = False
            for slot in range(next_slot, self.LESSONS_PER_DAY + 1):
                # Check if teacher is already assigned in this slot
                teacher_busy = False
                for other_class_id, other_assignment in schedule[day][slot].items():
                    if other_class_id != class_id and other_assignment is not None:
                        if other_assignment[0] == teacher_id:
                            teacher_busy = True
                            break
                
                if not teacher_busy:
                    placement.append((slot, assignment))
                    next_slot = slot + 1
                    placed = True
                    break
            
            if not placed:
                # Can't place all lessons compactly
                return None
        
        return placement
    
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
        
        best_schedule = self._compact_schedule_full(best_schedule)
        best_fitness = self.calculate_fitness(best_schedule)
        
        if verbose:
            print(f"\nEvolution complete!")
            print(f"Best fitness (after compaction): {best_fitness:.2f}")
            print(f"Found at generation: {best_generation}")
        
        return best_schedule, best_fitness, best_generation

