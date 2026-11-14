# Local validation — 14 November 2026

- 12 automated tests passed: points, tie-breaking, known deterministic outcomes,
  repeatability, conservation of outcome counts, batch completion order,
  spawned random streams, cutoff filtering, sparse history, invalid parameters,
  zero relegation places, and malformed CSV handling.
- Real-data smoke run completed for 1,000 simulated seasons.
- Starting standings matched an independent calculation from raw CSV rows.
- Current input: 20 teams, each with 10 played games; 100 completed matches,
  leaving 280 directed home/away pairings out of 380.
- Outcome totals were 1,000 titles, 4,000 top-four finishes, and 3,000 relegations.
  Every probability was in [0, 1].
- Local diagnostic profile completed for 10,000 simulated seasons. Most time
  was in the simulation loop; table updates and ranking were also visible.
- The starter Slurm script passed shell syntax checking only.

These are local correctness/smoke checks, not cluster performance results.
The full-size 10-minute baseline, repeated cluster measurements, CPU/memory
characterization, fresh-clone cluster run, and parallel equivalence/scaling
checks remain pending. Re-run the documented commands on the cluster.
