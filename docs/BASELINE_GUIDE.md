# Sequential baseline: start here

## How a run flows through the code
| Stage | File | Functions | Timed as |
|---|---|---|---|
| 1. Load data (serial) | `src/data.py` | `load_all()`, `load_matches()` | `loading_seconds` |
| 1. Current table, fixtures (serial) | `src/fixtures.py` | `current_matches()`, `team_list()`, `current_standings()`, `remaining_fixtures()` | `loading_seconds` |
| 1. Fit strengths (serial) | `src/strengths.py` | `fit_strengths()`, `promotion_factors()` | `fitting_seconds` |
| 1. Expected goals (serial) | `src/simulate.py` | `expected_goals()` | `fitting_seconds` |
| 2. Simulate (parallel part) | `src/simulate.py` | `batch_seeds()`, `generate_batch()`, `simulate_batch()` | `simulation_seconds` |
| Process-pool startup | `src/pool.py` | process creation, worker initialization, warm-up, and readiness synchronization | `pool_startup_seconds` |
| 2. Table rules | `src/table.py` | `update_table()`, `rank_teams()` | inside simulation |
| 3. Combine and write (serial) | `src/baseline.py` | `run_baseline()`, `summarize()`, `write_results()` | `writing_seconds` |

Every parallel version reuses stages 1 and 3 (`prepare()`, `write_results()`) and
only changes how the batches of stage 2 are run.

## Run it (laptop or cluster terminal)
From the repository root, with the course Python (on the cluster:
`export PATH=/data/software/envs/ospc/bin:$PATH`):

```bash
pytest -q
python -m src.baseline --as-of 2026-11-14 --seasons 1000 --output results/my-first-run
python -m src.pool --as-of 2026-11-14 --seasons 1000 --workers 4 --output results/my-pool-run
```

Use a **new output folder** for every run. Each run writes:
- `probabilities.csv`: title, top 4, top 6 and relegation probability per team.
- `counts.csv`: how often each team finished in each position (20 × 20, integers).
- `current_table.csv`: the table at the snapshot date.
- `timing.csv`: one row with the timings, node, Slurm job ID, date and node load.

For process-pool runs, `timing.csv` also records `pool_startup_seconds`, separately
from the batch `simulation_seconds`. Set the worker count explicitly with `--workers`;
it is never inferred from the machine's CPU count. In a Slurm job, the requested
worker count must not exceed `SLURM_CPUS_PER_TASK`; outside Slurm, local execution
uses the explicitly requested count. Each worker receives the simulation inputs
once at initialization, and each submitted task contains only its batch size and
seed stream.

## Batch job on the cluster
```bash
sbatch slurm/baseline.sbatch                   # 10,000 seasons, 5 repetitions
SEASONS=200000 sbatch slurm/baseline.sbatch    # bigger size
```

## Decisions built into the code
- **Snapshot:** 2026/27 results up to 14 November 2026 (100 matches, 280 left), frozen.
- **Training data:** every `E0_*.csv` and `E1_*.csv` in `data/raw/`; see `data/README.md`.
- **Strengths:** 3 past Premier League seasons + this season, weight 0.5 per season
  back; Championship conversion off by default. Why: `docs/VALIDATION.md`.
- **Ranking:** points → goal difference → goals scored → random draw.
- **Randomness:** fixed batches (`--batch-size`, default 1000) with one
  `SeedSequence.spawn` stream each. A batch draws all its goals first, then its
  tie-break numbers. Never tie the batch size to the number of workers.
- **Correctness:** every version must produce exactly the same `counts.csv`.

## Speed so far (laptop, not cluster evidence)
10,000 seasons took about 1.1 s, so a 10-minute baseline needs roughly 5 million
seasons. Measure again on the cluster before choosing the final size.
