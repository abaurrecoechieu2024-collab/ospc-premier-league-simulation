import pandas as pd
import pytest

from src.data import load_all, load_matches
from src.fixtures import current_matches, current_standings, remaining_fixtures, team_list

HEADER = "﻿Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"


def test_load_matches_reads_six_columns(tmp_path):
    path = tmp_path / "E0_2526.csv"
    path.write_text(HEADER + "E0,15/08/2025,20:00,A,B,2,1,H\nE0,16/08/25,15:00,B,A,0,0,D\n,,,,,,,\n",
                    encoding="utf-8")
    df = load_matches(path)
    assert list(df["home"]) == ["A", "B"]
    assert list(df["home_goals"]) == [2, 0]
    assert df["date"].dt.year.tolist() == [2025, 2025]      # both date formats
    assert set(df["season"]) == {2025}


@pytest.mark.parametrize("bad", ["E0,15/08/2025,20:00,A,B,,1,H\n",
                                 "E0,15/08/2025,20:00,A,B,1,0,H\nE0,16/08/2025,20:00,A,B,1,0,H\n"])
def test_load_matches_rejects_bad_rows(tmp_path, bad):
    path = tmp_path / "E0_2526.csv"
    path.write_text(HEADER + bad, encoding="utf-8")
    with pytest.raises(ValueError):
        load_matches(path)


def test_load_all_needs_files(tmp_path):
    with pytest.raises(ValueError):
        load_all(tmp_path)


def make_current(results, season=2026):
    rows = [{"div": "E0", "date": pd.Timestamp(d), "home": h, "away": a,
             "home_goals": hg, "away_goals": ag, "season": season}
            for d, h, a, hg, ag in results]
    return pd.DataFrame(rows)


TEAMS = [f"T{i:02d}" for i in range(20)]


def test_standings_fixtures_and_cutoff():
    # every team plays once so all 20 appear; one match after the cutoff
    results = [("2026-08-20", TEAMS[i], TEAMS[i + 1], 2, 1) for i in range(0, 20, 2)]
    results.append(("2026-12-01", TEAMS[1], TEAMS[0], 5, 0))
    current = current_matches(make_current(results), pd.Timestamp("2026-11-14"))
    teams = team_list(current)
    table = current_standings(current, teams)
    assert table[0] == [3, 2, 1] and table[1] == [0, 1, 2]
    fixtures = remaining_fixtures(current, teams)
    assert len(fixtures) == 380 - 10
    assert (0, 1) not in fixtures and (1, 0) in fixtures   # the later match is still to play


def test_load_matches_rejects_a_file_from_another_season(tmp_path):
    path = tmp_path / "E0_2425.csv"                       # name says 2024/25 ...
    path.write_text(HEADER + "E0,15/08/2025,20:00,A,B,2,1,H\n", encoding="utf-8")  # ... data is 2025/26
    with pytest.raises(ValueError, match="wrong file"):
        load_matches(path)
