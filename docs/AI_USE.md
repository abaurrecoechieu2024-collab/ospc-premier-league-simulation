# AI assistance record

## 12 November 2026
- Tool: OpenAI Codex.
- Assistance: explained the supplied assignment and feedback; created the repository structure, README, preparation checklist, and documentation templates.
- No simulation implementation, dataset processing, tests, or performance experiments were completed as part of this setup.
- Human review: pending. The group must check the plan against Blackboard updates and course requirements.
- Required syllabus acknowledgment format: not supplied here; obtain it and adapt this record before submission.

Record future AI assistance, verification, and corrections as the project develops.

## 14 November 2026
- Tool: OpenAI Codex.
- Assistance: implemented a sequential simulator, input validation, unit tests, run documentation, and starter Slurm script; downloaded public input snapshots and ran local checks.
- Provisional assumptions are documented in BASELINE_GUIDE.md for human review.
- No parallel implementation or cluster experiment was completed.
- Review the code and results together and adapt this record to the syllabus format.

## 14 November 2026 (2)
- Tool: Claude (Anthropic), used by Theodor-Gabriel David.
- Assistance: reviewed the baseline against the team plan; restructured it into data/fixtures/strengths/simulate/table modules with pandas; one goals array per batch and a seeded random tie-break; 20 × 20 position counts; season weights and Championship conversion for promoted teams; pytest tests; Slurm script using the course environment; docs/BEYOND_THE_COURSE.md.
- Verification: 18 pytest tests passed locally; real-data run of 10,000 seasons checked (probabilities sum to 1 per position).
- To do by the team: review the modelling choices, run the tests and a job on the cluster.
- Later the same day (Claude): pooled promotion factors, backtest script (simple/multi/full models, every matchweek), season-date check for input files, and the final defaults (multi, weight 0.5, Championship off) chosen by the team from the backtest results run locally.

## 17 November 2026 - Task D (Armando Hernandez)
- Tool: OpenAI ChatGPT.
- Assistance: Helped write and debug Python code for performance analysis, calculate speedup, efficiency and Amdahl's serial fraction, create scaling graphs, and improve the written interpretation.
- Prompts: Asked for step-by-step help analyzing Premier League simulation performance, comparing sequential and parallel execution, interpreting profiling results, and correcting the notebook.
- Verification: Checked the results using Slurm job 30371 data, reviewed profiling from job 30261, and verified the notebook outputs.
- Human review: Reviewed the analysis and corrected the explanations based on group feedback.
