"""Naive baselines: is our simulation better than simple guesses?

Scored exactly like the backtest (same seasons, same snapshots, same scores):
  table_now   : every team finishes where it stands at the snapshot
  last_season : last season's final order (promoted teams at the bottom)
  uniform     : every team equally likely to finish in every position

Example:
    python -m src.naive_baselines --test-seasons 2025 2024 --every-matchweek
"""
import argparse
from pathlib import Path

import pandas as pd

from .backtest import actual_positions, score, snapshot_date
from .data import load_all
from .fixtures import current_matches, current_standings, team_list
from .table import rank_teams


def certain(order):
    """Counts for a forecast that is 100% sure of one final order (1 season)."""
    counts = [[0] * len(order) for _ in order]
    for position, team in enumerate(order):
        counts[team][position] = 1
    return counts


def last_season_order(matches, season, teams):
    """Teams in last season's final order; promoted teams (not in it) last."""
    prev = matches[(matches["div"] == "E0") & (matches["season"] == season - 1)]
    if prev.empty:
        return list(range(len(teams)))
    prev_teams = team_list(prev)
    prev_rank = {prev_teams[i]: r for r, i in enumerate(rank_teams(current_standings(prev, prev_teams)))}
    return sorted(range(len(teams)), key=lambda i: (prev_rank.get(teams[i], 99), teams[i]))


def evaluate(matches, season, played):
    past = matches[matches["season"] <= season]
    as_of = snapshot_date(past, season, played)
    current = current_matches(past, as_of)
    teams = team_list(current)
    actual = actual_positions(past, season, teams)
    n = len(teams)
    forecasts = {
        "table_now": (certain(rank_teams(current_standings(current, teams))), 1),
        "last_season": (certain(last_season_order(past, season, teams)), 1),
        "uniform": ([[1] * n for _ in range(n)], n),
    }
    return [{"model": name, "season": season, "played": played, **score(counts, actual, total)}
            for name, (counts, total) in forecasts.items()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--test-seasons", type=int, nargs="+", default=[2025])
    parser.add_argument("--played", type=int, nargs="+", default=[100])
    parser.add_argument("--every-matchweek", action="store_true")
    parser.add_argument("--compare", default="results/backtest-weekly-all.csv",
                        help="backtest CSV to show our models next to the baselines")
    args = parser.parse_args(argv)

    matches = load_all(args.data_dir)
    played = list(range(10, 380, 10)) if args.every_matchweek else args.played
    rows = []
    for s in args.test_seasons:
        for p in played:
            try:
                rows.extend(evaluate(matches, s, p))
            except ValueError as error:
                print(f"skipped {s} after {p} matches: {error}")
    result = pd.DataFrame(rows)
    columns = ["position_error", "brier_title", "brier_top4", "brier_relegation", "p_real_champion"]
    table = result.groupby("model", sort=False)[columns].mean()

    compare = Path(args.compare)
    if compare.exists():                         # add our models, same seasons and snapshots
        ours = pd.read_csv(compare)
        ours = ours[ours["season"].str[:4].astype(int).isin(args.test_seasons) & ours["played"].isin(played)]
        ours["model"] = ours["model"] + " " + ours["decay"].astype(str)
        table = pd.concat([table, ours.groupby("model", sort=False)[columns].mean()])
    pd.set_option("display.width", 200)
    print(table.round(3).to_string())
    print("\nLower is better for every column except p_real_champion.")


if __name__ == "__main__":
    main()
