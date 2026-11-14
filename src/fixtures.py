"""The season we simulate: who plays, the current table, the matches left."""
from .table import update_table


def target_season(matches):
    """The latest Premier League season in the data (the one underway)."""
    return int(matches.loc[matches["div"] == "E0", "season"].max())


def current_matches(matches, as_of):
    """Premier League matches of the target season played up to `as_of`."""
    season = target_season(matches)
    current = matches[(matches["div"] == "E0") & (matches["season"] == season)]
    return current[current["date"] <= as_of]


def team_list(current):
    """The 20 teams, sorted by name; a team's number is its position here."""
    teams = sorted(set(current["home"]) | set(current["away"]))
    if len(teams) != 20:
        raise ValueError(f"Expected 20 teams, found {len(teams)}")
    return teams


def current_standings(current, teams):
    """Points, goals for and goals against of every team so far."""
    number = {team: i for i, team in enumerate(teams)}
    table = [[0, 0, 0] for _ in teams]
    for m in current.itertuples():
        update_table(table, number[m.home], number[m.away], m.home_goals, m.away_goals)
    return table


def remaining_fixtures(current, teams):
    """Every (home, away) pair of a double round robin not yet played."""
    number = {team: i for i, team in enumerate(teams)}
    played = {(number[h], number[a]) for h, a in zip(current["home"], current["away"])}
    return [(h, a) for h in range(len(teams)) for a in range(len(teams))
            if h != a and (h, a) not in played]
