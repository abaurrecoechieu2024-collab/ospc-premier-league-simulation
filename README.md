# Premier League Season Simulation
## Group 6 — Operating Systems and Parallel Computing

**Status:** Sequential baseline, final model (backtested), process pool and job arrays are done; all versions give identical counts (36 tests). Cluster results: baseline is CPU-bound (job 29781); the process pool reaches a 24.4× speedup on 32 workers (job 30371, plot in `results/plots/strong_scaling.png`). Next: vectorized version, full-size job arrays, weak scaling.

**Start here:** [Run and understand the baseline](docs/BASELINE_GUIDE.md).

## Our question
What is each Premier League team's probability of winning the league, qualifying for European competitions, or being relegated?

We will use real match results to estimate team strengths, simulate many possible season outcomes, and compare ways to compute the same answers faster. The number of simulated seasons is the adjustable workload size.

## Data
Source: [Football-Data.co.uk — England](https://www.football-data.co.uk/englandm.php), using the Premier League CSV links.

The exact historical seasons and download cutoff still need group agreement. If we adopt the teacher's suggestion to simulate only remaining matches, we also need current-season results and a complete list of remaining fixtures. Do not assume the results CSV contains all future fixtures.

Record chosen files and their provenance in [data/README.md](data/README.md). Keep a fixed dated input snapshot for comparisons.

## Planned implementations
1. **Sequential baseline:** simulate seasons one after another; verify correctness before optimizing.
2. **Process pool:** distribute fixed batches of seasons across workers and combine their counts.
3. **NumPy vectorization:** calculate match outcomes in batches, controlling memory use. Vectorization does not automatically imply multicore execution.
4. **Slurm job arrays:** the additional technique assigned by the instructor, replacing the proposal's Numba plan. Each task handles a block of seasons.

## Decisions (agreed)
- [x] Training: Premier League 2023/24–2025/26 + played 2026/27 games; a season k years back counts 0.5^k. Chosen with a weekly backtest on 2024/25 and 2025/26 (see docs/VALIDATION.md). The Championship conversion for promoted teams was tested and is off by default (`--championship`).
- [x] Simulate only the remaining 2026/27 matches from a frozen snapshot (14 November 2026: 100 played, 280 left).
- [x] Goals: Poisson with expected goals = league average × attack × opponent defence.
- [x] Ranking: points → goal difference → goals scored → seeded random draw (documented simplification).
- [x] Outcomes: title, top 4, top 6, relegation (bottom 3), all from 20 × 20 position counts.
- [x] Fixed batches (default 1,000 seasons), one `SeedSequence.spawn` stream each; every batch draws all its goals first, then its tie-break numbers. All versions must give exactly the same counts.
- [x] Additional technique: Slurm job arrays.
- [ ] Task owners and internal deadlines (see the team plan).

New ideas that were not covered in class are explained in [docs/BEYOND_THE_COURSE.md](docs/BEYOND_THE_COURSE.md).

For reproducibility, the teacher recommends independent random streams per fixed batch using `SeedSequence.spawn`. Assign streams to batch IDs rather than worker identities so worker count and completion order do not change inputs. For NumPy, agree early whether to reuse identical generated goals or compare probabilities statistically with a justified tolerance.

## Tuesday 17 November 2026: progress review
The formal requirement is a brief in-class progress presentation, **including a first scaling plot**, and discussion of current problems. It is not graded.

Suggested preparation:
- [ ] Agree the decisions above and task owners.
- [ ] Build a small, correct sequential baseline.
- [ ] Add repeatable correctness checks, including a hand-verifiable example.
- [ ] Profile the baseline to see where time goes; time strength estimation separately.
- [ ] Implement an initial process-pool version.
- [ ] Measure a fixed workload with 1, 2, and 4 workers, plus the sequential baseline.
- [ ] Run measurements as cluster batch jobs, with at least five repetitions per configuration.
- [ ] Save raw timings and plot median running time against worker count, with spread.
- [ ] Prepare an explanation of progress, limitations, problems, and next steps.

## Repository layout
| Folder | Intended contents |
|---|---|
| `src/` | Shared Python modules and simulation implementations |
| `tests/` | Automated correctness and equivalence checks |
| `data/` | Dataset documentation and agreed small input snapshots |
| `slurm/` | Cluster batch scripts for every experiment |
| `results/` | Raw timing CSVs and generated plots |
| `notebooks/` | Analysis and plotting from recorded results |
| `docs/` | Decisions, task allocation, and AI-use record |

## Running the project
The baseline has been tested locally and on the cluster (see `results/characterize/`).

The final README must document installation, data preparation, correctness checks, command-line runs with workload/worker parameters, cluster submission, and plot generation. Include a small configuration that completes in under five minutes and verify the full pipeline from a fresh clone on the cluster.

## Measurement rules from the course
- Full-size sequential workload: at least 10 minutes on one core (or the alternative larger-than-job-memory condition).
- Obtain report measurements on the cluster via `sbatch`, not notebook sessions.
- Repeat each configuration at least five times; report median and spread.
- Time computation separately from input/output; time strength estimation separately.
- Record version, workers, workload size, repetition, elapsed time, node, Slurm job ID, date, and node load.
- Eventually measure strong scaling, weak scaling, at least one overhead, and analyze the serial fraction.
- Limits: up to 64 Slurm CPUs (32 physical cores), 4 running jobs and 8 submitted jobs. Each array task counts toward job limits. The teacher suggested small arrays such as `--array=0-7%4`; coordinate other submissions too.

## Deadlines
| Deliverable | Due |
|---|---|
| Progress review with first scaling plot | 17 November 2026, in class |
| Experiments completed and slides uploaded | 30 November 2026, 23:59 |
| Group presentations | 2 or 15 December 2026 |
| Repository and report | 15 December 2026, 23:59 |

## Collaboration
Use one shared repository. Each member should make regular commits through their own account. Agree task owners in [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md), use branches for changes, and review each other's work. Share repository access with the instructor before submission. Use the team's private Blackboard conversation for instructor follow-ups.

Team: Ana Beatriz Aurrecoechea, Isabella Lizarraga, Armando Hernandez, Theodor-Gabriel David, David Hyeon, and Anarella Furoiani.

## AI assistance
Initial repository documentation and structure were prepared with OpenAI Codex on 12 November 2026 from the supplied project brief, proposal, teacher feedback, and conversation. See [docs/AI_USE.md](docs/AI_USE.md). The team must review the content and complete the acknowledgment in the syllabus-required format.
