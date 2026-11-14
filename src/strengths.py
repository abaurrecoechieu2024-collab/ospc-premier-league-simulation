"""Estimate each team's attack and defence from past results (runs once, serial).

The model, in words:
- A team's home attack = its home goals per game / the league's home goals per game.
  The same idea gives home defence, away attack and away defence.
- Recent seasons count more: a match from k seasons ago has weight decay**k
  (the current season has weight 1). Default decay = 0.5: last season 0.5,
  two seasons ago 0.25, three seasons ago 0.125 (chosen with the backtest).
- Optional (championship=True, off by default): Championship matches for promoted teams. Their goals are first
  converted to "Premier League goals" with two factors measured on the teams
  promoted in the two previous seasons (how much less they scored and how much
  more they conceded after going up).
- Every team gets `prior_games` imaginary games at the league average, so a team
  with few games is pulled toward average instead of getting an extreme value.
"""
import pandas as pd

from .fixtures import current_matches, target_season


def promotion_factors(matches, seasons):
    """(attack factor, defence factor) pooled over the teams promoted into `seasons`.

    For each season s, promoted teams = Premier League teams of s that played the
    Championship in s - 1. We add up all their goals and games in both leagues
    (e.g. 3 teams x 2 seasons = 6 teams), then divide. Seasons without both
    files are skipped; returns None if no season can be used.
    """
    totals = {"E0": [0, 0, 0], "E1": [0, 0, 0]}          # scored, conceded, games
    for season in seasons:
        pl = matches[(matches["div"] == "E0") & (matches["season"] == season)]
        ch = matches[(matches["div"] == "E1") & (matches["season"] == season - 1)]
        promoted = (set(pl["home"]) | set(pl["away"])) & (set(ch["home"]) | set(ch["away"]))
        for div, df in (("E0", pl), ("E1", ch)):
            t = totals[div]
            for m in df.itertuples():
                if m.home in promoted:
                    t[0] += m.home_goals; t[1] += m.away_goals; t[2] += 1
                if m.away in promoted:
                    t[0] += m.away_goals; t[1] += m.home_goals; t[2] += 1
    if totals["E1"][2] == 0:
        return None
    (pl_s, pl_c, pl_g), (ch_s, ch_c, ch_g) = totals["E0"], totals["E1"]
    return (pl_s / pl_g) / (ch_s / ch_g), (pl_c / pl_g) / (ch_c / ch_g)


def fit_strengths(matches, teams, as_of, decay=0.5, prior_games=5.0, championship=False):
    """Attack and defence per team, plus the league's average goals (home advantage)."""
    if not 0 < decay <= 1 or prior_games <= 0:
        raise ValueError("decay must be in (0, 1] and prior_games positive")
    season = target_season(matches)
    history = matches[matches["season"] < season]
    pl = pd.concat([history[history["div"] == "E0"], current_matches(matches, as_of)])
    ch_matches = history[history["div"] == "E1"]
    # The backtest showed the conversion helps only in the first weeks, so it is off by default.
    factors = promotion_factors(matches, [season - 1, season - 2]) if championship else None

    # League averages from Premier League matches only (weighted).
    weights = decay ** (season - pl["season"])
    mean_home = (weights * pl["home_goals"]).sum() / weights.sum()
    mean_away = (weights * pl["away_goals"]).sum() / weights.sum()

    # Per team: [home games, home scored, home conceded, away games, away scored, away conceded]
    stats = {team: [0.0] * 6 for team in teams}

    def add(m, w, scored_factor=1.0, conceded_factor=1.0):
        if m.home in stats:
            s = stats[m.home]
            s[0] += w
            s[1] += w * m.home_goals * scored_factor
            s[2] += w * m.away_goals * conceded_factor
        if m.away in stats:
            s = stats[m.away]
            s[3] += w
            s[4] += w * m.away_goals * scored_factor
            s[5] += w * m.home_goals * conceded_factor

    for m in pl.itertuples():
        add(m, decay ** (season - m.season))
    if factors is not None:          # without calibration data we skip Championship games
        for m in ch_matches.itertuples():
            add(m, decay ** (season - m.season), *factors)

    def smoothed(goals, games, mean):
        return (goals + prior_games * mean) / (games + prior_games) / mean

    strength = {}
    for team, (nh, hs, hc, na, a_s, ac) in stats.items():
        strength[team] = {
            "home_attack": smoothed(hs, nh, mean_home),
            "home_defence": smoothed(hc, nh, mean_away),   # > 1 means it concedes more than average
            "away_attack": smoothed(a_s, na, mean_away),
            "away_defence": smoothed(ac, na, mean_home),
        }
    return {"mean_home": mean_home, "mean_away": mean_away,
            "strength": strength, "promotion_factors": factors}
