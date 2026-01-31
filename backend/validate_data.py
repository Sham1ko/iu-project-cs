"""
Compatibility wrapper for the validation CLI.
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from app.core.validation import DataValidator  # noqa: E402


def main() -> None:
    data_dir = ROOT_DIR / "data"
    validator = DataValidator(data_dir=str(data_dir))
    validator.validate_all()


if __name__ == "__main__":
    main()
