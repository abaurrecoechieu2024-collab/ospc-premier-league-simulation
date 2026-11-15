# Experiments and measurements: David Hyeon

See `members/README.md` for the rules and the entry template. Newest entry first.

### 2026-11-15: Process-pool correctness tests
- **Question:** Does the process pool produce exactly the sequential baseline's counts for the requested worker counts?
- **Setup:** Synthetic four-team inputs, 53 seasons, batch size 10, seed 42; local Windows machine using Python 3.13 (not a cluster measurement).
- **Command:** `python -m pytest -q`
- **Result:** 30 passed, including exact count equality for 1, 2, and 4 workers. One unrelated deprecation warning came from the installed `anyio` pytest plugin.
- **Conclusion:** Local correctness checks passed. Cluster validation and performance measurements are still pending.
