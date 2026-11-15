"""Add up the counts of all array tasks and check they equal the baseline's.

Example:
    python -m src.merge_array --folder tmp/array --baseline tmp/base/counts.csv
"""
import argparse
from pathlib import Path

import pandas as pd


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True, help="where the tasks saved their counts")
    parser.add_argument("--baseline", type=Path, required=True, help="counts.csv of a baseline run")
    args = parser.parse_args(argv)

    files = sorted(args.folder.glob("counts_task*.csv"))
    merged = sum(pd.read_csv(f, index_col=0) for f in files)
    merged.to_csv(args.folder / "counts_merged.csv")
    baseline = pd.read_csv(args.baseline, index_col=0)

    equal = merged.equals(baseline)
    print(f"{len(files)} tasks merged; seasons per team: {int(merged.sum(axis=1).iloc[0]):,}")
    print("EQUAL to the baseline" if equal else "DIFFERENT from the baseline")
    timings = pd.concat(pd.read_csv(f) for f in sorted(args.folder.glob("timing_task*.csv")))
    timings.to_csv(args.folder / "timing_all_tasks.csv", index=False)
    print(timings[["task_id", "batches", "simulation_seconds", "node"]].to_string(index=False))
    if not equal:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
