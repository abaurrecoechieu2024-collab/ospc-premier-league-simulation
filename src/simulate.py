"""Simulate seasons. The batch is the unit of work every version shares.

Rule for exact equality between versions: each batch has its own random
stream (SeedSequence.spawn) and always draws in the same order:
  1. all its goals at once (seasons x matches x 2), then
  2. one tie-break number per team and season.
The batch size is fixed and never depends on the number of workers.
"""
import numpy as np

from .table import rank_teams, update_table


def expected_goals(model, teams, fixtures):
    """Expected (home, away) goals for every remaining match, shape (matches, 2)."""
    s = model["strength"]
    rates = [(model["mean_home"] * s[teams[h]]["home_attack"] * s[teams[a]]["away_defence"],
              model["mean_away"] * s[teams[a]]["away_attack"] * s[teams[h]]["home_defence"])
             for h, a in fixtures]
    return np.array(rates, dtype=float).reshape(len(fixtures), 2)


def batch_seeds(n_seasons, batch_size, seed):
    """[(seasons in batch, its random stream), ...]; the last batch may be smaller."""
    if n_seasons < 1 or batch_size < 1:
        raise ValueError("n_seasons and batch_size must be positive")
    n_batches = -(-n_seasons // batch_size)            # rounded up
    streams = np.random.SeedSequence(seed).spawn(n_batches)
    sizes = [min(batch_size, n_seasons - b * batch_size) for b in range(n_batches)]
    return list(zip(sizes, streams))


def generate_batch(seed_seq, n, rates, n_teams):
    """Step 1 and 2 of the rule above. Shared by the loop and vectorized versions."""
    rng = np.random.default_rng(seed_seq)
    goals = rng.poisson(rates, size=(n, len(rates), 2)).astype(np.int8)  # 8x less memory
    tiebreak = rng.random((n, n_teams))
    return goals, tiebreak


def simulate_batch(seed_seq, n, inputs):
    """Play n seasons with Python loops; return counts[team][final position]."""
    table0, fixtures, rates = inputs["table"], inputs["fixtures"], inputs["rates"]
    n_teams = len(table0)
    goals, tiebreak = generate_batch(seed_seq, n, rates, n_teams)
    counts = [[0] * n_teams for _ in range(n_teams)]
    for season in range(n):
        table = [row.copy() for row in table0]
        for (home, away), (hg, ag) in zip(fixtures, goals[season].tolist()):
            update_table(table, home, away, hg, ag)
        for position, team in enumerate(rank_teams(table, tiebreak[season].tolist())):
            counts[team][position] += 1
    return counts
