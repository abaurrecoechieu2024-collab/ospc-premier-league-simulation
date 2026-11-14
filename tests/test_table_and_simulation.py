import numpy as np

from src.baseline import add_counts, run_baseline
from src.simulate import batch_seeds, generate_batch, simulate_batch
from src.table import rank_teams, update_table


def test_hand_calculated_table():
    # A beats B 2-0; B draws C 1-1; C beats A 3-0.
    table = [[0, 0, 0] for _ in range(3)]
    update_table(table, 0, 1, 2, 0)
    update_table(table, 1, 2, 1, 1)
    update_table(table, 2, 0, 3, 0)
    assert table == [[3, 2, 3], [1, 1, 3], [4, 4, 1]]
    assert rank_teams(table) == [2, 0, 1]


def test_tiebreak_rule():
    # teams 0 and 2 are level on points, goal difference and goals scored
    table = [[3, 4, 2], [3, 3, 1], [3, 4, 2], [4, 0, 9]]
    assert rank_teams(table) == [3, 0, 2, 1]                        # no random: team order
    assert rank_teams(table, [0.1, 0.5, 0.9, 0.0]) == [3, 2, 0, 1]  # higher random number wins


def small_inputs(rates=1.4):
    fixtures = [(h, a) for h in range(4) for a in range(4) if h != a]
    return {"teams": ["A", "B", "C", "D"], "table": [[9, 9, 0], [6, 6, 0], [3, 3, 0], [0, 0, 0]],
            "fixtures": fixtures, "rates": np.full((len(fixtures), 2), rates)}


def test_zero_rates_give_a_known_result():
    counts = run_baseline(17, 5, 1, small_inputs(rates=0.0))   # every match ends 0-0
    assert counts == [[17, 0, 0, 0], [0, 17, 0, 0], [0, 0, 17, 0], [0, 0, 0, 17]]


def test_every_season_counted_once():
    counts = run_baseline(123, 17, 7, small_inputs())
    assert all(sum(row) == 123 for row in counts)                 # each team has one position
    assert all(sum(col) == 123 for col in zip(*counts))           # each position has one team


def test_same_seed_same_counts():
    assert run_baseline(200, 30, 42, small_inputs()) == run_baseline(200, 30, 42, small_inputs())


def test_batch_order_does_not_matter():
    inputs = small_inputs()
    total = [[0] * 4 for _ in range(4)]
    for n, seed_seq in reversed(batch_seeds(53, 10, 42)):
        add_counts(total, simulate_batch(seed_seq, n, inputs))
    assert total == run_baseline(53, 10, 42, inputs)


def test_batch_seeds_are_spawned_streams():
    batches = batch_seeds(53, 10, 42)
    assert [n for n, _ in batches] == [10, 10, 10, 10, 10, 3]
    expected = np.random.SeedSequence(42).spawn(6)
    for (_, got), ref in zip(batches, expected):
        assert np.array_equal(got.generate_state(4), ref.generate_state(4))


def test_generate_batch_shapes():
    goals, tiebreak = generate_batch(np.random.SeedSequence(1), 5, np.full((12, 2), 1.5), 4)
    assert goals.shape == (5, 12, 2) and goals.dtype == np.int8
    assert tiebreak.shape == (5, 4)
