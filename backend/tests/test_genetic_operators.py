from app.core.ga.genetic_scheduler import GeneticScheduler
from app.core.io.data_service import DataService


def _make_scheduler() -> GeneticScheduler:
    payload = {
        "subjects": [{"id": 1, "name": "Math"}],
        "teachers": [{"id": 1, "name": "Alice", "subjects": [1]}],
        "classes": [{"id": 1, "name": "5A", "grade": 5}],
    }
    return GeneticScheduler(DataService(payload=payload))


def _build_parent(days: list[str], lessons_per_day: int, class_id: int, marker: int):
    schedule = {}
    for day_index, day in enumerate(days):
        schedule[day] = {}
        for lesson in range(1, lessons_per_day + 1):
            schedule[day][lesson] = {class_id: None}
        schedule[day][1][class_id] = (marker, 100 + day_index)
    return schedule


def test_crossover_swaps_days(monkeypatch) -> None:
    scheduler = _make_scheduler()

    parent1 = _build_parent(scheduler.DAYS, scheduler.LESSONS_PER_DAY, 1, marker=1)
    parent2 = _build_parent(scheduler.DAYS, scheduler.LESSONS_PER_DAY, 1, marker=2)

    monkeypatch.setattr("random.randint", lambda *_: 2)

    child1, child2 = scheduler.crossover(parent1, parent2)

    for i, day in enumerate(scheduler.DAYS):
        slot1 = child1[day][1][1][0]
        slot2 = child2[day][1][1][0]
        if i < 2:
            assert slot1 == 1
            assert slot2 == 2
        else:
            assert slot1 == 2
            assert slot2 == 1
