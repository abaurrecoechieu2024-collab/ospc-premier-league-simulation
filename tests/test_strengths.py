import pandas as pd
import pytest

from src.strengths import fit_strengths, promotion_factors

AS_OF = pd.Timestamp("2026-11-14")


def rows(div, season, results):
    return [{"div": div, "date": pd.Timestamp(f"{season}-09-01"), "home": h, "away": a,
             "home_goals": hg, "away_goals": ag, "season": season} for h, a, hg, ag in results]


def table(*parts):
    return pd.DataFrame([r for part in parts for r in part])


# A current season (2026) that only involves X and Y, so "fit" sees them.
CURRENT = rows("E0", 2026, [("X", "Y", 1, 1)])


def test_team_without_data_is_average():
    matches = table(CURRENT, rows("E0", 2025, [("X", "Y", 2, 1), ("Y", "X", 1, 1)]))
    model = fit_strengths(matches, ["X", "Y", "NEW"], AS_OF)
    assert model["strength"]["NEW"] == pytest.approx(
        {"home_attack": 1, "home_defence": 1, "away_attack": 1, "away_defence": 1})


def test_recent_seasons_count_more():
    # X scored 4 at home two seasons ago and 0 last season.
    # Y always scores 1 at home, so the league average is not just X.
    old_and_new = table(CURRENT, rows("E0", 2024, [("X", "Y", 4, 0), ("Y", "X", 1, 1)]),
                        rows("E0", 2025, [("X", "Y", 0, 0), ("Y", "X", 1, 1)]))
    equal = fit_strengths(old_and_new, ["X", "Y"], AS_OF, decay=1.0)["strength"]["X"]["home_attack"]
    recent = fit_strengths(old_and_new, ["X", "Y"], AS_OF, decay=0.25)["strength"]["X"]["home_attack"]
    assert recent < equal


def test_promotion_factors():
    # P scored 2 and conceded 1 per game in the Championship,
    # then 1 and 2 per game after promotion: factors 0.5 and 2.0.
    matches = table(rows("E1", 2024, [("P", "Q", 2, 1), ("Q", "P", 1, 2)]),
                    rows("E0", 2025, [("P", "R", 1, 2), ("R", "P", 2, 1)]))
    assert promotion_factors(matches, [2025]) == pytest.approx((0.5, 2.0))
    assert promotion_factors(matches, [2026]) is None
    assert promotion_factors(matches, [2025, 2024]) == pytest.approx((0.5, 2.0))  # 2024 skipped


def test_promotion_factors_pool_teams_over_seasons():
    # S: 2 -> 1 goals per game (0.5); T: 1 -> 1 goals per game (1.0).
    # Pooled over both teams: 3 goals -> 2 goals per 2 games = 2/3, not the average of the ratios.
    matches = table(rows("E1", 2023, [("T", "U", 1, 1)]), rows("E0", 2024, [("T", "V", 1, 1)]),
                    rows("E1", 2024, [("S", "W", 2, 1)]), rows("E0", 2025, [("S", "V", 1, 1)]))
    attack, defence = promotion_factors(matches, [2025, 2024])
    assert attack == pytest.approx(2 / 3) and defence == pytest.approx(1.0)


def test_championship_goals_are_scaled_for_promoted_teams():
    base = [CURRENT,
            rows("E1", 2024, [("P", "Q", 2, 1), ("Q", "P", 1, 2)]),     # calibration: factors 0.5, 2.0
            rows("E0", 2025, [("P", "R", 1, 2), ("R", "P", 2, 1), ("X", "Y", 1, 1), ("Y", "X", 1, 1)])]
    matches = table(*base, rows("E1", 2025, [("NEW", "Z", 6, 0)]))     # promoted team scored 6
    s = fit_strengths(matches, ["X", "Y", "NEW"], AS_OF, decay=0.5, championship=True)["strength"]["NEW"]
    # Weights: current season 1, last season 0.5. League home average:
    mean_home = (1 * 1 + 0.5 * (1 + 2 + 1 + 1)) / (1 + 0.5 * 4)
    # NEW: one home game, weight 0.5, its 6 goals scaled by 0.5, plus 5 imaginary average games
    expected = (0.5 * 6 * 0.5 + 5 * mean_home) / (0.5 + 5) / mean_home
    assert s["home_attack"] == pytest.approx(expected)


def test_championship_is_off_by_default():
    base = [CURRENT,
            rows("E1", 2024, [("P", "Q", 2, 1), ("Q", "P", 1, 2)]),
            rows("E0", 2025, [("P", "R", 1, 2), ("R", "P", 2, 1), ("X", "Y", 1, 1), ("Y", "X", 1, 1)])]
    model = fit_strengths(table(*base, rows("E1", 2025, [("NEW", "Z", 6, 0)])), ["X", "Y", "NEW"], AS_OF)
    assert model["promotion_factors"] is None
    assert model["strength"]["NEW"]["home_attack"] == pytest.approx(1.0)   # no data -> average


def test_invalid_parameters():
    with pytest.raises(ValueError):
        fit_strengths(table(CURRENT), ["X", "Y"], AS_OF, decay=0)
