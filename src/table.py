"""League-table rules shared by every version.

A table is a list with one row per team: [points, goals for, goals against].
"""


def update_table(table, home, away, home_goals, away_goals):
    """Add one match result to the table (3 points for a win, 1 for a draw)."""
    table[home][1] += home_goals
    table[home][2] += away_goals
    table[away][1] += away_goals
    table[away][2] += home_goals
    if home_goals > away_goals:
        table[home][0] += 3
    elif away_goals > home_goals:
        table[away][0] += 3
    else:
        table[home][0] += 1
        table[away][0] += 1


def rank_teams(table, tiebreak=None):
    """Team numbers from first to last place.

    Rule (a documented simplification of the official Premier League rules):
    points, then goal difference, then goals scored, then a random draw.
    `tiebreak` holds one random number per team; the higher number wins an
    exact tie. Without it (e.g. to print the current table) ties keep the
    alphabetical order of the team numbers.
    """
    if tiebreak is None:
        tiebreak = [0.0] * len(table)
    return sorted(range(len(table)), key=lambda i: (
        -table[i][0], -(table[i][1] - table[i][2]), -table[i][1], -tiebreak[i]))
