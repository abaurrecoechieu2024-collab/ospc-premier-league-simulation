import tempfile
import unittest
from datetime import date
from pathlib import Path

import numpy as np

from src.baseline import batch_specs, simulate, simulate_batch
from src.model import Match, fit_rates, prepare_season, ranking, read_matches, update_table


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.teams = ["A", "B", "C", "D"]
        self.initial = [[0, 0, 0] for _ in self.teams]
        self.fixtures = [(h, a) for h in range(4) for a in range(4) if h != a]
        self.rates = [(1.6, 1.1)] * len(self.fixtures)

    def test_hand_calculated_table(self):
        # A beats B 2-0; B draws C 1-1; C beats A 3-0.
        table = [[0, 0, 0] for _ in range(3)]
        update_table(table, 0, 1, 2, 0)
        update_table(table, 1, 2, 1, 1)
        update_table(table, 2, 0, 3, 0)
        self.assertEqual(table, [[3, 2, 3], [1, 1, 3], [4, 4, 1]])
        self.assertEqual(ranking(table, ["A", "B", "C"]), [2, 0, 1])

    def test_tiebreak_order(self):
        table = [[3, 4, 2], [3, 3, 1], [3, 4, 2], [4, 0, 9]]
        self.assertEqual(ranking(table, ["Z", "B", "A", "D"]), [3, 2, 0, 1])

    def test_zero_rate_matches_have_known_outcome(self):
        counts = simulate(self.teams, self.initial, self.fixtures, [(0, 0)] * 12,
                          seasons=17, top_k=2, relegated=1)
        self.assertEqual(counts, [[17, 17, 0], [0, 17, 0], [0, 0, 0], [0, 0, 17]])

    def test_completed_season_is_deterministic(self):
        table = [[9, 3, 0], [6, 2, 1], [3, 1, 2], [0, 0, 3]]
        self.assertEqual(simulate(self.teams, table, [], [], 5, top_k=2, relegated=1),
                         [[5, 5, 0], [0, 5, 0], [0, 0, 0], [0, 0, 5]])

    def test_counts_and_repeatability_without_input_mutation(self):
        args = (self.teams, self.initial, self.fixtures, self.rates)
        a = simulate(*args, seasons=123, batch_size=17, top_k=2, relegated=1)
        self.assertEqual(a, simulate(*args, seasons=123, batch_size=17, top_k=2, relegated=1))
        self.assertEqual([sum(row[c] for row in a) for c in range(3)], [123, 246, 123])
        self.assertEqual(self.initial, [[0, 0, 0]] * 4)

    def test_batch_completion_order_does_not_matter(self):
        args = (self.teams, self.initial, self.fixtures, self.rates, 2, 1)
        partial = [simulate_batch(n, s, *args) for n, s in batch_specs(53, 10, 42)]
        combined = [[sum(batch[i][c] for batch in reversed(partial)) for c in range(3)]
                    for i in range(4)]
        self.assertEqual(combined, simulate(*args[:4], 53, 10, 42, 2, 1))

    def test_batch_seeds_match_spawn_all(self):
        expected = np.random.SeedSequence(42).spawn(6)
        actual = list(batch_specs(53, 10, 42))
        self.assertEqual([n for n, _ in actual], [10, 10, 10, 10, 10, 3])
        for (_, seed), ref in zip(actual, expected):
            np.testing.assert_array_equal(seed.generate_state(4), ref.generate_state(4))

    def test_cutoff_excludes_future_results(self):
        current = [Match(date(2026, 8, 1), "A", "B", 2, 0),
                   Match(date(2026, 9, 1), "B", "A", 9, 9)]
        teams, played, table, remaining = prepare_season(current, date(2026, 8, 15), 2)
        self.assertEqual(len(played), 1)
        self.assertEqual(table, [[3, 2, 0], [0, 0, 2]])
        self.assertEqual(remaining, [(1, 0)])

    def test_missing_team_history_uses_league_average(self):
        train = [Match(date(2025, 8, 1), "A", "B", 2, 1)]
        self.assertEqual(fit_rates(train, ["C", "D"], [(0, 1)]), [(2.0, 1.0)])

    def test_invalid_parameters(self):
        for kw in ({"seasons": 0}, {"batch_size": 0}, {"seed": -1}, {"top_k": 5}):
            with self.assertRaises(ValueError):
                simulate(self.teams, self.initial, self.fixtures, self.rates, **kw)
        with self.assertRaises(ValueError):
            simulate(self.teams, self.initial, self.fixtures, [])

    def test_no_relegation(self):
        counts = simulate(self.teams, self.initial, self.fixtures, self.rates,
                          seasons=5, top_k=2, relegated=0)
        self.assertEqual(sum(row[2] for row in counts), 0)

    def test_csv_validation(self):
        header = "Date,HomeTeam,AwayTeam,FTHG,FTAG\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            for bad in ("01/08/26,A,B,-1,0\n", "01/08/26,A,B,,\n",
                        "01/08/26,A,A,1,0\n", "bad,A,B,1,0\n",
                        "01/08/26,A,B,1,0\n02/08/26,A,B,1,0\n"):
                path.write_text(header + bad)
                with self.assertRaises(ValueError):
                    read_matches(path)
            path.write_text(header + "01/08/26,A,B,1,0\n")
            self.assertEqual(read_matches(path)[0].date, date(2026, 8, 1))


if __name__ == "__main__":
    unittest.main()
