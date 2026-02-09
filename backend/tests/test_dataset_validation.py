from app.core.dataset_validation import validate_dataset_payload


def test_validation_errors_for_missing_teachers() -> None:
    payload = {
        "subjects": [{"id": 1, "name": "Math", "weekly_hours": 2}],
        "teachers": [],
        "classes": [{"id": 1, "name": "5A", "grade": 5}],
    }

    errors, warnings = validate_dataset_payload(payload)

    assert any("Dataset has no teachers" in err for err in errors)
    assert any("No qualified teacher" in err for err in errors)
    assert warnings == []


def test_validation_warnings_for_inconsistent_teacher_names() -> None:
    payload = {
        "subjects": [{"id": 1, "name": "Math"}],
        "teachers": [
            {"id": 1, "name": "Alice", "subjects": [1]},
            {"id": 2, "name": "alice", "subjects": [1]},
        ],
        "classes": [{"id": 1, "name": "5A", "grade": 5}],
    }

    errors, warnings = validate_dataset_payload(payload)

    assert errors == []
    assert any("inconsistent naming variants" in warning for warning in warnings)
