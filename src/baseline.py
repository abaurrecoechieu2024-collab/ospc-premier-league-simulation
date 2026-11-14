"""Sequential baseline: run every batch one after another in one process.

Example:
    python -m src.baseline --as-of 2026-11-14 --seasons 1000 --output results/test-run
"""
import argparse
import os
import socket
from datetime import datetime
from pathlib import Path
from time import perf_counter

import pandas as pd

from .data import load_all
from .fixtures import current_matches, current_standings, remaining_fixtures, team_list
from .simulate import batch_seeds, expected_goals, simulate_batch
from .strengths import fit_strengths
from .table import rank_teams


def prepare(data_dir, as_of, decay=0.5, prior_games=5.0, matches=None, championship=False):
    """Serial part: load data, build the current table, fit strengths.

    Returns the inputs every version needs and the two serial timings.
    `matches` lets the backtest pass a table that stops at an earlier season.
    """
    start = perf_counter()
    if matches is None:
        matches = load_all(data_dir)
    current = current_matches(matches, as_of)
    teams = team_list(current)
    table = current_standings(current, teams)
    fixtures = remaining_fixtures(current, teams)
    loading_seconds = perf_counter() - start

    start = perf_counter()
    model = fit_strengths(matches, teams, as_of, decay, prior_games, championship)
    rates = expected_goals(model, teams, fixtures)
    fitting_seconds = perf_counter() - start

    inputs = {"teams": teams, "table": table, "fixtures": fixtures, "rates": rates}
    return inputs, model, loading_seconds, fitting_seconds


def add_counts(total, counts):
    for t_row, c_row in zip(total, counts):
        for position, value in enumerate(c_row):
            t_row[position] += value


def run_baseline(n_seasons, batch_size, seed, inputs):
    """Total counts[team][final position] over all batches."""
    n_teams = len(inputs["teams"])
    total = [[0] * n_teams for _ in range(n_teams)]
    for n, seed_seq in batch_seeds(n_seasons, batch_size, seed):
        add_counts(total, simulate_batch(seed_seq, n, inputs))
    return total


def summarize(counts, teams, n_seasons):
    """Title, top 4, top 6 and relegation probabilities from the position counts."""
    rows = []
    for team, c in zip(teams, counts):
        rows.append({"team": team, "title": c[0] / n_seasons, "top4": sum(c[:4]) / n_seasons,
                     "top6": sum(c[:6]) / n_seasons, "relegation": sum(c[-3:]) / n_seasons})
    return pd.DataFrame(rows).sort_values(["title", "top4", "top6"], ascending=False)


def write_results(output, version, workers, args, inputs, counts, timings):
    """Results, current table, raw counts and one timing row (CSV) per run."""
    output.mkdir(parents=True, exist_ok=False)
    teams = inputs["teams"]
    start = perf_counter()
    summarize(counts, teams, args.seasons).to_csv(output / "probabilities.csv", index=False)
    pd.DataFrame(counts, index=teams, columns=range(1, len(teams) + 1)).to_csv(output / "counts.csv")
    table = [[teams[i], *inputs["table"][i]] for i in rank_teams(inputs["table"])]
    pd.DataFrame(table, columns=["team", "points", "goals_for", "goals_against"]).to_csv(
        output / "current_table.csv", index=False)
    timings["writing_seconds"] = perf_counter() - start
    row = {"version": version, "workers": workers, "seasons": args.seasons,
           "batch_size": args.batch_size, "seed": args.seed, "repetition": args.repetition,
           **timings, "node": socket.gethostname(),
           "slurm_job_id": os.environ.get("SLURM_JOB_ID", "local"),
           "date": datetime.now().isoformat(timespec="seconds"), "as_of": args.as_of,
           "decay": args.decay, "championship": args.championship}
    pd.DataFrame([row]).to_csv(output / "timing.csv", index=False)


def parse_args(argv=None, workers=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--as-of", required=True, help="snapshot date, e.g. 2026-11-14")
    parser.add_argument("--seasons", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--repetition", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True, help="a new folder for this run")
    parser.add_argument("--championship", action="store_true",
                        help="also use Championship games for promoted teams (off by default)")
    parser.add_argument("--decay", type=float, default=0.5,
                        help="weight per season back in time (this season = 1)")
    if workers:
        parser.add_argument("--workers", type=int, required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    inputs, model, loading, fitting = prepare(args.data_dir, pd.Timestamp(args.as_of), args.decay,
                                               championship=args.championship)

    load_before = os.getloadavg()[0]          # the "load average" htop shows
    start = perf_counter()
    counts = run_baseline(args.seasons, args.batch_size, args.seed, inputs)
    simulation = perf_counter() - start

    timings = {"loading_seconds": loading, "fitting_seconds": fitting,
               "simulation_seconds": simulation, "node_load": load_before}
    write_results(args.output, "baseline", 1, args, inputs, counts, timings)
    print(f"{len(inputs['fixtures'])} matches left; {args.seasons:,} seasons in {simulation:.2f} s "
          f"(loading {loading:.3f} s, fitting {fitting:.3f} s) -> {args.output}")


if __name__ == "__main__":
    main()
