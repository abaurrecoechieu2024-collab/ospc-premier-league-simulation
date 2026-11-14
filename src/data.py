"""Load the football-data.co.uk CSV files into one pandas table.

File names follow the source: E0 = Premier League, E1 = Championship,
then the season, e.g. E0_2526.csv is the Premier League 2025/26.
"""
from pathlib import Path

import pandas as pd

COLUMNS = ["Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"]
NAMES = {"Div": "div", "Date": "date", "HomeTeam": "home", "AwayTeam": "away",
         "FTHG": "home_goals", "FTAG": "away_goals"}


def season_of(path):
    """E0_2526.csv -> 2025 (the year the season starts)."""
    return 2000 + int(Path(path).stem.split("_")[1][:2])


def load_matches(path):
    """Read one file, keeping only the six columns we use."""
    df = pd.read_csv(path, usecols=COLUMNS, encoding="utf-8-sig")
    df = df.dropna(how="all").rename(columns=NAMES)      # empty lines at the end
    if df.isna().any().any():
        raise ValueError(f"{path}: missing values in a played match")
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, format="mixed")
    df["home_goals"] = df["home_goals"].astype(int)
    df["away_goals"] = df["away_goals"].astype(int)
    df["season"] = season = season_of(path)
    start, end = pd.Timestamp(f"{season}-07-01"), pd.Timestamp(f"{season + 1}-06-30")
    if not df["date"].between(start, end).all():         # e.g. the wrong season's E0.csv
        raise ValueError(f"{path}: dates {df['date'].min().date()} to {df['date'].max().date()} "
                         f"are not in season {season}/{(season + 1) % 100:02d}; wrong file?")
    if df.duplicated(["home", "away"]).any():
        raise ValueError(f"{path}: the same home/away match appears twice")
    return df


def load_all(data_dir="data/raw"):
    """One table with every match: div, date, home, away, goals, season."""
    paths = sorted(Path(data_dir).glob("E[01]_*.csv"))
    if not paths:
        raise ValueError(f"No E0_/E1_ CSV files in {data_dir}")
    return pd.concat([load_matches(p) for p in paths], ignore_index=True)
