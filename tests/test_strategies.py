from __future__ import annotations

import pandas as pd
import pytest

from argmax.strategies import (
    BollingerReversion,
    MomentumStrategy,
    MovingAverageCross,
    RSIMeanReversion,
    Strategy,
)


@pytest.mark.parametrize(
    "strategy",
    [
        MovingAverageCross(fast=10, slow=30),
        RSIMeanReversion(period=7, oversold=40, exit_level=60),
        BollingerReversion(period=10),
        MomentumStrategy(lookback=20),
    ],
)
def test_builtin_strategies_generate_valid_aligned_signals(strategy, market_data) -> None:
    signals = strategy.signals(market_data)
    assert signals.index.equals(market_data.index)
    assert set(signals.unique()).issubset({0.0, 1.0})
    assert signals.name == "signal"


def test_moving_average_cross_enters_uptrend(market_data) -> None:
    signals = MovingAverageCross(fast=10, slow=30).signals(market_data)
    assert signals.iloc[:29].eq(0).all()
    assert signals.iloc[-1] == 1


class InvalidStrategy(Strategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        return pd.Series(2, index=data.index)


def test_strategy_rejects_short_or_levered_targets(market_data) -> None:
    with pytest.raises(ValueError, match="0 and 1"):
        InvalidStrategy().signals(market_data)


@pytest.mark.parametrize(
    ("strategy_type", "kwargs"),
    [
        (MovingAverageCross, {"fast": 20, "slow": 10}),
        (RSIMeanReversion, {"oversold": 70, "exit_level": 50}),
        (BollingerReversion, {"std_dev": 0}),
        (MomentumStrategy, {"lookback": 0}),
    ],
)
def test_strategy_parameters_are_validated(strategy_type, kwargs) -> None:
    with pytest.raises(ValueError):
        strategy_type(**kwargs)
