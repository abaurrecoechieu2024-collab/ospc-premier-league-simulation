import pytest

from src.backtest import score
from src.naive_baselines import certain


def test_uniform_relegation_score():
    # every team has 3/20 relegation chance: (0.85^2 x 3 + 0.15^2 x 17) / 20 = 0.1275
    uniform = [[1] * 20 for _ in range(20)]
    assert score(uniform, list(range(1, 21)), 20)["brier_relegation"] == pytest.approx(0.1275)


def test_certain_forecast():
    assert certain([2, 0, 1]) == [[0, 1, 0], [0, 0, 1], [1, 0, 0]]
