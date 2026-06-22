from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from argmax.indicators import ATR, EMA, MACD, RSI, SMA, BollingerBands


def test_sma_and_ema_are_aligned_series() -> None:
    values = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    sma = SMA(values, 3)
    ema = EMA(values, 3)
    assert isinstance(sma, pd.Series)
    assert sma.iloc[-1] == pytest.approx(4.0)
    assert sma.iloc[:2].isna().all()
    assert ema.index.equals(values.index)
    assert ema.iloc[:2].isna().all()


def test_rsi_handles_one_way_and_flat_markets() -> None:
    rising = pd.Series(np.arange(30, dtype=float))
    flat = pd.Series(np.ones(30))
    assert RSI(rising, 14).iloc[-1] == pytest.approx(100.0)
    assert RSI(flat, 14).iloc[-1] == pytest.approx(50.0)


def test_macd_and_bollinger_components_are_series() -> None:
    values = pd.Series(np.linspace(10, 40, 80))
    output = MACD(values)
    bands = BollingerBands(values, period=20, std_dev=2)
    assert all(isinstance(component, pd.Series) for component in output)
    assert all(isinstance(component, pd.Series) for component in bands)
    assert (bands.upper.dropna() > bands.middle.dropna()).all()
    assert (bands.middle.dropna() > bands.lower.dropna()).all()
    assert output.histogram.name == "MACD_histogram"


def test_atr_for_constant_daily_range() -> None:
    close = pd.Series(np.full(30, 10.0))
    data = pd.DataFrame({"High": close + 1, "Low": close - 1, "Close": close})
    assert ATR(data, period=14).iloc[-1] == pytest.approx(2.0)


@pytest.mark.parametrize("function", [SMA, EMA, RSI])
def test_indicators_reject_nonpositive_period(function) -> None:
    with pytest.raises(ValueError, match="positive"):
        function(pd.Series([1.0]), 0)
