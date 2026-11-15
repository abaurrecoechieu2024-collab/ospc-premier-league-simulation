"""Process-pool simulation: run each deterministic batch in a worker process.

Example:
    python -m src.pool --as-of 2026-11-14 --seasons 1000 --workers 4 \\
        --output results/test-pool-run
"""
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from queue import Empty
from time import perf_counter

import pandas as pd

from .baseline import add_counts, parse_args, prepare, write_results
from .simulate import batch_seeds, simulate_batch


_pool_start_event = None


def _initialize_pool_worker(ready_queue, start_event):
    global _pool_start_event
    _pool_start_event = start_event
    ready_queue.put(os.getpid())


def _pool_warmup():
    _pool_start_event.wait()


def run_pool(n_seasons, batch_size, seed, inputs, workers):
    """Return counts and separate pool-startup and batch-simulation timings."""
    if workers < 1:
        raise ValueError("workers must be a positive integer")

    n_teams = len(inputs["teams"])
    total = [[0] * n_teams for _ in range(n_teams)]
    batches = batch_seeds(n_seasons, batch_size, seed)
    context = get_context()
    ready_queue = context.Queue()
    start_event = context.Event()

    try:
        start = perf_counter()
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=context,
            initializer=_initialize_pool_worker,
            initargs=(ready_queue, start_event),
        ) as executor:
            warmup_futures = [executor.submit(_pool_warmup) for _ in range(workers)]
            try:
                for _ in range(workers):
                    ready_queue.get(timeout=60)
            except Empty as error:
                start_event.set()
                raise RuntimeError("Timed out while starting process pool workers") from error
            start_event.set()
            for future in warmup_futures:
                future.result()
            pool_startup_seconds = perf_counter() - start

            start = perf_counter()
            futures = [
                executor.submit(simulate_batch, seed_seq, n, inputs)
                for n, seed_seq in batches
            ]
            for future in as_completed(futures):
                add_counts(total, future.result())
            simulation_seconds = perf_counter() - start
    finally:
        ready_queue.close()
        ready_queue.join_thread()

    return total, pool_startup_seconds, simulation_seconds


def main(argv=None):
    args = parse_args(argv, workers=True, description=__doc__)
    if args.workers < 1:
        raise ValueError("--workers must be a positive integer")

    inputs, model, loading, fitting = prepare(
        args.data_dir,
        pd.Timestamp(args.as_of),
        args.decay,
        championship=args.championship,
    )
    node_load = os.getloadavg()[0]
    counts, pool_startup, simulation = run_pool(
        args.seasons, args.batch_size, args.seed, inputs, args.workers
    )

    timings = {
        "loading_seconds": loading,
        "fitting_seconds": fitting,
        "pool_startup_seconds": pool_startup,
        "simulation_seconds": simulation,
        "node_load": node_load,
    }
    write_results(args.output, "pool", args.workers, args, inputs, counts, timings)
    print(
        f"{len(inputs['fixtures'])} matches left; {args.seasons:,} seasons in "
        f"{simulation:.2f} s (pool startup {pool_startup:.3f} s, "
        f"loading {loading:.3f} s, fitting {fitting:.3f} s) -> {args.output}"
    )


if __name__ == "__main__":
    main()