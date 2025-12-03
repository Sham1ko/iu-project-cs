import copy
import random
from pathlib import Path
from typing import Dict, List, Tuple

from services.io.data_service import DataService

from .fitness_metrics import calculate_schedule_fitness
from .population_init import initialize_population
from .schedule_compaction import compact_mutation, compact_schedule_full


def get_next_version_dir(base_dir: str = "data") -> Path:
    """
    Find the next version directory (v1, v2, v3, ...).
    Returns the path to the next version directory.
    """
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    # Find all existing version directories
    version_dirs = [
        d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("v")
    ]

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
        self.teachers_by_id = {t["id"]: t for t in self.teachers}
        self.classes_by_id = {c["id"]: c for c in self.classes}
        self.subjects_by_id = {s["id"]: s for s in self.subjects}

        # Map subjects to available teachers
        self.teachers_by_subject = {}
        for subject in self.subjects:
            self.teachers_by_subject[subject["id"]] = [
                t for t in self.teachers if subject["id"] in t["subjects"]
            ]

    def calculate_fitness(self, schedule: Dict) -> float:
        return calculate_schedule_fitness(
            schedule,
            days=self.DAYS,
            lessons_per_day=self.LESSONS_PER_DAY,
            teachers=self.teachers,
            classes=self.classes,
            teachers_by_id=self.teachers_by_id,
        )

    def selection(self, population: List[Tuple[Dict, float]]) -> Dict:
        """Tournament selection: pick best from random sample."""
        tournament = random.sample(
            population, min(self.TOURNAMENT_SIZE, len(population))
        )
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
                    mutated[day][lesson][cls["id"]] = None
                else:
                    subject = random.choice(self.subjects)
                    available_teachers = self.teachers_by_subject.get(subject["id"], [])

                    if available_teachers:
                        teacher = random.choice(available_teachers)
                        mutated[day][lesson][cls["id"]] = (teacher["id"], subject["id"])

        return mutated

    def generate_schedule(self, verbose: bool = True) -> Tuple[Dict, float, int]:
        """
        Main genetic algorithm loop.
        Returns: (best_schedule, fitness_score, generation)
        """
        if verbose:
            print(f"Initializing population of {self.POPULATION_SIZE}...")

        schedules = initialize_population(
            self.POPULATION_SIZE,
            self.classes,
            self.subjects,
            self.teachers_by_subject,
            self.DAYS,
            self.LESSONS_PER_DAY,
        )
        population = [
            (schedule, self.calculate_fitness(schedule)) for schedule in schedules
        ]

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
            print("\nApplying final compaction to remove all gaps...")

        # Fix: Ensure best_schedule is not None before passing to compact_schedule_full
        if best_schedule is not None:
            best_schedule = compact_schedule_full(
                best_schedule, self.DAYS, self.LESSONS_PER_DAY, self.classes
            )
            best_fitness = self.calculate_fitness(best_schedule)
        else:
            best_schedule = {}
            best_fitness = 0.0

        if verbose:
            print("\nEvolution complete!")
            print(f"Best fitness (after compaction): {best_fitness:.2f}")
            print(f"Found at generation: {best_generation}")

        return best_schedule, best_fitness, best_generation
