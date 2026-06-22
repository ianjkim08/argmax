"""Technical indicators implemented with pandas."""

from __future__ import annotations

from typing import NamedTuple

import pandas as pd


def _period(value: int) -> int:
    if value <= 0:
        raise ValueError("period must be positive")
    return value


def SMA(series: pd.Series, period: int = 20) -> pd.Series:
    """Simple moving average."""
    result = series.astype(float).rolling(_period(period), min_periods=period).mean()
    return result.rename(f"SMA_{period}")


def EMA(series: pd.Series, period: int = 20) -> pd.Series:
    """Exponential moving average using the standard recursive definition."""
    result = series.astype(float).ewm(span=_period(period), adjust=False, min_periods=period).mean()
    return result.rename(f"EMA_{period}")


def RSI(series: pd.Series, period: int = 14) -> pd.Series:
    """Wilder relative strength index."""
    _period(period)
    delta = series.astype(float).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    relative_strength = avg_gain / avg_loss
    result = 100 - (100 / (1 + relative_strength))
    result = result.mask((avg_gain == 0) & (avg_loss == 0), 50.0)
    result = result.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    return result.rename(f"RSI_{period}")


class MACDOutput(NamedTuple):
    """MACD components; every component is a pandas Series."""

    macd: pd.Series
    signal: pd.Series
    histogram: pd.Series


def MACD(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> MACDOutput:
    """Moving average convergence divergence components."""
    if fast >= slow:
        raise ValueError("fast must be less than slow")
    _period(fast)
    _period(slow)
    _period(signal)
    fast_line = series.astype(float).ewm(span=fast, adjust=False, min_periods=fast).mean()
    slow_line = series.astype(float).ewm(span=slow, adjust=False, min_periods=slow).mean()
    line = (fast_line - slow_line).rename("MACD")
    signal_line = (
        line.ewm(span=signal, adjust=False, min_periods=signal).mean().rename("MACD_signal")
    )
    return MACDOutput(line, signal_line, (line - signal_line).rename("MACD_histogram"))


class BollingerOutput(NamedTuple):
    """Bollinger band components; every component is a pandas Series."""

    middle: pd.Series
    upper: pd.Series
    lower: pd.Series


def BollingerBands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> BollingerOutput:
    """Middle, upper, and lower Bollinger bands."""
    _period(period)
    if std_dev <= 0:
        raise ValueError("std_dev must be positive")
    middle = SMA(series, period).rename("BB_middle")
    rolling_std = series.astype(float).rolling(period, min_periods=period).std(ddof=0)
    return BollingerOutput(
        middle,
        (middle + std_dev * rolling_std).rename("BB_upper"),
        (middle - std_dev * rolling_std).rename("BB_lower"),
    )


def ATR(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder average true range from High, Low, and Close columns."""
    _period(period)
    missing = {"High", "Low", "Close"}.difference(data.columns)
    if missing:
        raise ValueError(f"ATR requires columns: {sorted(missing)}")
    previous_close = data["Close"].shift(1)
    ranges = pd.concat(
        [
            data["High"] - data["Low"],
            (data["High"] - previous_close).abs(),
            (data["Low"] - previous_close).abs(),
        ],
        axis=1,
    )
    true_range = ranges.max(axis=1)
    return (
        true_range.ewm(alpha=1 / period, adjust=False, min_periods=period)
        .mean()
        .rename(f"ATR_{period}")
    )
