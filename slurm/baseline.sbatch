#!/bin/bash
#SBATCH --job-name=football-baseline
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=01:00:00
#SBATCH --output=baseline-%j.out
# 2 CPUs = 1 physical core (Slurm counts both hardware threads): the baseline uses one.
# Submit from the repository root:  sbatch slurm/baseline.sbatch
# Change the size with:             SEASONS=200000 sbatch slurm/baseline.sbatch

set -euo pipefail
export PATH=/data/software/envs/ospc/bin:$PATH   # course Python (cluster guide, section 5)
export OMP_NUM_THREADS=1                          # no hidden library threads
SEASONS="${SEASONS:-10000}"

for repetition in 1 2 3 4 5; do
  python -m src.baseline --as-of 2026-11-14 --seasons "$SEASONS" --batch-size 1000 \
    --seed 2026 --repetition "$repetition" \
    --output "results/baseline/job-${SLURM_JOB_ID}/rep-${repetition}"
done
