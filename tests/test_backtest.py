import pandas as pd

from src.backtest import model_data, score


def test_perfect_prediction_scores_zero():
    # 4 teams, every simulated season ends exactly as the real one: A, B, C, D
    counts = [[10, 0, 0, 0], [0, 10, 0, 0], [0, 0, 10, 0], [0, 0, 0, 10]]
    s = score(counts, [1, 2, 3, 4], 10)
    assert s["position_error"] == 0 and s["brier_title"] == 0 and s["brier_relegation"] == 0
    assert s["p_real_champion"] == 1


def test_wrong_prediction_is_penalised():
    # the model is sure A wins, but B won
    counts = [[10, 0, 0, 0], [0, 10, 0, 0], [0, 0, 10, 0], [0, 0, 0, 10]]
    s = score(counts, [2, 1, 3, 4], 10)
    assert s["position_error"] == 0.5          # A and B each one place off, over 4 teams
    assert s["brier_title"] == 0.5             # (1-0)^2 + (0-1)^2 over 4 teams
    assert s["p_real_champion"] == 0


def test_models_use_the_right_data():
    rows = [(div, season) for div in ("E0", "E1") for season in (2022, 2023, 2024, 2025)]
    matches = pd.DataFrame(rows, columns=["div", "season"])
    simple = model_data(matches, 2024, "simple")
    assert set(simple["div"]) == {"E0"} and set(simple["season"]) == {2023, 2024}
    multi = model_data(matches, 2024, "multi")
    assert set(multi["div"]) == {"E0"} and set(multi["season"]) == {2022, 2023, 2024}
    full = model_data(matches, 2024, "full")
    assert set(full["div"]) == {"E0", "E1"} and full["season"].max() == 2024   # never the future
