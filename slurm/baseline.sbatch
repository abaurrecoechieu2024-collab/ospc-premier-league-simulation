#!/bin/bash
#SBATCH --job-name=football-baseline
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=01:00:00
#SBATCH --output=baseline-%j.out

# Submit from the repository root. Add course account/partition flags if required.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?Submit this file with sbatch from the repository root}"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
SEASONS="${SEASONS:-1000}"
for repetition in 1 2 3 4 5; do
  "$PYTHON_BIN" -m src.baseline \
    --history data/raw/E0_2526.csv --current data/raw/E0_2627.csv \
    --as-of 2026-11-14 --seasons "$SEASONS" --batch-size 100 --seed 2026 \
    --repetition "$repetition" --output "results/job-${SLURM_JOB_ID}/rep-${repetition}"
done
