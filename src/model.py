"""Input validation, a simple goals model, and league-table rules."""
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class Match:
    date: date
    home: str
    away: str
    home_goals: int
    away_goals: int


def season_year(day):
    return day.year if day.month >= 7 else day.year - 1


def read_matches(path):
    """Read completed Football-Data rows; never silently drop bad scores."""
    matches, seen = [], set()
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: missing required columns {sorted(required)}")
        for line, row in enumerate(reader, 2):
            if not any(str(v or "").strip() for v in row.values()):
                continue
            try:
                day = None
                for fmt in ("%d/%m/%Y", "%d/%m/%y"):
                    try:
                        day = datetime.strptime(row["Date"].strip(), fmt).date()
                        break
                    except ValueError:
                        pass
                if day is None:
                    raise ValueError("invalid date")
                home, away = row["HomeTeam"].strip(), row["AwayTeam"].strip()
                hg, ag = int(row["FTHG"]), int(row["FTAG"])
                if not home or not away or home == away or min(hg, ag) < 0:
                    raise ValueError("invalid teams or goals")
                if row.get("Div", "E0") != "E0":
                    raise ValueError("expected Premier League division E0")
                expected = "H" if hg > ag else "A" if hg < ag else "D"
                if row.get("FTR", expected) != expected:
                    raise ValueError("FTR disagrees with goals")
                key = (season_year(day), home, away)
                if key in seen:
                    raise ValueError("duplicate home/away fixture in a season")
                seen.add(key)
                matches.append(Match(day, home, away, hg, ag))
            except (ValueError, TypeError, AttributeError, KeyError) as error:
                raise ValueError(f"{path}, row {line}: {error}") from error
    return sorted(matches, key=lambda m: (m.date, m.home, m.away))


def update_table(table, home, away, hg, ag):
    """Each row is [points, goals for, goals against]."""
    table[home][1] += hg
    table[home][2] += ag
    table[away][1] += ag
    table[away][2] += hg
    if hg > ag:
        table[home][0] += 3
    elif ag > hg:
        table[away][0] += 3
    else:
        table[home][0] += 1
        table[away][0] += 1


def ranking(table, teams):
    """Simplified rule: points, goal difference, goals for, then name.

    Name is a reproducible final fallback, NOT the full official PL rule.
    """
    return sorted(range(len(teams)), key=lambda i: (
        -table[i][0], -(table[i][1] - table[i][2]), -table[i][1], teams[i]))


def prepare_season(current, cutoff, expected_teams=20):
    """Infer a double round robin and subtract completed games by cutoff.

    Team membership is taken from the complete supplied target-season file;
    results after cutoff are never used in standings or model fitting.
    """
    if not current or len({season_year(m.date) for m in current}) != 1:
        raise ValueError("Current input must contain matches from exactly one season")
    if season_year(cutoff) != season_year(current[0].date):
        raise ValueError("Cutoff must fall in the target season (July through June)")
    teams = sorted({t for m in current for t in (m.home, m.away)})
    if len(teams) != expected_teams:
        raise ValueError(f"Expected {expected_teams} teams, found {len(teams)}; supply a complete roster's results")
    index = {team: i for i, team in enumerate(teams)}
    played = [m for m in current if m.date <= cutoff]
    table = [[0, 0, 0] for _ in teams]
    completed = set()
    for m in played:
        pair = (index[m.home], index[m.away])
        if pair in completed:
            raise ValueError("Duplicate current-season fixture")
        completed.add(pair)
        update_table(table, *pair, m.home_goals, m.away_goals)
    remaining = [(h, a) for h in range(len(teams)) for a in range(len(teams))
                 if h != a and (h, a) not in completed]
    return teams, played, table, remaining


def fit_rates(training, teams, fixtures, prior_games=5.0):
    """Smoothed home/away scoring and conceding rates; fit once per run."""
    if not training or prior_games <= 0:
        raise ValueError("Need training matches and a positive smoothing prior")
    mean_home = sum(m.home_goals for m in training) / len(training)
    mean_away = sum(m.away_goals for m in training) / len(training)
    if min(mean_home, mean_away) <= 0:
        raise ValueError("Training data must include both home and away goals")
    # [home games, home scored, home conceded, away games, away scored, away conceded]
    stats = {team: [0] * 6 for team in teams}
    for m in training:
        if m.home in stats:
            s = stats[m.home]
            s[0] += 1; s[1] += m.home_goals; s[2] += m.away_goals
        if m.away in stats:
            s = stats[m.away]
            s[3] += 1; s[4] += m.away_goals; s[5] += m.home_goals
    strengths = {}
    for team, (nh, hs, hc, na, aws, ac) in stats.items():
        strengths[team] = (
            (hs + prior_games * mean_home) / (nh + prior_games) / mean_home,
            (hc + prior_games * mean_away) / (nh + prior_games) / mean_away,
            (aws + prior_games * mean_away) / (na + prior_games) / mean_away,
            (ac + prior_games * mean_home) / (na + prior_games) / mean_home,
        )
    rates = []
    for h, a in fixtures:
        home, away = strengths[teams[h]], strengths[teams[a]]
        rates.append((mean_home * home[0] * away[3], mean_away * away[2] * home[1]))
    return rates
