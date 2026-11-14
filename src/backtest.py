"""Backtest: would our model have predicted a finished season well?

We pretend we are at the same point of a past season (after the same number of
matches as our 2026/27 snapshot), use only data available then, simulate the rest,
and compare with how that season really ended.

It compares three models:
  simple : last season + this season, equal weights, no Championship (our first version)
  multi  : all past Premier League seasons, weighted by --decays, no Championship
  full   : multi + Championship games for promoted teams (tested, not our default)
Our final model is multi with decay 0.5 (the default of src.baseline).

Example (season 2025 = 2025/26):
    python -m src.backtest --test-seasons 2025 2024 --decays 0.5 0.25 0.1
Every matchweek (10, 20, ..., 370 matches played), as the forecast is updated weekly:
    python -m src.backtest --test-seasons 2025 2024 --models simple multi full --decays 0.5 1.0 --every-matchweek
"""
import argparse

import pandas as pd

from .baseline import prepare, run_baseline
from .data import load_all
from .fixtures import current_standings
from .table import rank_teams


def snapshot_date(matches, season, played):
    """Date of the `played`-th Premier League match of `season`."""
    dates = matches[(matches["div"] == "E0") & (matches["season"] == season)]["date"].sort_values()
    return dates.iloc[played - 1]


def actual_positions(matches, season, teams):
    """Real final position (1-20) of every team, from all of the season's results."""
    full = matches[(matches["div"] == "E0") & (matches["season"] == season)]
    order = rank_teams(current_standings(full, teams))
    position = [0] * len(teams)
    for rank, team in enumerate(order, 1):
        position[team] = rank
    return position


def score(counts, actual, n_seasons):
    """How close the simulated positions were to the real ones (lower is better)."""
    n_teams = len(actual)
    expected_pos = [sum((p + 1) * c for p, c in enumerate(row)) / n_seasons for row in counts]

    def brier(first, last):
        # mean of (predicted probability - what happened)^2, what happened = 1 or 0
        total = 0.0
        for row, pos in zip(counts, actual):
            p = sum(row[first - 1:last]) / n_seasons
            total += (p - (first <= pos <= last)) ** 2
        return total / n_teams

    champion = actual.index(1)
    return {"position_error": sum(abs(e - a) for e, a in zip(expected_pos, actual)) / n_teams,
            "brier_title": brier(1, 1), "brier_top4": brier(1, 4),
            "brier_relegation": brier(n_teams - 2, n_teams),
            "p_real_champion": counts[champion][0] / n_seasons}


def model_data(matches, season, model):
    """The matches each model is allowed to use for a test season."""
    past = matches[matches["season"] <= season]              # nothing from later seasons
    if model in ("simple", "multi"):
        past = past[past["div"] == "E0"]                     # no Championship
    if model == "simple":
        past = past[past["season"] >= season - 1]            # only last season
    return past


def backtest(matches, season, played, model, decay, n_seasons, seed):
    past = model_data(matches, season, model)
    as_of = snapshot_date(past, season, played)
    inputs, _, _, _ = prepare(None, as_of, decay, matches=past, championship=(model == "full"))
    counts = run_baseline(n_seasons, 1000, seed, inputs)
    return {"season": f"{season}/{(season + 1) % 100:02d}", "model": model, "decay": decay,
            "played": played, "as_of": as_of.date(), "remaining": len(inputs["fixtures"]),
            **score(counts, actual_positions(past, season, inputs["teams"]), n_seasons)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--test-seasons", type=int, nargs="+", default=[2025])
    parser.add_argument("--played", type=int, nargs="+", default=[100],
                        help="matches played at the snapshot (one or more values)")
    parser.add_argument("--every-matchweek", action="store_true",
                        help="test after 10, 20, ..., 370 matches (overrides --played)")
    parser.add_argument("--decays", type=float, nargs="+", default=[0.5, 0.25, 0.1])
    parser.add_argument("--models", nargs="+", default=["simple", "multi", "full"],
                        choices=["simple", "multi", "full"])
    parser.add_argument("--seasons", type=int, default=10000, help="simulated seasons per run")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output", default="results/backtest.csv")
    args = parser.parse_args(argv)

    matches = load_all(args.data_dir)
    runs = [(m, 1.0) if m == "simple" else (m, d)        # simple = equal weights, as before
            for m in args.models for d in (args.decays if m != "simple" else [1.0])]
    played = list(range(10, 380, 10)) if args.every_matchweek else args.played
    rows = []
    for s in args.test_seasons:
        for p in played:
            for m, d in runs:
                try:
                    rows.append(backtest(matches, s, p, m, d, args.seasons, args.seed))
                except ValueError as error:          # e.g. a team has not played yet
                    print(f"skipped {s} after {p} matches: {error}")
    result = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    if len(played) == 1:
        print(result.round(3).to_string(index=False))
    else:
        print("Position error by matchweek (average over the tested seasons):")
        print(result.pivot_table(index="played", columns=["model", "decay"],
                                 values="position_error").round(2).to_string())
    print("\nAverage over everything tested:")
    print(result.drop(columns=["season", "as_of", "remaining", "played"])
          .groupby(["model", "decay"], sort=False).mean().round(3).to_string())
    result.to_csv(args.output, index=False)
    print(f"\nSaved to {args.output}. Lower is better for every column except p_real_champion.")


if __name__ == "__main__":
    main()
