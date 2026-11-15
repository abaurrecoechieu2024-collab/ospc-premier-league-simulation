# Experiments and measurements: Anarella Furoiani

See `members/README.md` for the rules and the entry template. Newest entry first.

### 2026-11-15: Slurm job-array test (additional technique)
- **Question:** do 4 Slurm array tasks, each simulating its own block of batches, reproduce the baseline counts exactly? How much does the scheduler cost?
- **Setup:** snapshot 2026-11-14, 100,000 seasons, batch size 1000, seed 2026; `--array=0-3%4`, 2 CPUs (1 core) per task, `OMP_NUM_THREADS=1`. Cluster job **30256**, all 4 tasks on haskell. Reference baseline (100,000 seasons) run in the JupyterLab session, used only for the equality check.
- **Command:** `mkdir -p results/array && sbatch slurm/array_test.sbatch`, then `python -m src.merge_array --folder results/array/job-30256 --baseline results/array/baseline-100k/counts.csv`
- **Result:** merged counts **EQUAL to the baseline** (100,000 seasons per team). Each task: 25 batches, ~1.5 s of simulation (1.53, 1.54, 1.53, 1.68 s). Queue wait from `sacct`: tasks 0–2 waited **25 s**, task 3 waited **55 s** (submitted 19:03:25, started 19:03:50 / 19:04:20). Files: `results/array/job-30256/` (counts, timings, `sacct-30256.txt`).
- **Conclusion:** the array version is correct. At this size the scheduler overhead (25–55 s) is ~20–35x the useful work (~1.5 s per task), so job arrays only pay off when each task runs for minutes. Next: full-size run with `--array=0-7%4` spread over both nodes, compared with the process pool.

### 2026-11-15: Profile of the sequential baseline
- **Question:** where does the baseline spend its time, and what fraction can be parallelized?
- **Setup:** snapshot 2026-11-14, batch size 1000, seed 2026, 1 core (2 CPUs), `OMP_NUM_THREADS=1`. cProfile with 200,000 seasons; line_profiler on `simulate_batch` with 20,000 seasons. Cluster job **30261**. (First explored on my laptop on 2026-11-14 with the same commands; same pattern.)
- **Command:** `mkdir -p results/profile && sbatch slurm/profile.sbatch` (runs `python -m cProfile -m src.baseline ...` and `python -m src.profile_lines ...`)
- **Result (cProfile, simulation = 19.92 s):**

  | Part | Time | Share of simulation |
  |---|---|---|
  | Building tables (`update_table`, 56 M calls) | 7.78 s | 39% |
  | Season loop itself (copy, zip, tolist) | 8.06 s | 40% |
  | Generating goals (`generate_batch`) | 3.05 s | 15% |
  | Ranking (`rank_teams`) | 1.03 s | 5% |
  | Serial: `prepare` (load + fit) | 0.088 s | – |
  | Serial: `write_results` | 0.071 s | – |

  line_profiler: line 50 (`update_table`) 79.5% and line 49 (match loop) 12.5% of `simulate_batch`. Files: `results/profile/job-30261/`.
- **Conclusion:** parallel fraction from profiling ≈ **99.2%** (serial 0.16 s of 20.09 s ≈ 0.8%), so Amdahl's limit is ≈ 1/0.008 ≈ 125x, far above 32 workers. The bottleneck is building tables in a Python loop (~92% of `simulate_batch`), not generating goals: the pool parallelizes all of it, and a vectorized version must replace lines 49–50 to be faster. Note: the profilers add overhead to Python lines, so use the shares, not the absolute times.
