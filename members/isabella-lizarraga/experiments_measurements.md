# Experiments and measurements: Isabella Lizarraga

See `members/README.md` for the rules and the entry template. Newest entry first.

### 2026-11-15: Process-pool strong scaling on the cluster (job 30371)
- **Question:** How does running time change when the fixed simulation workload is split among 1, 2, 4, 8, 16, and 32 workers?
- **Setup:** `haskell` cluster node, Premier League snapshot `--as-of 2026-11-14` (280 remaining matches), process-pool implementation, 2,000,000 seasons per run, batch size 1,000, seed 2026, five repetitions per worker configuration, `OMP_NUM_THREADS=1`; code revision `f6b012e`. Allocated **62 logical CPUs** (not the planned 64), because the 2-CPU JupyterHub interactive job plus 64 would exceed the student QoS 64-CPU per-user limit.
- **Command:** From the repository root: `sbatch --cpus-per-task=62 slurm/strong_pool.sbatch` (Slurm job **30371**). The original 64-CPU job **30369** stayed pending with `QOSMaxCpuPerUserLimit` and was canceled before any runs; job 30371 completed all 30 runs.
- **Correctness check:** Separate Slurm test job **30352** with 4 CPUs: 36 pytest tests passed (15 non-fatal multiprocessing warnings); the scaling job also ran 36 tests successfully before measuring. Tests include exact equivalence of process-pool and sequential counts at 1, 2 and 4 workers on a small deterministic example.
- **Raw results:** [`results/strong_pool/job-30371/scaling.csv`](../../results/strong_pool/job-30371/scaling.csv), 30 rows, one for each of 6 worker counts × 5 repetitions, includes node load and job ID. Times below are **median wall-clock seconds** (full `python -m src.pool` invocation) and min–max spreads:

  | Workers | Median time (s) | Min–max (s) | Speedup vs 1 | Efficiency |
  | ---: | ---: | ---: | ---: | ---: |
  | 1 | 122.611 | 122.489–123.648 | 1.000x | 100.0% |
  | 2 | 61.862 | 61.698–62.197 | 1.982x | 99.1% |
  | 4 | 31.184 | 31.029–31.511 | 3.932x | 98.3% |
  | 8 | 15.877 | 15.714–16.033 | 7.722x | 96.5% |
  | 16 | 8.782 | 8.556–8.875 | 13.961x | 87.3% |
  | 32 | 5.019 | 4.849–5.336 | 24.429x | 76.3% |

- **Other measurements:** Median pool-startup time increased from about 0.0045 s (1 worker) to 0.0391 s (32 workers). This suggests increasing parallel overhead and limited scaling at higher worker counts. From the 1-vs-32 *wall-clock* medians, the two-point Amdahl effective serial fraction is approximately 1.0%; this is an estimate from timings, not a measured code profile.
- **Conclusion:** For the fixed 2-million-season workload, 32 workers achieved a 24.43× speedup, but efficiency decreased at higher worker counts. Send CSV to Person D for the plots and note; Person A's final sign-off is still pending. Measured 62-CPU **allocation** is a documented deviation from the original 64-CPU plan; actual worker counts are unchanged. The `sacct` executable was unavailable in the JupyterHub shell, but the script printed `Completed 30 runs` and the CSV has all 30 rows.
- **Assistance:** ChatGPT helped construct the Slurm script, check CSV measurements, and draft this log; cluster jobs were submitted from the user's course account.

### 2026-11-15: One-worker workload calibration (job 30363)
- **Question:** How many seasons produce roughly a 1–2 minute single-worker run?
- **Setup:** `haskell` cluster node, 200,000 seasons, 1 worker, 2 CPUs allocated, seed 2026, batch size 1,000, snapshot 2026-11-14.
- **Command:** `python -m src.pool --as-of 2026-11-14 --seasons 200000 --batch-size 1000 --seed 2026 --workers 1 --output "results/calibration/job-${SLURM_JOB_ID}"` (submitted via `sbatch --wrap` in Slurm job 30363).
- **Result:** 12.21 seconds for simulation; approximately 122.1 s projected for 2,000,000 seasons.
- **Conclusion:** Fixed 2,000,000 seasons for the full scaling comparison.
