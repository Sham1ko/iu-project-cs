import argparse
import csv
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.io.excel_loader import load_dataset_from_excel
from app.core.timetable_generation import generate_timetable


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_excel_path() -> Path:
    return _repo_root() / "data" / "dataset.xlsx"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _run_benchmark(
    payload: Dict[str, Any],
    runs: int,
    config: Dict[str, Any],
    seed: int | None,
    with_pdf: bool,
    pdf_dir: Path,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for idx in range(1, runs + 1):
        if seed is not None:
            random.seed(seed + idx)
        run_config = dict(config)
        if with_pdf:
            _ensure_parent(pdf_dir / "placeholder.txt")
            run_config["output_dir"] = str(pdf_dir)
            run_config["pdf_title"] = f"Benchmark Schedule {idx}"
            run_config["pdf_filename"] = f"schedule_bench_{idx}.pdf"
        start = time.perf_counter()
        result = generate_timetable(payload, run_config)
        duration = time.perf_counter() - start

        stats = result.get("statistics", {})
        results.append(
            {
                "run": idx,
                "duration_sec": round(duration, 4),
                "fitness_score": result.get("fitness_score"),
                "generation": result.get("generation"),
                "teacher_conflicts": stats.get("teacher_conflicts"),
                "teacher_gaps": stats.get("teacher_gaps"),
                "total_lessons": stats.get("total_lessons"),
            }
        )
    return results


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    _ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="GA performance benchmark")
    parser.add_argument(
        "--excel",
        type=Path,
        default=_default_excel_path(),
        help="Path to dataset.xlsx (default: data/dataset.xlsx)",
    )
    parser.add_argument("--runs", type=int, default=5, help="Number of runs")
    parser.add_argument("--generations", type=int, default=200, help="GA generations")
    parser.add_argument("--population", type=int, default=50, help="Population size")
    parser.add_argument("--mutation", type=float, default=0.1, help="Mutation rate")
    parser.add_argument("--tournament", type=int, default=5, help="Tournament size")
    parser.add_argument("--seed", type=int, default=None, help="Base random seed")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("benchmarks/benchmark_results.csv"),
        help="CSV output path",
    )
    parser.add_argument(
        "--with-pdf",
        action="store_true",
        help="Generate PDF files for each run",
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=Path("benchmarks/pdfs"),
        help="Directory for PDF outputs (used with --with-pdf)",
    )
    args = parser.parse_args()

    if not args.excel.exists():
        raise FileNotFoundError(f"Excel dataset not found: {args.excel}")

    payload = load_dataset_from_excel(args.excel)

    config: Dict[str, Any] = {
        "population_size": args.population,
        "generations": args.generations,
        "mutation_rate": args.mutation,
        "tournament_size": args.tournament,
    }

    if args.with_pdf:
        _ensure_parent(args.pdf_dir / "placeholder.txt")

    rows = _run_benchmark(
        payload,
        args.runs,
        config,
        args.seed,
        args.with_pdf,
        args.pdf_dir,
    )

    _write_csv(args.out, rows)

    durations = [row["duration_sec"] for row in rows]
    avg = sum(durations) / len(durations)
    print(f"Runs: {args.runs}")
    print(f"Average duration: {avg:.2f}s")
    print(f"Results written to: {args.out}")


if __name__ == "__main__":
    main()
