#!/bin/bash
#SBATCH --job-name=strong_pool
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=64
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=results/strong_pool-%j.out

# Group 6 / Person C: strong-scaling experiment.
# Run from the repository root with: sbatch slurm/strong_pool.sbatch
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit this script with sbatch from the repository root}"
export PATH=/data/software/envs/ospc/bin:$PATH
export OMP_NUM_THREADS=1

SEASONS=2000000
BATCH_SIZE=1000
SEED=2026
AS_OF=2026-11-14
JOB_ID="${SLURM_JOB_ID:?This script must run through Slurm}"
NODE="${SLURMD_NODENAME:-$(hostname)}"
RESULTS_DIR="results/strong_pool/job-${JOB_ID}"
mkdir -p "$RESULTS_DIR"
CSV="$RESULTS_DIR/scaling.csv"

# Fail before collecting measurements if the pool/baseline tests are broken.
python -m pytest -q

printf 'version,workers,seasons,repetition,time,prepare_seconds,compute_seconds,pool_startup_seconds,loading_seconds,fitting_seconds,node,job_id,date,node_load,output_directory\n' > "$CSV"

# All 6 configurations x 5 repetitions run within ONE Slurm allocation.
for WORKERS in 1 2 4 8 16 32; do
    for REPETITION in 1 2 3 4 5; do
        RUN_DIR="$RESULTS_DIR/workers-${WORKERS}/repeat-${REPETITION}"
        mkdir -p "$RUN_DIR"
        LOG="$RUN_DIR/console.log"
        DATE_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        NODE_LOAD="$(awk '{print $1}' /proc/loadavg)"
        START="$(date +%s.%N)"

        echo "Starting workers=$WORKERS repeat=$REPETITION at $DATE_UTC on $NODE (job $JOB_ID)"
        python -m src.pool \
            --as-of "$AS_OF" \
            --seasons "$SEASONS" \
            --batch-size "$BATCH_SIZE" \
            --seed "$SEED" \
            --workers "$WORKERS" \
            --output "$RUN_DIR/output" 2>&1 | tee "$LOG"

        END="$(date +%s.%N)"
        WALL_SECONDS="$(awk -v a="$START" -v b="$END" 'BEGIN {printf "%.3f", b-a}')"

        # pool.py prints the phase timings after each successful run.
        SUMMARY="$(grep -E 'seasons in [0-9.]+ s \(pool startup' "$LOG" | tail -n 1 || true)"
        if [[ -z "$SUMMARY" ]]; then
            echo "Cannot parse pool timings from $LOG; check pool.py output" >&2
            exit 1
        fi
        SIMULATION_SECONDS="$(printf '%s\n' "$SUMMARY" | sed -nE 's/.*seasons in ([0-9.]+) s \(pool startup.*/\1/p')"
        POOL_STARTUP_SECONDS="$(printf '%s\n' "$SUMMARY" | sed -nE 's/.*pool startup ([0-9.]+) s,.*/\1/p')"
        LOADING_SECONDS="$(printf '%s\n' "$SUMMARY" | sed -nE 's/.*loading ([0-9.]+) s,.*/\1/p')"
        FITTING_SECONDS="$(printf '%s\n' "$SUMMARY" | sed -nE 's/.*fitting ([0-9.]+) s\).*/\1/p')"
        if [[ -z "$SIMULATION_SECONDS" || -z "$POOL_STARTUP_SECONDS" || -z "$LOADING_SECONDS" || -z "$FITTING_SECONDS" ]]; then
            echo "A phase timing is missing from $LOG" >&2
            exit 1
        fi
        PREPARE_SECONDS="$(awk -v a="$LOADING_SECONDS" -v b="$FITTING_SECONDS" 'BEGIN {printf "%.3f", a+b}')"

        printf 'pool,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
            "$WORKERS" "$SEASONS" "$REPETITION" "$WALL_SECONDS" \
            "$PREPARE_SECONDS" "$SIMULATION_SECONDS" "$POOL_STARTUP_SECONDS" \
            "$LOADING_SECONDS" "$FITTING_SECONDS" "$NODE" "$JOB_ID" \
            "$DATE_UTC" "$NODE_LOAD" "$RUN_DIR/output" >> "$CSV"
        echo "Saved measurement to $CSV (wall=${WALL_SECONDS}s, simulation=${SIMULATION_SECONDS}s)"
    done
done

echo "Finished 30 experiments. CSV: $CSV"
