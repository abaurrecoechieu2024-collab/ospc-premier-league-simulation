# Sequential baseline: start here

This is a working first version, with provisional modelling choices for group review.
It uses one worker and Python loops over seasons and matches. NumPy supplies random
numbers; there is no vectorized or parallel simulation yet.

## What happens in a run?
1. Read the saved results files.
2. Rebuild the target season's table from games completed by the chosen date.
3. Estimate each team's scoring/conceding strength once.
4. Generate the remaining matchups by taking every home/away pair and removing
   completed games. Dates are not needed because strengths stay fixed in this model.
5. Simulate those games one at a time, add points and goals, and sort the final table.
6. Repeat, then divide title/top-k/relegation counts by the number of simulations.

## Run it on your computer
Use Python 3.11 or newer. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m src.baseline --history data/raw/E0_2526.csv --current data/raw/E0_2627.csv --as-of 2026-11-14 --seasons 1000 --output results/my-first-run
```

On Windows activate with `.venv\Scripts\activate` instead. The simulation and tests
are intended for macOS/Linux (node-load recording uses `os.getloadavg`); use the
course Linux environment on Windows.

Choose a **new output folder** for every run. Existing results are never overwritten.
The small configuration above is intended to finish in under five minutes; it was
checked locally, but the required fresh-clone cluster check remains to be done.

## Open your results
- `probabilities.csv`: team counts and probabilities between 0 and 1 (multiply by 100 for percentages).
- `current_table.csv`: the starting points and goals, reconstructed from completed games.
- `metadata.json`: assumptions, input file hashes, versions, and separate timings.
- `timing.csv`: one row for this run, suitable for later plotting.

`elapsed_seconds` measures simulation including random-stream setup, table updates,
ranking, and aggregation. `fitting_seconds` measures one-off strength estimation.
`compute_seconds` is their sum. `loading_seconds` includes input parsing, validation,
initial-table/fixture preparation, and hashing. `result_writing_seconds` times the
two results CSVs, excluding metadata/timing-file writes. Use the same boundaries
for future parallel versions. Local smoke timings are not course cluster evidence.

## Provisional choices to discuss with your group
- **Inputs:** previous season 2025/26 plus played 2026/27 matches through 14 November 2026.
  The downloaded current file contains 100 completed matches, last dated 8 November.
  Inputs are frozen, not automatically refreshed. The 20 current teams determine the roster.
- **Training:** all previous-season games plus current games on/before cutoff, equally weighted.
  History must precede the target season, so the current results cannot accidentally be counted twice.
- **Goals:** independent Poisson draws for home and away goals. This is a simple count model,
  not a sophisticated prediction system. It ignores injuries, lineups, changing form, and score dependence.
- **Home advantage:** separate league home/away averages and home/away team strengths.
- **Sparse history:** smooth each team's average using five imaginary games at league-average
  scoring/conceding rates. A promoted team with no older records starts near average and uses
  its played current-season games. This is a modelling assumption, not evidence it is average.
- **Standings:** points, goal difference, goals scored, then alphabetical order for an exact tie.
  The alphabetical fallback is deliberately simplified, not the complete official PL procedure.
  This can affect very close outcomes. No disciplinary points deductions are included.
- **Outcomes:** league winner, top four (configurable `--top-k`), bottom three
  (configurable `--relegated`). Top four is a positional proxy; it is not a claim about
  all official European qualification routes.
- **Fixtures:** assume a complete double round robin (each pair plays twice, swapping home/away).
  Missing completed rows would be mistaken for remaining games. Check snapshot completeness
  against your chosen source before treating forecasts as current.

## How expected goals are calculated
For a home team's attack strength:

`smoothed home goals per game / league home goals per game`

For an away team's defence weakness:

`smoothed away goals conceded per game / league home goals per game`

Expected home goals = league home average × home attack × away defence weakness.
Expected away goals use the equivalent away attack and home defence values.
A higher defence weakness means more goals conceded. The smoothing weight is
configurable with `--prior-games` and must be positive.

## Randomness: the rule future versions must preserve
Seasons are grouped into fixed logical batches (default 100). Each batch gets a
child stream from `SeedSequence.spawn`, using PCG64. Batches run sequentially here.
The process pool can later execute the **same batch function** on separate workers.
Keep seed, batch size, ordered teams/fixtures, input snapshot, and NumPy version fixed.
Changing worker count or completion order should then preserve integer counts exactly.
Changing batch size changes the random experiment. A future NumPy version needs its
own agreed shared-goals or statistical comparison strategy.

## Profile and run on the cluster
Set up the environment and run the tests on the cluster first. Submit from the repo root:

```bash
sbatch slurm/baseline.sbatch
```

The starter job requests one CPU and runs five repetitions. Adjust account/partition
settings if the course requires them. The script has not been executed on the cluster.
It expects `.venv/bin/python`; set `PYTHON_BIN` if your environment lives elsewhere.

For a local diagnostic profile (not report timing):

```bash
python -m cProfile -s cumulative -m src.baseline --history data/raw/E0_2526.csv --current data/raw/E0_2627.csv --as-of 2026-11-14 --seasons 10000 --output results/profile-run
```

Run a pilot on the cluster, then increase `SEASONS` to reach at least ten minutes
on one core for the full-size workload. Example: if a cluster pilot takes 30 seconds
for 100,000 seasons, about 2,000,000 seasons is a starting estimate; measure again.
Do not insert artificial delays. Allow enough batch-job wall time for five repeats.
Use `/usr/bin/time -v` or `sacct` on the cluster to characterize CPU/memory use.

## Next development step
Review the assumptions, then add a process-pool runner around `simulate_batch` and
an automated exact-count comparison with this baseline. Measure fixed-size runs at
1, 2, and 4 workers to make Tuesday's first scaling plot. This sequential baseline
alone does not provide a parallel scaling plot.

References: [data columns](https://www.football-data.co.uk/notes.txt),
[NumPy random streams](https://numpy.org/doc/stable/reference/random/parallel.html).
