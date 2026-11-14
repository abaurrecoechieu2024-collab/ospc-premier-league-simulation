# What in our code goes beyond the course

Most of the code uses only what we saw in class: pandas to read CSVs, NumPy random
numbers, `SeedSequence.spawn`, Python loops, `int8` to save memory, pytest, and Slurm
batch jobs with `OMP_NUM_THREADS=1`. These few extra ideas are also in it. Read this
so anyone can explain them if Matteo asks.

## 1. `argparse`: running from the command line
**What:** reads options like `--seasons 10000` when we run `python -m src.baseline ...`.
**Why:** the handout asks that every version runs from the command line with the
problem size and the number of workers as parameters.
**Where:** `parse_args()` in `src/baseline.py`.

## 2. The goals model (Poisson)
**What:** the number of goals a team scores in a match is drawn from a Poisson
distribution: `rng.poisson(expected_goals)`. It is the standard simple model for
counts ("how many times something happens in 90 minutes").
**Expected goals** = league average × attack of the scorer × defence of the opponent.
Example: league home average 1.5, home attack 1.2, away defence 1.1 → 1.5 × 1.2 × 1.1 ≈ 2.0 goals.
**Where:** `src/strengths.py`, `expected_goals()` in `src/simulate.py`.

## 3. Smoothing: "imaginary average games"
**What:** each team gets 5 extra imaginary games at the league average before we
divide. Formula: `(goals + 5 × league average) / (games + 5) / league average`.
**Why:** after a few games a team can look extreme by chance (3 goals in 1 game ≠ 3
per game forever). The fewer real games, the more the team is pulled toward 1.0 (average).
**Where:** `smoothed()` in `src/strengths.py` (`prior_games=5`).

## 4. Season weights: recent seasons count more
**What:** a match from k seasons ago counts `0.5 ** k`: this season 1, last season
0.5, two seasons ago 0.25, three seasons ago 0.125.
**Why:** squads change every summer, so old results tell us somewhat less. In the
backtest every weight from 0.5 to 1.0 (all seasons equal) did equally well, and 0.25
or 0.1 did worse, especially early in the season. We chose 0.5 because it matches how
squads change and keeps old seasons from dominating if more history is added.
**Where:** `decay` in `fit_strengths()`; try other values with `--decay`.

## 5. Promoted teams: Championship conversion (tested, off by default)
**What:** an optional way to use Coventry's and Hull's Championship games. Their goals
are converted to "Premier League goals" with two factors measured on the 6 teams
promoted in the two previous seasons: attack factor = (PL goals scored per game the
year after promotion) ÷ (Championship goals scored per game the year before);
defence factor = the same with goals conceded.
**Why it is off:** the weekly backtest showed it helps only in the first ~40 matches of
a season (when promoted teams have almost no Premier League games) and makes
forecasts worse afterwards: the factors are dominated by teams that went straight back
down, so every promoted team looks too weak. Without it, a promoted team starts at the
league average (smoothing, section 3) and its real results take over within weeks.
**Where:** `promotion_factors()` in `src/strengths.py`; turn it on with `--championship`.

## 6. Random tie-break
**What:** after points, goal difference and goals scored, an exact tie is decided by
a random number per team, drawn from the batch's own stream right after the goals.
**Why:** fair (alphabetical order would always favour the same teams) and still
reproducible, so all versions give exactly the same counts.
**Where:** `rank_teams()` in `src/table.py`, `generate_batch()` in `src/simulate.py`.

## 7. `os.getloadavg()`: node load
**What:** the 1-minute load average of the node, the same number htop shows at the top.
**Why:** the handout asks us to record the load, because other jobs can share our cores.
**Where:** `main()` in `src/baseline.py`, column `node_load` in `timing.csv`.

## 8. `pytest.ini`
**What:** two lines that tell pytest where our code and tests are, so `pytest` works
from the repository root without extra settings.

## 9. Backtest: checking the model on finished seasons
**What:** `python -m src.backtest` replays 2025/26 and 2024/25: it stops after 10, 20, ...,
370 matches (`--every-matchweek`), uses only the data available then, simulates the
rest and compares with the real final table. It compares three models: `simple` (last
season + this season, equal weights: our first version), `multi` (3 past seasons,
weighted: our final model) and `full` (multi + Championship conversion).
**Scores (lower is better):** `position_error` = average number of places between a
team's simulated average position and its real one. `brier_*` = average of
(predicted probability − what happened)², where what happened is 1 or 0; e.g. 90%
relegation for a team that went down costs (0.9 − 1)² = 0.01, for a team that stayed
up (0.9 − 0)² = 0.81. `p_real_champion` = the chance we gave the real champion.
**Results:** see `docs/VALIDATION.md`.
**Limitation:** two seasons only; treat differences of a few hundredths as ties.
