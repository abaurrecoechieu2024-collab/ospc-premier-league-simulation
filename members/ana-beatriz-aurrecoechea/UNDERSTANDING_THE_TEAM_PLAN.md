# Understanding our Tuesday plan

This explanation is based on the task plan Ana supplied and main revision
`52d4d11da2a3cb8c7ba6c1087341297cb5f65e6e`, inspected on 15 November 2026.
The tasks below are assignments, not claims that they are completed. At this
revision there is no `src/pool.py`, `slurm/strong_pool.sbatch`, or final scaling
notebook on main. Teammates may be working on their own branches or computers.

## David (A): make multiple workers cooperate correctly
The baseline completes every batch one after another. David's process pool gives
batches to several separate Python workers, then adds their position counts.

The key check is: same input + same seed + same batch size must give exactly the
same counts with 1, 2, and 4 workers as the baseline. A faster wrong answer is
not useful. David also measures the cost of starting workers separately. Creating
an executor object may not start its processes immediately; the timing should
measure actual startup, with clear boundaries. His handoff is working code plus
passing equivalence checks on the cluster.

## Anarella (B): find where time goes, and try scheduler jobs
Profiling is a stopwatch for different parts of the program: loading, estimating
strengths, generating goals, updating tables, and sorting tables. This identifies
what can be split across workers and what remains serial.

Her separate job-array experiment gives blocks of batches to separate Slurm jobs,
then merges their counts. Each array task must receive distinct global batch IDs;
restarting every task at batch zero would repeat the same simulations. Compare
the merged result with the baseline. Four array tasks use all four running-job
slots if no other jobs are running, so coordinate submissions.

## Person C: run a fair speed experiment
C uses David's tested pool and runs the same 2,000,000 seasons with 1, 2, 4, 8,
16, and 32 workers. Five repeats at each count give 30 measurements, all within
one cluster job. The data, seed 2026, batch size 1,000, and code revision stay fixed.

64 allocated Slurm CPUs are the resource reservation, not an instruction to run
64 Python workers: the course counts hardware threads as CPUs. Use the selected
worker count for each run. Save raw timings, node, load and Slurm job ID.

The existing baseline cluster run took 61.23 seconds for 1,000,000 seasons, so
122.46 seconds for 2,000,000 is a linear estimate, not a result already measured.
A slower pool run could involve startup, transfers, contention, or other costs;
it needs investigation, not an automatic conclusion that the code is wrong.

## Person D: explain C's measurements
- Runtime: median of five runs, with minimum and maximum.
- Speedup: one-worker time divided by p-worker time, using consistent boundaries.
- Ideal speedup: p workers would give p times the speed if there were no limits.
- Efficiency: speedup divided by p.
- Serial fraction: compare B's profile-based estimate with an estimate from scaling.

For speedup S with p > 1 workers, the Amdahl-based effective serial estimate is
`f = (1/S - 1/p) / (1 - 1/p)`. State the definition of the one-worker reference
(pool with one worker or sequential baseline) and whether startup/I/O is included.
Overhead and contention can make this an effective limit rather than literal
serial code time. Do not force it to equal the earlier 0.8% estimate: that was
from a different run size and timing boundary. The serial fraction can change
when the number of simulated seasons changes.

D combines the plot with a short note: question, snapshot, design, correctness,
measurements, interpretation, limitations and questions. Tuesday's progress update
is sent through the group's Blackboard conversation, following the professor's
11 November verbal update.

## Ana's contribution: check and understand the shared baseline
The added experiment runner leaves all simulation/model functions unchanged.
It reuses the baseline and records:
1. Exact reproducibility for two identical 1,000-season runs.
2. Position-count and probability accounting on real data.
3. How probabilities change at 1,000, 10,000 and 50,000 seasons.
4. Whether future scores leak into a forecast made at an earlier cutoff.

These complement A-D; they are not the parallel equivalence checks or the cluster
scaling experiment. They were run with Codex assistance. Ana should rerun/read them
and add her own explanation or questions before claiming independent understanding.

## Try it yourself
From this branch's repository root, using the course Python environment:

```bash
python -m pytest -q
python -m src.baseline --as-of 2026-11-14 --seasons 1000 --batch-size 1000 --seed 2026 --output results/ana-my-first-run
```

Open `probabilities.csv`: 0.20 means 20%. Open `counts.csv`: each row is a team,
and columns 1-20 count its finishing positions. Each row and each column should
sum to 1,000.

For the complete recorded experiment, choose a new folder:

```bash
python -m src.ana_experiments --output results/ana-my-rerun --source-revision 52d4d11da2a3cb8c7ba6c1087341297cb5f65e6e
```

That revision identifies the underlying baseline being tested; update it if the
baseline has changed. The new experiment script itself is recorded in this PR.
You need NumPy, pandas and pytest; the recorded local versions are in the results
metadata. On the cluster the team guide uses `/data/software/envs/ospc/bin`.
Keep local timings labelled local; course report measurements use batch jobs.

Questions to answer in your own words:
- Why do identical random seeds produce identical counts but not identical timings?
- Why do title probabilities across all teams sum to 1, but top-four probabilities sum to 4?
- Why do more simulations reduce sampling noise without fixing a poor football model?
- Why is the two-minute Tuesday workload separate from the final ten-minute baseline requirement?
