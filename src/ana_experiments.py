"""Local learning checks using the team's unchanged baseline.

Run from the repository root:
python -m src.ana_experiments --output results/ana-2026-11-15
"""
import argparse
import hashlib
import json
import platform
import socket
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .baseline import main as baseline_main, prepare
from .data import load_all


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--source-revision", default="unrecorded")
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    inputs = sorted(Path(args.data_dir).glob("E[01]_*.csv"))
    manifest = {
        "purpose": "local learning/correctness checks, not cluster benchmarks",
        "source_revision": args.source_revision,
        "python": sys.version, "numpy": np.__version__, "pandas": pd.__version__,
        "platform": platform.platform(), "node": socket.gethostname(),
        "seed": 2026, "batch_size": 1000, "as_of": "2026-11-14",
        "input_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    }
    counts, probabilities, checks, timings, commands = {}, {}, [], [], []
    for label, n in [("n1000-a", 1000), ("n1000-b", 1000),
                     ("n10000", 10000), ("n50000", 50000)]:
        folder = args.output / label
        cli = ["--data-dir", args.data_dir, "--as-of", "2026-11-14", "--seasons", str(n),
               "--batch-size", "1000", "--seed", "2026", "--output", str(folder)]
        commands.append([sys.executable, "-m", "src.baseline", *cli])
        baseline_main(cli)
        c = pd.read_csv(folder / "counts.csv", index_col=0)
        p = pd.read_csv(folder / "probabilities.csv").set_index("team")
        counts[label], probabilities[label] = c, p
        test_results = {
            "20_by_20_counts": c.shape == (20, 20),
            "nonnegative_integer_counts": bool((c.to_numpy() >= 0).all() and
                                                (c.to_numpy() % 1 == 0).all()),
            "every_team_counted_once_per_season": bool((c.sum(axis=1) == n).all()),
            "every_position_filled_once_per_season": bool((c.sum(axis=0) == n).all()),
            "probabilities_in_range": bool(((p >= 0) & (p <= 1)).all().all()),
            "probability_totals_1_4_6_3": bool(np.allclose(
                p[["title", "top4", "top6", "relegation"]].sum(), [1, 4, 6, 3])),
            "nested_top_positions": bool(((p.title <= p.top4) & (p.top4 <= p.top6)).all()),
        }
        checks.extend({"run": label, "check": key, "passed": value}
                      for key, value in test_results.items())
        row = pd.read_csv(folder / "timing.csv").iloc[0].to_dict()
        row["run"] = label
        timings.append(row)
    checks.append({"run": "n1000-a vs n1000-b", "check": "identical_position_counts",
                   "passed": counts["n1000-a"].equals(counts["n1000-b"])})
    comparisons = []
    for left, right in [("n1000-a", "n10000"), ("n10000", "n50000")]:
        difference = (probabilities[left] - probabilities[right]).abs() * 100
        for metric in ("title", "top4", "top6", "relegation"):
            comparisons.append({"comparison": f"{left} vs {right}", "metric": metric,
                                "max_change_percentage_points": difference[metric].max(),
                                "team_at_max_change": difference[metric].idxmax()})
    # Controlled experiment: changing scores AFTER an earlier cutoff must not
    # change either its starting table or its fitted goal rates.
    matches = load_all(args.data_dir)
    cutoff = pd.Timestamp("2026-10-01")
    earlier, _, _, _ = prepare(args.data_dir, cutoff, matches=matches)
    changed = matches.copy()
    future = (changed["season"] == 2026) & (changed["date"] > cutoff)
    changed.loc[future, ["home_goals", "away_goals"]] = 99
    altered, _, _, _ = prepare(args.data_dir, cutoff, matches=changed)
    no_leakage = (earlier["teams"] == altered["teams"] and earlier["table"] == altered["table"]
                  and earlier["fixtures"] == altered["fixtures"]
                  and np.array_equal(earlier["rates"], altered["rates"]))
    checks.append({"run": "cutoff-2026-10-01", "check": "future_scores_do_not_leak",
                   "passed": bool(future.any() and no_leakage)})
    manifest["future_score_rows_changed_in_memory"] = int(future.sum())
    manifest["commands"] = commands
    pd.DataFrame(checks).to_csv(args.output / "checks.csv", index=False)
    pd.DataFrame(comparisons).to_csv(args.output / "probability_changes.csv", index=False)
    pd.DataFrame(timings).to_csv(args.output / "local_timings.csv", index=False)
    (args.output / "environment.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(pd.DataFrame(comparisons).to_string(index=False))
    if not all(c["passed"] for c in checks):
        raise AssertionError("At least one check failed; inspect checks.csv")
    print(f"All {len(checks)} checks passed. Raw results: {args.output}")
    print("Shared seed/batches give overlapping samples: these differences are descriptive,")
    print("not an independent-sample significance test or proof the model predicts accurately.")


if __name__ == "__main__":
    main()
