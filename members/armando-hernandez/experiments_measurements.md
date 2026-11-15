# Experiments and measurements: Armando Hernandez

See `members/README.md` for the rules and the entry template. Newest entry first.

### 2026-11-15: Sequential baseline performance on the cluster

- **Question:** How long does the sequential baseline take to simulate 1,000,000 Premier League seasons?
- **Setup:** Premier League simulation, snapshot 2026-11-14, 1,000,000 seasons, Slurm job 29781, CPU partition, 2 CPUs allocated, 2 GB memory requested, OMP_NUM_THREADS=1.
- **Command:** `sbatch slurm/characterize.sbatch` (runs `python -m src.baseline --as-of 2026-11-14 --seasons 1000000 --output results/characterize/job-29781`).
- **Result:** The simulation took 61.23 seconds. The total Slurm job duration was 62 seconds, with approximately 99% CPU utilization and 114 MB maximum memory reported by Slurm. The job completed successfully. Logs: `results/characterize/characterize-29781.out` and `results/characterize/sacct-29781.txt`.
- **Conclusion:** The sequential baseline provides an initial performance reference. Additional measurements are needed before evaluating parallel speedup.
