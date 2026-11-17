# Simulation code

| File | What it does |
|---|---|
| `data.py` | Loads the football-data CSVs and checks each file matches its season |
| `fixtures.py` | Current table and remaining fixtures at the snapshot date |
| `strengths.py` | Team attack/defence strengths (serial, timed separately) |
| `table.py` | League-table rules and tie-breaker |
| `simulate.py` | Expected goals, batch seeds, one batch of seasons |
| `baseline.py` | Sequential version: runs all batches in one process |
| `pool.py` | Process-pool version: one batch per task |
| `array_task.py`, `merge_array.py` | Slurm job-array version and the script that adds up the counts |
| `profile_lines.py` | Line-by-line profile of `simulate_batch` |
| `backtest.py`, `naive_baselines.py` | Model checks on past seasons |

See [the guide](../docs/BASELINE_GUIDE.md) for how to run them.
