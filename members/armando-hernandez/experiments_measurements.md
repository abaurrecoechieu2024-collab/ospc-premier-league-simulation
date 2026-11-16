# Experiments and measurements: Armando Hernandez

See `members/README.md` for the rules and the entry template. Newest entry first.
### 2026-11-16: Task D - Process-pool scaling test

- **Question:** Does increasing the number of workers improve simulation performance while keeping the results correct?
- **Setup:** 100,000 Premier League seasons, snapshot 2026-11-14, batch size 1,000, seed 2026. Preliminary interactive test on haskell, with a Slurm allocation limited to 2 CPUs.
- **Command:** `OMP_NUM_THREADS=1 python -m src.pool --as-of 2026-11-14 --seasons 100000 --batch-size 1000 --seed 2026 --workers "$w" --output "results/scaling-pool-${w}w"` (tested with w = 1, 2, 4).
- **Result:** The 1-worker run took 7.42 seconds and the 2-worker run took 5.09 seconds. Preliminary speedup was 1.46x, with 72.9% efficiency. The 4-worker attempt failed because SLURM_CPUS_PER_TASK was 2. Raw timings are saved in `results/scaling-pool-1w/timing.csv` and `results/scaling-pool-2w/timing.csv`.
- **Conclusion:** Two workers improved performance, but the speedup was below the ideal 2x. These interactive measurements are exploratory, not official cluster batch benchmarks. More worker counts and repeated cluster runs are still needed.

### 2026-11-16: Task D - Correctness verification

- **Question:** Do the sequential and parallel versions produce identical simulation results?
- **Setup:** 100,000 seasons, snapshot 2026-11-14, batch size 1,000, seed 2026. Preliminary interactive checks.
- **Command:** `python -m src.merge_array --folder results/array-100k-test --baseline results/baseline-100k-test/counts.csv`. Process-pool results were also compared against the baseline using pandas `DataFrame.equals()`.
- **Result:** The four array tasks merged successfully and produced counts equal to the sequential baseline. Both the 1-worker and 2-worker process-pool results also matched the baseline exactly.
- **Conclusion:** The tested parallel implementations preserved correctness for this workload. Full cluster scaling and automated tests are still required.
### 2026-11-15: Baseline simulation test

- **Question:** How long does it take to simulate 1 million Premier League seasons?
- **Setup:** I checked the results of an existing cluster job (Job 29781, run by Theo) that simulated 1 million seasons using 2 CPUs and 2 GB of memory. I used the data from 2026-11-14 and set OMP_NUM_THREADS=1.
- **Command:** `sbatch slurm/characterize.sbatch` (runs `python -m src.baseline --as-of 2026-11-14 --seasons 1000000 --output results/characterize/job-29781`).
- **Result:** The simulation took 61.23 seconds. The full job took 62 seconds. CPU usage was around 99%, and memory usage was around 114 MB. Everything ran successfully. The results are saved in `results/characterize/characterize-29781.out` and `results/characterize/sacct-29781.txt`.
- **Conclusion:** These results show how fast the original simulation runs. We can use these results later to compare it with the parallel version.
