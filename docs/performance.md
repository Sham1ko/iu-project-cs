# Performance Testing

This document describes how to run and report GA performance benchmarks for the
timetable generator.

## Benchmark datasets

The repository includes three prepared Excel datasets for performance testing
(format A: `subjects`, `teachers`, `classes` sheets):

- `data/dataset_small.xlsx` — 6 classes, 12 teachers, 10 subjects
- `data/dataset_medium.xlsx` — 12 classes, 25 teachers, 15 subjects
- `data/dataset_large.xlsx` — 16 classes, 35 teachers, 18 subjects

These datasets are synthetic and are intended only for runtime comparisons
across different school sizes.

## How to run the benchmark

Use the benchmark script:

```
/opt/homebrew/opt/python@3.11/bin/python3.11 backend/scripts/benchmark.py \
  --excel data/dataset_small.xlsx \
  --runs 5 \
  --generations 200 \
  --population 50 \
  --mutation 0.1 \
  --tournament 5 \
  --out benchmarks/benchmark_small.csv
```

Repeat for `dataset_medium.xlsx` and `dataset_large.xlsx`, changing `--excel` and
`--out` accordingly.

The script outputs CSV with:

- `run`
- `duration_sec`
- `fitness_score`
- `generation`
- `teacher_conflicts`
- `teacher_gaps`
- `total_lessons`

## Methodology (required in the report)

When reporting results, always include:

- Hardware: CPU model, RAM
- OS version
- Python version
- Code version (git commit hash)
- Benchmark config (`runs`, `generations`, `population`, `mutation`, `tournament`)
- Dataset used (small/medium/large)

If you need reproducibility, pass a fixed `--seed` to the benchmark script.

## Result tables (templates)

### Runtime performance across school sizes

| School size | Classes | Avg runtime (min) | Avg generations | Runs | Config |
| --- | --- | --- | --- | --- | --- |
| Small | 6 | 0.029 | 93 | 5 | G=200, P=50, M=0.1, T=5 |
| Medium | 12 | 0.900 | 90 | 5 | G=200, P=50, M=0.1, T=5 |
| Large | 16 | 3.388 | 77 | 5 | G=200, P=50, M=0.1, T=5 |

Notes:

- `Avg runtime (min)` = average `duration_sec` / 60
- `Avg generations` = average `generation`

### Incremental update performance

Not available in the current codebase. The system does not implement
incremental schedule updates, so full-regeneration vs. incremental comparisons
cannot be measured at this time. If incremental scheduling is implemented in
the future, this table can be added with the same methodology:

| Update type | Full regeneration (sec) | Incremental update (sec) | Reduction |
| --- | --- | --- | --- |
| Single teacher absence | N/A (not implemented) | N/A | N/A |
| Two teacher absences | N/A (not implemented) | N/A | N/A |
| Subject hour adjustment | N/A (not implemented) | N/A | N/A |

Reduction formula: `(1 - incremental / full) * 100%`.
