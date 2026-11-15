"""Line by line profile of simulate_batch (how is the time in the simulation distributed).

Example on how to use:
    python -m src.profile_lines --as-of 2026-11-14 --seasons 20000
"""
import argparse

import pandas as pd
from line_profiler import LineProfiler

from .baseline import prepare, run_baseline
from .simulate import simulate_batch

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--seasons", type=int, default=20000)
    args = parser.parse_args()

    inputs, model, loading, fitting = prepare("data/raw", pd.Timestamp(args.as_of))
    profiler = LineProfiler(simulate_batch)          # watch every line of this function
    profiler.runcall(run_baseline, args.seasons, 1000, 2026, inputs)
    profiler.print_stats()

if __name__ == "__main__":
    main()
