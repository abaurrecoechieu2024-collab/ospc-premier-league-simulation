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

## Model choice: weekly backtest (results/backtest-weekly-all.csv)

Replayed 2025/26 and 2024/25 after every 10 matches (37 points per season), 5,000
simulated seasons per forecast, scored against the real final tables.

Average over both seasons and all 37 points (lower is better, except the last column):

| Model | Weight | Position error | Relegation Brier | P(real champion) |
|---|---|---|---|---|
| simple (1 past season) | equal | 1.949 | 0.028 | 0.671 |
| multi (3 past seasons) | **0.5 (final)** | 1.936 | 0.027 | 0.701 |
| multi | 0.75 | 1.929 | 0.026 | 0.693 |
| multi | 1.0 | 1.929 | 0.026 | 0.687 |
| full (+ Championship) | 0.5 | 2.012 | 0.024 | 0.696 |
| full | 1.0 | 2.039 | 0.027 | 0.682 |
| multi (earlier run) | 0.25 | 1.977 | 0.030 | 0.710 |
| multi (earlier run) | 0.1 | 2.039 | 0.032 | 0.713 |

Position error at selected points in the season:

| Matches played | full 0.5 | multi 0.5 | multi 1.0 | simple |
|---|---|---|---|---|
| 10 | **3.14** | 3.49 | 3.51 | 3.57 |
| 30 | 3.18 | 3.14 | **3.06** | 3.31 |
| 100 (our snapshot) | 2.46 | **2.40** | 2.42 | 2.41 |
| 150 | 2.36 | 2.24 | 2.23 | **2.23** |
| 250 | 1.69 | 1.61 | 1.57 | **1.56** |

Conclusions:
- More history (3 seasons instead of 1) helps early in the season and makes little
  difference later.
- Weights from 0.5 to 1.0 tie; 0.25 and 0.1 are worse. Final choice: 0.5.
- The Championship conversion helps only in the first ~40 matches and hurts afterwards,
  so it is off by default (`--championship` turns it on).
- Testing a single point (100 matches) first suggested weight 0.25; the weekly test
  overturned it. Test across the whole season, not one snapshot.
- A wrong input file (2025/26 data saved as E0_2425.csv) was found by the backtest;
  `load_matches()` now rejects files whose dates do not match their season.
