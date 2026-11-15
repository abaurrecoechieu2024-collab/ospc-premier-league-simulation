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


def test_pool_rejects_nonpositive_worker_count():
    with pytest.raises(ValueError, match="positive integer"):
        run_pool(10, 5, 42, small_inputs(), 0)
