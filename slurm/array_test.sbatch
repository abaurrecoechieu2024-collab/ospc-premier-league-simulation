#!/bin/bash
#SBATCH --job-name=array-test
#SBATCH --partition=cpu
#SBATCH --array=0-3%4
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=results/array/array-%A_%a.out
# Job-array test: 4 tasks, each simulates its own block of batches.
# Each array task counts as one job (limit: 4 running, 8 submitted).
# Submit from the repository root:  mkdir -p results/array && sbatch slurm/array_test.sbatch
# Then merge and check:             python -m src.merge_array --folder results/array/job-<ID> --baseline <baseline counts.csv>

set -euo pipefail
export PATH=/data/software/envs/ospc/bin:$PATH   # course Python (cluster guide, section 5)
export OMP_NUM_THREADS=1                          # no hidden library threads
SEASONS="${SEASONS:-100000}"

python -m src.array_task --as-of 2026-11-14 --seasons "$SEASONS" --batch-size 1000 --seed 2026 \
  --output "results/array/job-${SLURM_ARRAY_JOB_ID}"
