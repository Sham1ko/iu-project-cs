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
