# Experiments and measurements: Armando Hernandez

See `members/README.md` for the rules and the entry template. Newest entry first.

### 2026-11-15: Baseline simulation test

- **Question:** How long does it take to simulate 1 million Premier League seasons?
- **Setup:** I ran 1 million seasons on the university cluster using 2 CPUs and 2 GB of memory (Job 29781). I used the data from 2026-11-14 and set OMP_NUM_THREADS=1.
- **Command:** `sbatch slurm/characterize.sbatch` (runs `python -m src.baseline --as-of 2026-11-14 --seasons 1000000 --output results/characterize/job-29781`).
- **Result:** The simulation took 61.23 seconds. The full job took 62 seconds. CPU usage was around 99%, and memory usage was around 114 MB. Everything ran successfully. The results are saved in `results/characterize/characterize-29781.out` and `results/characterize/sacct-29781.txt`.
- **Conclusion:** This test shows how fast the original simulation runs. We can use these results later to compare it with the parallel version.
