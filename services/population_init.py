from typing import Any, Dict, List


def initialize_population(
    population_size: int,
    create_random_schedule,
) -> List[Dict[str, Any]]:
    """
    Initialize genetic algorithm population with random schedules.

    Parameters
    ----------
    population_size:
        Number of individuals in the population.
    create_random_schedule:
        Callable that returns a new random schedule (chromosome).
    """
    population: List[Dict[str, Any]] = []

    for _ in range(population_size):
        schedule = create_random_schedule()
        population.append(schedule)

    return population
