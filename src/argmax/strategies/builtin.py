"""Reference strategy implementations."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from argmax.indicators import RSI, SMA, BollingerBands
from argmax.strategies.base import Strategy


def _close(data: pd.DataFrame) -> pd.Series:
    if "Close" not in data:
        raise ValueError("Strategy data requires a Close column")
    return data["Close"].astype(float)


@dataclass(frozen=True, slots=True)
class MovingAverageCross(Strategy):
    """Invest while the fast simple moving average is above the slow average."""

    fast: int = 20
    slow: int = 100

    def __post_init__(self) -> None:
        if self.fast <= 0 or self.slow <= 0 or self.fast >= self.slow:
            raise ValueError("Require 0 < fast < slow")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        close = _close(data)
        ready = SMA(close, self.slow).notna()
        return ((SMA(close, self.fast) > SMA(close, self.slow)) & ready).astype(float)


@dataclass(frozen=True, slots=True)
class RSIMeanReversion(Strategy):
    """Buy oversold RSI and exit when it recovers above the exit threshold."""

    period: int = 14
    oversold: float = 30.0
    exit_level: float = 50.0

    def __post_init__(self) -> None:
        if self.period <= 0 or not 0 <= self.oversold < self.exit_level <= 100:
            raise ValueError("Require period > 0 and 0 <= oversold < exit_level <= 100")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        indicator = RSI(_close(data), self.period)
        entries = indicator < self.oversold
        exits = indicator > self.exit_level
        state = pd.Series(float("nan"), index=data.index)
        state.loc[entries] = 1.0
        state.loc[exits] = 0.0
        return state.ffill().fillna(0.0)


@dataclass(frozen=True, slots=True)
class BollingerReversion(Strategy):
    """Buy below the lower band and exit on a return to the middle band."""

    period: int = 20
    std_dev: float = 2.0

    def __post_init__(self) -> None:
        if self.period <= 0 or self.std_dev <= 0:
            raise ValueError("period and std_dev must be positive")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        close = _close(data)
        bands = BollingerBands(close, self.period, self.std_dev)
        state = pd.Series(float("nan"), index=data.index)
        state.loc[close < bands.lower] = 1.0
        state.loc[close >= bands.middle] = 0.0
        return state.ffill().fillna(0.0)


@dataclass(frozen=True, slots=True)
class MomentumStrategy(Strategy):
    """Invest when trailing price momentum is positive."""

    lookback: int = 126
    threshold: float = 0.0

    def __post_init__(self) -> None:
        if self.lookback <= 0:
            raise ValueError("lookback must be positive")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        momentum = _close(data).pct_change(self.lookback)
        return (momentum > self.threshold).astype(float)
