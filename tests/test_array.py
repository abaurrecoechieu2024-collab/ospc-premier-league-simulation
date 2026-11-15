"""The job-array version must reproduce the baseline counts exactly."""
import pandas as pd

from src.array_task import my_batches
from src.baseline import add_counts, prepare, run_baseline
from src.simulate import batch_seeds, simulate_batch


def test_blocks_cover_every_batch_once():
    batches = list(range(11))                      # 11 batches over 4 tasks: 2, 3, 3, 3
    blocks = [my_batches(batches, t, 4) for t in range(4)]
    assert sum(blocks, []) == batches


def test_array_counts_equal_baseline():
    inputs, *_ = prepare("data/raw", pd.Timestamp("2026-11-14"))
    seasons, batch_size, seed = 2500, 1000, 2026   # 3 batches, the last one smaller
    n_teams = len(inputs["teams"])
    merged = [[0] * n_teams for _ in range(n_teams)]
    batches = batch_seeds(seasons, batch_size, seed)
    for task in range(4):                          # more tasks than batches: one task gets none
        for n, seed_seq in my_batches(batches, task, 4):
            add_counts(merged, simulate_batch(seed_seq, n, inputs))
    assert merged == run_baseline(seasons, batch_size, seed, inputs)
