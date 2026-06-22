"""Minimal custom strategy example."""

import pandas as pd

from argmax import Backtest
from argmax.data import get_data
from argmax.indicators import EMA
from argmax.strategies import Strategy


class PriceAboveEMA(Strategy):
    """Hold the asset while its close is above a trailing EMA."""

    def __init__(self, period: int = 50) -> None:
        self.period = period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        return (data["Close"] > EMA(data["Close"], self.period)).astype(float)


if __name__ == "__main__":
    history = get_data("SPY", start="2020-01-01", end="2025-01-01")
    outcome = Backtest(PriceAboveEMA(50), history).run()
    print(outcome.summary())
