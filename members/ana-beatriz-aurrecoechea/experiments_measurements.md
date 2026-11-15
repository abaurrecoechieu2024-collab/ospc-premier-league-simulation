# Experiments and measurements: Ana Beatriz Aurrecoechea

### 15 nov 2026 #1: Running the same simulation twice

**What I tested:** Would the program give the same results if I ran it twice with the same settings?

**Setup:** My laptop, results through 14 November 2026, 1,000 simulated seasons, batch size 1,000, and seed 2026.

| Step | Command | Result |
|---|---|---|
| First run | `python -m src.baseline --as-of 2026-11-14 --seasons 1000 --batch-size 1000 --seed 2026 --output results/ana-manual-repeat-1` | Completed 1,000 simulations. |
| Second run | `python -m src.baseline --as-of 2026-11-14 --seasons 1000 --batch-size 1000 --seed 2026 --output results/ana-manual-repeat-2` | Completed another 1,000 simulations with the same settings. |
| Compare results | `diff -s results/ana-manual-repeat-1/counts.csv results/ana-manual-repeat-2/counts.csv` | The files were identical. |

**Conclusion:** The program gave exactly the same results both times. This means we can repeat this experiment reliably. It does **not** prove that the football predictions are accurate—only that the same settings produce the same answer.

### 15 nov 2026 #2: Increasing the number of simulations

**Question:** How do more simulations affect the predictions and running time?

**Setup:** My laptop; snapshot 14 November 2026; batch size 1,000; seed 2026; same model and one worker.

| Run | Command |
|---|---|
| 1,000 seasons | `python -m src.baseline --as-of 2026-11-14 --seasons 1000 --batch-size 1000 --seed 2026 --output results/ana-manual-repeat-1` |
| 10,000 seasons | `python -m src.baseline --as-of 2026-11-14 --seasons 10000 --batch-size 1000 --seed 2026 --output results/ana-manual-10000` |
| 100,000 seasons | `python -m src.baseline --as-of 2026-11-14 --seasons 100000 --batch-size 1000 --seed 2026 --output results/ana-manual-100000` |

**Prediction results:** I compared the saved probability files using pandas.

| Team | Title chance: 1,000 seasons | Title chance: 10,000 seasons | Change |
|---|---:|---:|---:|
| Arsenal | 77.70% | 78.47% | +0.77 percentage points |
| Man City | 15.60% | 13.99% | −1.61 percentage points |
| Liverpool | 1.30% | 1.93% | +0.63 percentage points |

Arsenal remained the favourite. The largest change across all teams was 1.61 percentage points.

**Running time and calculated guesses:**

| Simulated seasons | Simulation time | Status |
|---|---:|---|
| 1,000 | 0.05 seconds | Measured |
| 10,000 | 0.45 seconds | Measured |
| 100,000 | 4.53 seconds (estimated 4.50) | Measured |
| 1,000,000 | About 45 seconds | Calculated guess |
| 10,000,000 | About 7.5 minutes | Calculated guess |

**Assumption:** Using the same laptop, model, batch size, and one worker, simulation time will grow roughly in proportion to the number of seasons. These guesses use the measured 10,000-season run as a starting point and exclude loading and fitting.

**Conclusion:** Running **10 times more simulations took about 9 times longer**. From 10,000 to 100,000 seasons, simulation time grew from 0.45 to 4.53 seconds, close to the 4.50-second estimate. Loading the data and estimating team strengths stayed almost unchanged because they happen once per run. Small timing differences can come from rounding and other laptop activity.

More simulations slightly changed the probabilities and can reduce random fluctuation, but they do not prove prediction accuracy. The 1,000,000 and 10,000,000-season workloads have not been tested yet, and these single laptop runs are not cluster performance measurements.
