"""
Compatibility wrapper for the validation CLI.
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from app.core.validation import main  # noqa: E402


if __name__ == "__main__":
    main()
