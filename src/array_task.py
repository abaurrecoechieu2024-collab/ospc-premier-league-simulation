"""One Slurm array task: simulate its own block of batches and save the counts.

Every task uses the same batches and random streams as the baseline
(batch_seeds), so the merged counts must equal the baseline's exactly.

On the cluster (Slurm sets the task number and the number of tasks):
    sbatch slurm/array_test.sbatch
On a laptop, pass them by hand:
    python -m src.array_task --as-of 2026-11-14 --seasons 20000 --task-id 0 --n-tasks 4 --output tmp/array
"""
import argparse
import os
import socket
from datetime import datetime
from pathlib import Path
from time import perf_counter

import pandas as pd

from .baseline import add_counts, prepare
from .simulate import batch_seeds, simulate_batch


def my_batches(batches, task_id, n_tasks):
    """The contiguous block of batches that belongs to this task."""
    start = task_id * len(batches) // n_tasks
    end = (task_id + 1) * len(batches) // n_tasks
    return batches[start:end]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--seasons", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output", type=Path, required=True, help="folder shared by all tasks")
    parser.add_argument("--task-id", type=int, default=None, help="default: $SLURM_ARRAY_TASK_ID")
    parser.add_argument("--n-tasks", type=int, default=None, help="default: $SLURM_ARRAY_TASK_COUNT")
    args = parser.parse_args(argv)
    task_id = args.task_id if args.task_id is not None else int(os.environ["SLURM_ARRAY_TASK_ID"])
    n_tasks = args.n_tasks if args.n_tasks is not None else int(os.environ["SLURM_ARRAY_TASK_COUNT"])

    inputs, model, loading, fitting = prepare("data/raw", pd.Timestamp(args.as_of))
    batches = my_batches(batch_seeds(args.seasons, args.batch_size, args.seed), task_id, n_tasks)

    n_teams = len(inputs["teams"])
    counts = [[0] * n_teams for _ in range(n_teams)]
    start = perf_counter()
    for n, seed_seq in batches:
        add_counts(counts, simulate_batch(seed_seq, n, inputs))
    simulation = perf_counter() - start

    args.output.mkdir(parents=True, exist_ok=True)
    teams = inputs["teams"]
    pd.DataFrame(counts, index=teams, columns=range(1, n_teams + 1)).to_csv(
        args.output / f"counts_task{task_id}.csv")
    pd.DataFrame([{"task_id": task_id, "n_tasks": n_tasks, "batches": len(batches),
                   "seasons": sum(n for n, _ in batches), "loading_seconds": loading,
                   "fitting_seconds": fitting, "simulation_seconds": simulation,
                   "node": socket.gethostname(), "node_load": os.getloadavg()[0],
                   "slurm_job_id": os.environ.get("SLURM_JOB_ID", "local"),
                   "array_job_id": os.environ.get("SLURM_ARRAY_JOB_ID", "local"),
                   "date": datetime.now().isoformat(timespec="seconds")}]).to_csv(
        args.output / f"timing_task{task_id}.csv", index=False)
    print(f"task {task_id}/{n_tasks}: {len(batches)} batches in {simulation:.2f} s -> {args.output}")


if __name__ == "__main__":
    main()
