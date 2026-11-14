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

## Files used (names must follow `E0_YYYY.csv` / `E1_YYYY.csv`)
Download from https://www.football-data.co.uk/englandm.php (E0 = Premier League, E1 = Championship) and save in `raw/` with these names:

| File | Season | Used for |
|---|---|---|
| `E0_2627.csv` | Premier League 2026/27 | Current table + remaining fixtures (frozen at 14 Nov 2026) |
| `E0_2526.csv` | Premier League 2025/26 | Strengths (weight 0.5); backtest |
| `E0_2425.csv` | Premier League 2024/25 | Strengths (weight 0.25); backtest |
| `E0_2324.csv` | Premier League 2023/24 | Strengths (weight 0.125); backtest |
| `E1_2223.csv` … `E1_2526.csv` | Championship 2022/23–2025/26 | Only with `--championship` and in the backtest's `full` model |

Every `E0_*`/`E1_*` file in `raw/` is loaded automatically. After adding a file, record its URL, download date and SHA-256 in `snapshot_manifest.json`. Never re-download `E0_2627.csv` for timing runs: the snapshot must stay frozen. Only date, teams and full-time goals are used.
