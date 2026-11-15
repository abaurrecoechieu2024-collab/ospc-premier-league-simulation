#!/bin/bash
#SBATCH --job-name=strong-pool
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=64
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=results/strong-pool-%j.out

# Person C: fixed-workload strong scaling (one allocation, 30 runs).
# Submit from the GitHub repository root, after the pool correctness tests pass:
#   sbatch slurm/strong_pool.sbatch
# Optional size override after a measured one-worker calibration:
#   SEASONS=1000000 sbatch slurm/strong_pool.sbatch
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit with sbatch from the repository root}"
export PATH=/data/software/envs/ospc/bin:$PATH
export OMP_NUM_THREADS=1
export PYTHONUNBUFFERED=1

SEASONS="${SEASONS:-2000000}"
BATCH_SIZE=1000
SEED=2026
AS_OF=2026-11-14
JOB_ID="${SLURM_JOB_ID:?Submit this script with sbatch}"
RESULTS_DIR="results/strong_pool/job-${JOB_ID}"
CSV="${RESULTS_DIR}/scaling.csv"
CODE_REVISION="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
mkdir -p "$RESULTS_DIR"

# Never measure incorrect pool output. Person A must confirm equivalence first.
python -m pytest -q

# Each run generates its own output/timing.csv using the existing src.baseline.write_results().
# Append a summary row immediately after each successful run so partial results
# survive a later timeout, failure, or cancellation.
for WORKERS in 1 2 4 8 16 32; do
  for REPETITION in 1 2 3 4 5; do
    RUN_DIR="${RESULTS_DIR}/workers-${WORKERS}/repeat-${REPETITION}"
    mkdir -p "$RUN_DIR"
    NODE_LOAD_BEFORE="$(awk '{print $1}' /proc/loadavg)"
    START="$(date +%s.%N)"
    echo "Running workers=${WORKERS}, repetition=${REPETITION}, job=${JOB_ID}, node=${SLURMD_NODENAME:-$(hostname)}"

    python -m src.pool \
      --as-of "$AS_OF" \
      --seasons "$SEASONS" \
      --batch-size "$BATCH_SIZE" \
      --seed "$SEED" \
      --repetition "$REPETITION" \
      --workers "$WORKERS" \
      --output "${RUN_DIR}/output" 2>&1 | tee "${RUN_DIR}/console.log"

    END="$(date +%s.%N)"
    WALL_SECONDS="$(awk -v a="$START" -v b="$END" 'BEGIN {printf "%.6f", b-a}')"

    python - "${RUN_DIR}/output/timing.csv" "$CSV" "$WALL_SECONDS" "$NODE_LOAD_BEFORE" "$CODE_REVISION" <<'PY'
import csv
import os
import sys

source_path, target_path, wall, load_before, revision = sys.argv[1:]
with open(source_path, newline="") as f:
    source_rows = list(csv.DictReader(f))
if len(source_rows) != 1:
    raise ValueError(f"Expected exactly one timing row in {source_path}")
r = source_rows[0]
prepare = float(r["loading_seconds"]) + float(r["fitting_seconds"])
compute = float(r["pool_startup_seconds"]) + float(r["simulation_seconds"])
record = {
    "version": r["version"],
    "workers": r["workers"],
    "seasons": r["seasons"],
    "batch_size": r["batch_size"],
    "seed": r["seed"],
    "repetition": r["repetition"],
    "time": wall,                  # whole command's wall time, including setup and output
    "elapsed_seconds": wall,
    "prepare_seconds": f"${prepare:.6f}",
    "compute_seconds": f"${compute:.6f}",  # pool startup + simulation
    "pool_startup_seconds": r["pool_startup_seconds"],
    "simulation_seconds": r["simulation_seconds"],
    "loading_seconds": r["loading_seconds"],
    "fitting_seconds": r["fitting_seconds"],
    "writing_seconds": r["writing_seconds"],
    "node": r["node"],
    "slurm_job_id": r["slurm_job_id"],
    "date": r["date"],
    "node_load": r["node_load"],    # 1-minute load average sampled by src.pool
    "node_load_before": load_before,
    "as_of": r["as_of"],
    "code_revision": revision,
    "source_timing_csv": source_path,
}
header = not os.path.exists(target_path) or os.path.getsize(target_path) == 0
with open(target_path, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=record.keys())
    if header:
        writer.writeheader()
    writer.writerow(record)
PY
    echo "Saved ${WORKERS} workers, repetition ${REPETITION} to ${CSV}"
  done
done

echo "Completed 30 runs. Summary CSV: ${CSV}"
