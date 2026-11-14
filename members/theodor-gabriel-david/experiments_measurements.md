# Experiments and measurements: Theodor-Gabriel David

See `members/README.md` for the rules and the entry template. Newest entry first.
All runs on 14 November 2026 in the course container (laptop), not cluster timings.

### 2026-11-14: Final forecast with the chosen model (multi, weight 0.5)
- **Setup:** snapshot 14 Nov 2026 (100 played, 280 left), 10,000 seasons.
- **Command:** `python -m src.baseline --as-of 2026-11-14 --seasons 10000 --output results/final-check`
- **Result (relegation):** Crystal Palace 57%, Coventry 59%, Ipswich 56%, Sunderland 44%,
  Nott'm Forest 20%, Man United 13%, Hull 8%. Title: Arsenal 78%, Man City 14%.
  Relegation probabilities sum to exactly 3.00, title to 1.00.
- **Conclusion:** sensible for the current table. Known quirk: Ipswich (one bad PL season
  in its history) is judged harder than Hull (no PL history, starts at average).

### 2026-11-14: Model choice with a weekly backtest
- **Question:** which model and season weight forecast best, at every point of a season?
- **Setup:** replay 2025/26 and 2024/25 after 10, 20, ..., 370 matches; 5,000 seasons each.
- **Command:** `python -m src.backtest --test-seasons 2025 2024 --models simple multi full --decays 0.5 0.75 1.0 --every-matchweek --seasons 5000 --output results/backtest-weekly-all.csv`
- **Result (averages):**

  | Model | Weight | Position error | Relegation Brier |
  |---|---|---|---|
  | simple (1 past season) | equal | 1.949 | 0.028 |
  | multi (3 past seasons) | 0.5 | 1.936 | 0.027 |
  | multi | 1.0 | 1.929 | 0.026 |
  | full (+ Championship) | 0.5 | 2.012 | 0.024 |
  | multi (earlier run) | 0.25 / 0.1 | 1.977 / 2.039 | 0.030 / 0.032 |

- **Conclusion:** weights 0.5–1.0 tie, lower weights are worse; the Championship
  conversion helps only in the first ~40 matches and hurts later. Final model: multi,
  weight 0.5, Championship off by default. Details: `docs/VALIDATION.md`.
- **Lesson:** a single snapshot (100 matches) first suggested weight 0.25; testing every
  matchweek overturned it.

### 2026-11-14: Wrong input file found by the backtest
- **Problem:** the 2024/25 backtest snapshot was dated November 2025. `E0_2425.csv`
  actually contained 2025/26 matches (every download is called `E0.csv`).
- **Fix:** re-downloaded the file; `load_matches()` now rejects a file whose dates do not
  match the season in its name. Earlier results with the wrong file were discarded.

### 2026-11-14: Promoted teams and season weights (first attempt)
- **Question:** why did Hull (13th, 11 points) get 93% relegation?
- **Result:** the Championship → PL conversion measured on 3 teams gave a defence factor
  of 2.41 (driven by Burnley's record Championship defence); pooling 6 teams gave lower
  but still pessimistic factors. Championship history outweighed this season's games.
- **Conclusion:** led to the backtests above; the conversion was finally switched off.

### 2026-11-14: Restructured baseline and new data
- **Changes:** shared modules (`data`, `fixtures`, `strengths`, `simulate`, `table`), one
  goals array per batch + seeded random tie-break (exact equality across versions),
  20 × 20 position counts, pytest tests, Slurm script with the course Python.
- **Data added:** Premier League 2023/24, 2024/25; Championship 2022/23–2025/26
  (hashes in `data/snapshot_manifest.json`).
- **Speed (container, indicative only):** 10,000 seasons ≈ 0.6 s simulation,
  ≈ 0.47 s loading, ≈ 0.01 s fitting. Cluster timing still to do.
