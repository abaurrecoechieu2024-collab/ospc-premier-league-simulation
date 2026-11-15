import numpy as np
import pytest

from src.baseline import run_baseline
from src.pool import run_pool


def small_inputs():
    fixtures = [(home, away) for home in range(4) for away in range(4) if home != away]
    return {
        "teams": ["A", "B", "C", "D"],
        "table": [[9, 9, 0], [6, 6, 0], [3, 3, 0], [0, 0, 0]],
        "fixtures": fixtures,
        "rates": np.full((len(fixtures), 2), 1.4),
    }


@pytest.mark.parametrize("workers", [1, 2, 4])
def test_pool_counts_match_baseline(workers):
    inputs = small_inputs()
    expected = run_baseline(53, 10, 42, inputs)

    counts, _, _ = run_pool(53, 10, 42, inputs, workers)

    assert counts == expected


def test_pool_initializes_each_call_with_its_own_inputs():
    first_inputs = small_inputs()
    second_inputs = small_inputs()
    second_inputs["table"] = [[0, 0, 0], [3, 0, 1], [6, 0, 2], [9, 0, 3]]
    second_inputs["rates"] = np.full((len(second_inputs["fixtures"]), 2), 0.6)

    first_expected = run_baseline(37, 8, 24, first_inputs)
    first_counts, _, _ = run_pool(37, 8, 24, first_inputs, 2)
    second_expected = run_baseline(37, 8, 24, second_inputs)
    second_counts, _, _ = run_pool(37, 8, 24, second_inputs, 2)

    assert first_counts == first_expected
    assert second_counts == second_expected


def test_pool_rejects_nonpositive_worker_count():
    with pytest.raises(ValueError, match="positive integer"):
        run_pool(10, 5, 42, small_inputs(), 0)


def test_pool_allows_workers_without_slurm_allocation(monkeypatch):
    monkeypatch.delenv("SLURM_CPUS_PER_TASK", raising=False)

    counts, _, _ = run_pool(13, 5, 42, small_inputs(), 4)

    assert all(sum(row) == 13 for row in counts)


def test_pool_rejects_workers_above_slurm_allocation(monkeypatch):
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "2")

    with pytest.raises(ValueError, match=r"--workers \(4\).*SLURM_CPUS_PER_TASK \(2\)"):
        run_pool(10, 5, 42, small_inputs(), 4)


def test_pool_rejects_invalid_slurm_allocation(monkeypatch):
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "not-an-integer")

    with pytest.raises(ValueError, match="SLURM_CPUS_PER_TASK must be a positive integer"):
        run_pool(10, 5, 42, small_inputs(), 2)
