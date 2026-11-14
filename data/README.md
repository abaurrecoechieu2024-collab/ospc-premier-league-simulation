# Data

Source: https://www.football-data.co.uk/englandm.php
Use the Premier League links. Exact seasons are pending group agreement.

Before adding data, record:
- Season and exact download URL.
- Download date and snapshot cutoff.
- Filename, row count, relevant columns, and any cleaning.
- Handling of missing values, team names, and promoted teams.
- Source or construction of the remaining fixtures, if used.
- Applicable source attribution and reuse conditions.

Retain original inputs unchanged and document transformations. Small agreed CSVs may be committed; keep large datasets out of Git. Do not commit credentials or personal data.

## Provisional baseline snapshot
The original 2025/26 (380 rows) and 2026/27 (100 rows) Premier League files are saved in `raw/`. See `snapshot_manifest.json` for source URLs, retrieval date, and SHA-256 hashes. The current snapshot ends on 8 November 2026. These seasons are a starting choice for review, not a recorded group decision. Only match dates, teams and full-time scores are used; betting odds are unused.
