"""Sequential Monte Carlo baseline: one season, one match at a time."""
import argparse
import csv
import hashlib
import json
import math
import os
import platform
import socket
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np

from .model import fit_rates, prepare_season, ranking, read_matches, season_year, update_table


def batch_specs(seasons, batch_size, seed):
    """Fixed logical batches: keep these identical in future parallel versions."""
    if seasons < 1 or batch_size < 1 or seed < 0:
        raise ValueError("Seasons/batch size must be positive and seed nonnegative")
    parent = np.random.SeedSequence(seed)
    for start in range(0, seasons, batch_size):
        yield min(batch_size, seasons - start), parent.spawn(1)[0]


def simulate_batch(size, child_seed, teams, initial, fixtures, rates, top_k, relegated):
    """Pure Python loops; NumPy is used only for scalar random goal draws."""
    rng = np.random.Generator(np.random.PCG64(child_seed))
    counts = [[0, 0, 0] for _ in teams]  # titles, top-k finishes, relegations
    for _ in range(size):
        table = [row.copy() for row in initial]
        for (home, away), (home_rate, away_rate) in zip(fixtures, rates):
            hg = int(rng.poisson(home_rate))
            ag = int(rng.poisson(away_rate))
            update_table(table, home, away, hg, ag)
        order = ranking(table, teams)
        counts[order[0]][0] += 1
        for team in order[:top_k]:
            counts[team][1] += 1
        if relegated:
            for team in order[-relegated:]:
                counts[team][2] += 1
    return counts


def simulate(teams, initial, fixtures, rates, seasons=1000, batch_size=100,
             seed=2026, top_k=4, relegated=3):
    if not 1 <= top_k <= len(teams) or not 0 <= relegated < len(teams):
        raise ValueError("Invalid top-k or relegation count")
    if len(fixtures) != len(rates) or len(initial) != len(teams):
        raise ValueError("Fixture/rate or team/table lengths differ")
    if any(not math.isfinite(x) or x < 0 for pair in rates for x in pair):
        raise ValueError("Goal rates must be finite and nonnegative")
    totals = [[0, 0, 0] for _ in teams]
    for size, child_seed in batch_specs(seasons, batch_size, seed):
        counts = simulate_batch(size, child_seed, teams, initial, fixtures, rates, top_k, relegated)
        for total, count in zip(totals, counts):
            for column in range(3):
                total[column] += count[column]
    return totals


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, nargs="+", required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--seasons", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--workers", type=int, choices=[1], default=1)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--relegated", type=int, default=3)
    parser.add_argument("--expected-teams", type=int, default=20)
    parser.add_argument("--prior-games", type=float, default=5.0)
    parser.add_argument("--repetition", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True, help="New directory; existing outputs are not overwritten")
    args = parser.parse_args(argv)
    if (args.seasons < 1 or args.batch_size < 1 or args.seed < 0 or args.repetition < 1
            or not math.isfinite(args.prior_games) or args.prior_games <= 0):
        parser.error("Invalid seasons, batch size, seed, repetition, or prior")
    if args.output.exists():
        parser.error("Output directory already exists; choose a new run directory")

    started = perf_counter()
    try:
        current = read_matches(args.current)
        history = [m for path in args.history for m in read_matches(path)]
        keys = [(season_year(m.date), m.home, m.away) for m in history]
        if len(keys) != len(set(keys)):
            raise ValueError("Overlapping or duplicate history files")
        teams, played, initial, fixtures = prepare_season(current, args.as_of, args.expected_teams)
        if any(season_year(m.date) >= season_year(current[0].date) for m in history):
            raise ValueError("History must contain only seasons before the target season")
        if not 1 <= args.top_k <= len(teams) or not 0 <= args.relegated < len(teams):
            raise ValueError("Invalid top-k or relegation count")
    except ValueError as error:
        parser.error(str(error))
    input_hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [*args.history, args.current]}
    loading_seconds = perf_counter() - started

    start = perf_counter()
    rates = fit_rates(history + played, teams, fixtures, args.prior_games)
    fitting_seconds = perf_counter() - start
    load_before = os.getloadavg()
    start = perf_counter()
    totals = simulate(teams, initial, fixtures, rates, args.seasons, args.batch_size,
                      args.seed, args.top_k, args.relegated)
    simulation_seconds = perf_counter() - start
    load_after = os.getloadavg()
    assert [sum(row[i] for row in totals) for i in range(3)] == [
        args.seasons, args.top_k * args.seasons, args.relegated * args.seasons]

    metadata = {
        "version": "sequential", "workers": 1, "problem_size": args.seasons,
        "repetition": args.repetition, "elapsed_seconds": simulation_seconds,
        "fitting_seconds": fitting_seconds, "loading_seconds": loading_seconds,
        "compute_seconds": fitting_seconds + simulation_seconds,
        "node": socket.gethostname(), "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""),
        "date": datetime.now(timezone.utc).isoformat(),
        "node_load_1m_before": load_before[0], "node_load_1m_after": load_after[0],
        "seed": args.seed, "batch_size": args.batch_size, "numpy_version": np.__version__,
        "python_version": platform.python_version(), "as_of": str(args.as_of),
        "completed_matches": len(played), "remaining_matches": len(fixtures),
        "training_matches": len(history) + len(played), "top_k": args.top_k,
        "relegated": args.relegated, "prior_games": args.prior_games,
        "ranking_rule": "points, goal difference, goals for, alphabetical fallback",
        "input_sha256": input_hashes,
        "local_smoke_test_only": "SLURM_JOB_ID" not in os.environ,
    }
    try:
        metadata["git_revision"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        metadata["git_revision"] = "unavailable"
    args.output.mkdir(parents=True, exist_ok=False)
    write_start = perf_counter()
    with (args.output / "probabilities.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["team", "titles", "top_k_finishes", "relegations",
                         "title_probability", "top_k_probability", "relegation_probability"])
        for team, counts in zip(teams, totals):
            writer.writerow([team, *counts, *(count / args.seasons for count in counts)])
    with (args.output / "current_table.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["rank", "team", "points", "goals_for", "goals_against"])
        for rank, i in enumerate(ranking(initial, teams), 1):
            writer.writerow([rank, teams[i], *initial[i]])
    metadata["result_writing_seconds"] = perf_counter() - write_start
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    flat = {k: v for k, v in metadata.items() if not isinstance(v, dict)}
    with (args.output / "timing.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat))
        writer.writeheader(); writer.writerow(flat)
    print(f"{len(teams)} teams; {len(played)} completed / {len(fixtures)} remaining matches")
    print(f"{args.seasons:,} simulated seasons in {simulation_seconds:.3f}s; fitting {fitting_seconds:.4f}s")
    print(f"Results: {args.output}")
    print("Top-k is a finishing-position proxy, not official European qualification.")


if __name__ == "__main__":
    main()
