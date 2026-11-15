# Experiments and measurements: Isabella Lizarraga

See `members/README.md` for the rules and the entry template. Newest entry first.

### 2026-11-15: Prepared strong-scaling job (not yet run on cluster)
- **Question:** How does fixed-workload process-pool runtime change with 1, 2, 4, 8, 16 and 32 workers?
- **Setup:** Premier League snapshot 2026-11-14; planned 2,000,000 seasons; batch size 1,000; seed 2026; 64 Slurm CPUs; 8G memory; OMP_NUM_THREADS=1; five repetitions per worker count in one job.
- **Command (pending cluster submission):** `sbatch slurm/strong_pool.sbatch` from the repository root, on a checked-out revision containing `slurm/strong_pool.sbatch`.
- **Result:** Created `slurm/strong_pool.sbatch` in the `person-c-strong-scaling` branch. A local mock-data execution checked output CSV generation for several worker configurations; **no actual university-cluster timings or Slurm job ID have been collected yet**. The script first calls `python -m pytest -q` and saves each completed run's timing CSV plus summary rows in `results/strong_pool/job-<JOB_ID>/scaling.csv`.
- **Conclusion / next action:** After Person A confirms pool/baseline count equivalence, check out the updated branch on the cluster, confirm the one-worker runtime is around 1–2 minutes (adjust `SEASONS` if needed), submit the full Slurm job, verify 30 timing rows, add measured job ID/node and numerical results here, and share the CSV with Person D.
- **Assistance:** ChatGPT helped prepare and inspect the Slurm script and mock-test CSV collection; real experiments and verification remain to be done by the team.
