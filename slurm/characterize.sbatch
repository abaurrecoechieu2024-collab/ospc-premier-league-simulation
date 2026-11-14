#!/bin/bash
#SBATCH --job-name=characterize
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:30:00
#SBATCH --output=results/characterize/characterize-%j.out

set -euo pipefail
export PATH=/data/software/envs/ospc/bin:$PATH
export OMP_NUM_THREADS=1

/usr/bin/time -v python -m src.baseline --as-of 2026-11-14 --seasons 1000000 \
  --output "results/characterize/job-${SLURM_JOB_ID}"