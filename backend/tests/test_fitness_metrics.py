from app.core.ga.fitness_metrics import calculate_schedule_fitness


def test_fitness_penalties_and_bonus() -> None:
    days = ["Mon"]
    lessons_per_day = 2

    teachers = [
        {"id": 1, "name": "Alice", "subjects": [1]},
        {"id": 2, "name": "Bob", "subjects": [1]},
    ]
    classes = [{"id": 1, "name": "5A"}, {"id": 2, "name": "5B"}]
    teachers_by_id = {t["id"]: t for t in teachers}

    schedule = {
        "Mon": {
            1: {1: (1, 1), 2: (1, 1)},  # teacher conflict (double-booked)
            2: {1: None, 2: None},
        }
    }

    score = calculate_schedule_fitness(
        schedule,
        days=days,
        lessons_per_day=lessons_per_day,
        teachers=teachers,
        classes=classes,
        teachers_by_id=teachers_by_id,
    )

    # Base 1000 - conflict(1*100) - min_daily_deficit(2*80) + total_lessons(2*0.5)
    assert score == 741.0


def test_fitness_prefers_single_pair_per_day() -> None:
    days = ["Mon"]
    lessons_per_day = 4

    teachers = [{"id": 1, "name": "Alice", "subjects": [1, 2]}]
    classes = [{"id": 1, "name": "5A"}]
    teachers_by_id = {1: teachers[0]}

    # One pair: lessons 1-2 have same subject.
    one_pair_schedule = {
        "Mon": {
            1: {1: (1, 1)},
            2: {1: (1, 1)},
            3: {1: (1, 2)},
            4: {1: None},
        }
    }

    # Two pairs in one day: lessons 1-2 and 3-4 are pairs.
    two_pairs_schedule = {
        "Mon": {
            1: {1: (1, 1)},
            2: {1: (1, 1)},
            3: {1: (1, 2)},
            4: {1: (1, 2)},
        }
    }

    score_one_pair = calculate_schedule_fitness(
        one_pair_schedule,
        days=days,
        lessons_per_day=lessons_per_day,
        teachers=teachers,
        classes=classes,
        teachers_by_id=teachers_by_id,
        min_lessons_per_day=0,
    )
    score_two_pairs = calculate_schedule_fitness(
        two_pairs_schedule,
        days=days,
        lessons_per_day=lessons_per_day,
        teachers=teachers,
        classes=classes,
        teachers_by_id=teachers_by_id,
        min_lessons_per_day=0,
    )

    # Second schedule has one extra pair in the same day, so it should be penalized.
    assert score_one_pair > score_two_pairs
