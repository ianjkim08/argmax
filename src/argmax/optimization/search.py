"""Grid and random parameter optimization."""

from __future__ import annotations

import itertools
import random
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from argmax.backtest import Backtest
from argmax.strategies import Strategy


class GridSearch:
    """Exhaustive strategy parameter search ranked by a performance metric."""

    def __init__(
        self,
        strategy_class: type[Strategy],
        param_grid: Mapping[str, Sequence[Any]],
        *,
        metric: str = "sharpe_ratio",
    ) -> None:
        if not param_grid or any(not values for values in param_grid.values()):
            raise ValueError("param_grid must contain non-empty value sequences")
        self.strategy_class = strategy_class
        self.param_grid = dict(param_grid)
        self.metric = metric
        self.results_: pd.DataFrame | None = None

    def _parameter_sets(self) -> list[dict[str, Any]]:
        names = list(self.param_grid)
        return [
            dict(zip(names, values, strict=True))
            for values in itertools.product(*(self.param_grid[name] for name in names))
        ]

    def run(self, data: pd.DataFrame, **backtest_kwargs: Any) -> pd.DataFrame:
        """Evaluate combinations and return best-first rankings."""
        rows: list[dict[str, Any]] = []
        for parameters in self._parameter_sets():
            strategy = self.strategy_class(**parameters)
            result = Backtest(strategy, data, **backtest_kwargs).run()
            if not hasattr(result.metrics, self.metric):
                raise ValueError(f"Unknown optimization metric: {self.metric}")
            rows.append(
                {
                    **parameters,
                    "score": getattr(result.metrics, self.metric),
                    **result.metrics.to_dict(),
                }
            )
        self.results_ = (
            pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
        )
        self.results_.index.name = "rank"
        self.results_.index += 1
        return self.results_.copy()

    @property
    def best_params(self) -> dict[str, Any]:
        """Best parameter mapping after :meth:`run`."""
        if self.results_ is None:
            raise RuntimeError("Run the optimizer before requesting best_params")
        return {name: self.results_.iloc[0][name] for name in self.param_grid}


class RandomSearch(GridSearch):
    """Reproducible random sampling without replacement from a parameter grid."""

    def __init__(
        self,
        strategy_class: type[Strategy],
        param_grid: Mapping[str, Sequence[Any]],
        n_iter: int = 10,
        *,
        metric: str = "sharpe_ratio",
        random_state: int | None = None,
    ) -> None:
        super().__init__(strategy_class, param_grid, metric=metric)
        if n_iter <= 0:
            raise ValueError("n_iter must be positive")
        self.n_iter = n_iter
        self.random_state = random_state

    def _parameter_sets(self) -> list[dict[str, Any]]:
        combinations = super()._parameter_sets()
        count = min(self.n_iter, len(combinations))
        return random.Random(self.random_state).sample(combinations, count)
