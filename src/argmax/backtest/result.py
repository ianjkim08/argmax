"""Backtest result container."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from argmax.analytics import Metrics, drawdown_series


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Immutable bundle of account history, signals, trades, and metrics."""

    portfolio: pd.DataFrame
    trades: pd.DataFrame
    signals: pd.Series
    metrics: Metrics
    data: pd.DataFrame

    @property
    def equity(self) -> pd.Series:
        return self.portfolio["equity"]

    @property
    def returns(self) -> pd.Series:
        return self.portfolio["returns"]

    @property
    def drawdown(self) -> pd.Series:
        return drawdown_series(self.equity)

    @property
    def total_return(self) -> float:
        return self.metrics.total_return

    @property
    def annualized_return(self) -> float:
        return self.metrics.annualized_return

    @property
    def volatility(self) -> float:
        return self.metrics.volatility

    @property
    def sharpe_ratio(self) -> float:
        return self.metrics.sharpe_ratio

    @property
    def sortino_ratio(self) -> float:
        return self.metrics.sortino_ratio

    @property
    def max_drawdown(self) -> float:
        return self.metrics.max_drawdown

    @property
    def win_rate(self) -> float:
        return self.metrics.win_rate

    @property
    def profit_factor(self) -> float:
        return self.metrics.profit_factor

    def summary(self) -> pd.Series:
        """Return a display-friendly metric Series."""
        return pd.Series(self.metrics.to_dict(), name="value")
