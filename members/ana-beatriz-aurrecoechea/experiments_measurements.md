# Experiments and measurements: Ana Beatriz Aurrecoechea

See `members/README.md` for the rules. Newest entry first.

The experiments below were executed locally with **Codex assistance** on 15 November
2026. They do not establish that Ana has independently rerun or reviewed them yet.
No cluster jobs were submitted for these entries. Base code revision:
`52d4d11da2a3cb8c7ba6c1087341297cb5f65e6e`. Shared rules: seed 2026,
batch size 1,000, Championship option off, default decay 0.5.
Full setup and versions: [environment.json](../../results/ana-2026-11-15/environment.json).
Commands below assume the course Python or an environment with the same dependencies.
Use fresh output folders on reruns. The recorded local interpreter was `.venv/bin/python`.

### 2026-11-15: Does the forecast accidentally use future results?
- **Question:** would results after a cutoff affect a forecast at that cutoff?
- **Setup:** unchanged repository data; earlier cutoff 2026-10-01; local, one worker.
- **Command:** `python -m src.ana_experiments --output results/ana-2026-11-15 --source-revision 52d4d11da2a3cb8c7ba6c1087341297cb5f65e6e` (runs all four experiments).
- **Result:** replaced the home/away scores in 50 later rows with 99 in memory only.
  Teams, starting table, remaining fixtures, and expected goal rates stayed identical.
  Original files were unchanged. [Checks](../../results/ana-2026-11-15/checks.csv).
- **Conclusion:** this controlled check found no future-score leakage at this cutoff.
  It is not proof that every possible data-leakage path has been excluded.

### 2026-11-15: How much do probabilities change with more simulations?
- **Question:** do estimates move less as we simulate more seasons?
- **Setup:** local; snapshot 2026-11-14, 20 teams, 280 remaining matches;
  1,000 / 10,000 / 50,000 seasons; same fixed seed and batch size.
- **Command:** `python -m src.ana_experiments --output results/ana-2026-11-15 --source-revision 52d4d11da2a3cb8c7ba6c1087341297cb5f65e6e`.
- **Result:** largest absolute change across teams, in percentage points:

  | Outcome | 1,000 to 10,000 | 10,000 to 50,000 |
  |---|---:|---:|
  | Title | 1.610 | 0.732 |
  | Top four | 1.480 | 0.532 |
  | Top six | 2.540 | 0.774 |
  | Relegation | 1.290 | 0.910 |

  [Comparisons and affected teams](../../results/ana-2026-11-15/probability_changes.csv).
- **Conclusion:** changes were smaller in the second comparison for all four outcomes.
  The samples overlap because seed/batches are shared, so this is descriptive, not an
  independent-sample statistical test. More simulations reduce sampling noise; they
  do not prove forecast accuracy or remove model bias.

### 2026-11-15: Are the position counts and probabilities internally consistent?
- **Question:** is each team/position counted exactly once per simulated season?
- **Setup:** all four local runs; same inputs as above.
- **Command:** `python -m src.ana_experiments --output results/ana-2026-11-15 --source-revision 52d4d11da2a3cb8c7ba6c1087341297cb5f65e6e`.
- **Result:** every counts table is 20 × 20 with nonnegative integer values; each row
  and column sums to its simulation count. Probabilities lie in [0,1]. Totals across
  teams are 1 title, 4 top-four places, 6 top-six places, and 3 relegation places.
  For each team, title <= top4 <= top6. [Checks](../../results/ana-2026-11-15/checks.csv).
- **Conclusion:** accounting is consistent on these real-data runs; this complements
  rather than replaces hand-checked ranking tests and future pool equivalence tests.

### 2026-11-15: Do identical inputs and randomness reproduce identical counts?
- **Question:** will repeating a 1,000-season run change its results?
- **Setup:** local one-worker baseline; same data, snapshot 2026-11-14, seed 2026,
  batch size 1,000, default model; separate output folders.
- **Commands:**
  - `python -m src.baseline --data-dir data/raw --as-of 2026-11-14 --seasons 1000 --batch-size 1000 --seed 2026 --output results/ana-2026-11-15/n1000-a`
  - `python -m src.baseline --data-dir data/raw --as-of 2026-11-14 --seasons 1000 --batch-size 1000 --seed 2026 --output results/ana-2026-11-15/n1000-b`
- **Result:** all 400 position counts matched exactly. [Run A](../../results/ana-2026-11-15/n1000-a/counts.csv),
  [run B](../../results/ana-2026-11-15/n1000-b/counts.csv).
- **Conclusion:** repeatable random inputs reproduce the baseline counts in this environment.
  Runtime can still vary. Raw [local timings](../../results/ana-2026-11-15/local_timings.csv)
  are quick-check evidence only, not the team's cluster scaling results.

### 2026-11-15: Existing regression suite
- **Question:** does the current shared code pass the existing checks locally?
- **Setup:** same base revision, Python/NumPy/pandas/pytest versions in environment.json.
- **Command:** `python -m pytest -q`.
- **Result:** 26 tests passed. The experiment runner additionally passed 30 checks.
- **Conclusion:** suitable for these local exploration runs. David still needs to run
  the pool equivalence tests and the required suite on the cluster.
