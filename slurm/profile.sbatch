#!/bin/bash
#SBATCH --job-name=profile
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:20:00
#SBATCH --output=results/profile/profile-%j.out
# Profile the baseline on one core: cProfile (time per function) and
# line_profiler (time per line of simulate_batch).
# Submit from the repository root:  mkdir -p results/profile && sbatch slurm/profile.sbatch

set -euo pipefail
export PATH=/data/software/envs/ospc/bin:$PATH   # course Python (cluster guide, section 5)
export OMP_NUM_THREADS=1                          # no hidden library threads
SEASONS="${SEASONS:-200000}"
OUT="results/profile/job-${SLURM_JOB_ID}"
mkdir -p "$OUT"
PROF=$(mktemp)                                    # binary profile, not committed

python -m cProfile -o "$PROF" -m src.baseline --as-of 2026-11-14 --seasons "$SEASONS" \
  --output "$OUT/run"
python -c "import pstats, sys; pstats.Stats(sys.argv[1]).sort_stats('cumulative').print_stats('run_baseline|simulate_batch|update_table|generate_batch|rank_teams|prepare|write_results|baseline.py')" \
  "$PROF" > "$OUT/cprofile.txt"
python -m src.profile_lines --as-of 2026-11-14 --seasons 20000 > "$OUT/line_profile.txt"
rm -f "$PROF"
