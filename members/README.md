# Members: experiments and measurements

Each member keeps a short log of what they tested in
`members/<your-name>/experiments_measurements.md`. It is our shared memory for the
report and the Q&A: what we tried, the exact command, what we saw, and what we decided.

## Rules
- Newest entry at the top. One entry per experiment, a few lines each.
- Always give the **command** so anyone can rerun it, and the **data/snapshot** used.
- Write negative results too (what did not work and why): the handout values them.
- Put raw outputs (CSV) in `results/`, not here; link to them.
- Report measurements (timings, scaling) only from cluster batch jobs, with the Slurm
  job ID and node. Laptop or container numbers are fine for quick checks but say so.

## Entry template
```markdown
### YYYY-MM-DD: <what you tested, in a few words>
- **Question:** what did you want to find out?
- **Setup:** data, snapshot, version, number of seasons/workers, where it ran (cluster job ID + node, or laptop)
- **Command:** `python -m ...`
- **Result:** the key numbers (small table if useful) and a link to the CSV in `results/`
- **Conclusion:** what we decided and why
```
