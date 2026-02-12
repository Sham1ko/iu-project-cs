import random
from pathlib import Path

from app.core.timetable_generation import generate_timetable


def _sample_payload():
    return {
        "subjects": [
            {"id": 1, "name": "Math"},
            {"id": 2, "name": "English"},
        ],
        "teachers": [
            {"id": 1, "name": "Alice", "subjects": [1]},
            {"id": 2, "name": "Bob", "subjects": [2]},
        ],
        "classes": [
            {"id": 1, "name": "5A", "grade": 5},
        ],
    }


def test_generate_timetable_end_to_end(tmp_path: Path) -> None:
    random.seed(0)
    payload = _sample_payload()
    config = {
        "population_size": 8,
        "generations": 5,
        "mutation_rate": 0.1,
        "tournament_size": 3,
        "output_dir": tmp_path,
        "pdf_filename": "schedule_test.pdf",
    }

    result = generate_timetable(payload, config)

    assert "schedule" in result
    assert "fitness_score" in result
    assert "statistics" in result
    assert set(result["statistics"].keys()) == {
        "total_lessons",
        "teacher_conflicts",
        "teacher_gaps",
    }
    assert set(result["schedule"].keys()) == {
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    }

    pdf_path = tmp_path / "schedule_test.pdf"
    assert pdf_path.exists()


def test_generate_timetable_respects_contiguity_and_hour_targets(tmp_path: Path) -> None:
    random.seed(1)
    payload = {
        "subjects": [
            {"id": 1, "name": "Math", "weekly_hours_by_class": {1: 2, 2: 2}},
            {"id": 2, "name": "English", "weekly_hours_by_class": {1: 1, 2: 1}},
        ],
        "teachers": [
            {
                "id": 1,
                "name": "Alice",
                "subjects": [1, 2],
                "groups": [1],
                "max_weekly_hours": 3,
            },
            {
                "id": 2,
                "name": "Bob",
                "subjects": [1, 2],
                "groups": [2],
                "max_weekly_hours": 3,
            },
        ],
        "classes": [
            {"id": 1, "name": "9A", "grade": 9},
            {"id": 2, "name": "9B", "grade": 9},
        ],
    }
    config = {
        "population_size": 8,
        "generations": 50,
        "mutation_rate": 0.1,
        "tournament_size": 3,
        "output_dir": tmp_path,
        "pdf_filename": "schedule_matrix_test.pdf",
    }

    result = generate_timetable(payload, config)
    schedule = result["schedule"]
    class_names = ["9A", "9B"]

    # Lessons for each class on each day must be contiguous and start from lesson 1.
    for day, day_schedule in schedule.items():
        for class_name in class_names:
            lesson_numbers = []
            for lesson_key, lesson_schedule in day_schedule.items():
                if lesson_schedule.get(class_name) is not None:
                    lesson_numbers.append(int(lesson_key))
            lesson_numbers.sort()
            if not lesson_numbers:
                continue
            assert lesson_numbers[0] == 1
            assert lesson_numbers == list(range(1, len(lesson_numbers) + 1))

    # First lesson start time for classes that have lessons must match (lesson 1).
    for day, day_schedule in schedule.items():
        starts = []
        for class_name in class_names:
            class_lessons = sorted(
                int(lesson_key)
                for lesson_key, lesson_schedule in day_schedule.items()
                if lesson_schedule.get(class_name) is not None
            )
            if class_lessons:
                starts.append(class_lessons[0])
        if starts:
            assert set(starts) == {1}

    # Weekly subject-hour targets per class must match exactly.
    expected = {
        ("9A", "Math"): 2,
        ("9A", "English"): 1,
        ("9B", "Math"): 2,
        ("9B", "English"): 1,
    }
    actual = {key: 0 for key in expected}
    for day_schedule in schedule.values():
        for lesson_schedule in day_schedule.values():
            for class_name, entry in lesson_schedule.items():
                if entry is None:
                    continue
                key = (class_name, entry["subject"])
                if key in actual:
                    actual[key] += 1

    assert actual == expected
