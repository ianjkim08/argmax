from __future__ import annotations

import pytest

from argmax.optimization import GridSearch, RandomSearch
from argmax.strategies import MovingAverageCross


def test_grid_search_returns_ranked_results(market_data) -> None:
    search = GridSearch(MovingAverageCross, {"fast": [5, 10], "slow": [30, 50]})
    ranking = search.run(market_data, commission=0)
    assert len(ranking) == 4
    assert ranking["score"].is_monotonic_decreasing
    assert set(search.best_params) == {"fast", "slow"}


def test_random_search_is_reproducible(market_data) -> None:
    kwargs = {
        "strategy_class": MovingAverageCross,
        "param_grid": {"fast": [5, 10], "slow": [30, 50]},
        "n_iter": 2,
        "random_state": 7,
    }
    first = RandomSearch(**kwargs).run(market_data)
    second = RandomSearch(**kwargs).run(market_data)
    assert first[["fast", "slow"]].equals(second[["fast", "slow"]])


def test_best_params_requires_run() -> None:
    search = GridSearch(MovingAverageCross, {"fast": [5], "slow": [30]})
    with pytest.raises(RuntimeError):
        _ = search.best_params
