from __future__ import annotations

import pandas as pd
import pytest

from argmax.backtest import Backtest
from argmax.strategies import Strategy


class ScheduledStrategy(Strategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        return pd.Series([0, 1, 1, 0], index=data.index, dtype=float)


def test_backtest_executes_signal_on_next_bar_and_liquidates() -> None:
    index = pd.date_range("2024-01-01", periods=4, freq="D")
    data = pd.DataFrame(
        {
            "Open": [10, 20, 30, 40],
            "High": [11, 21, 31, 41],
            "Low": [9, 19, 29, 39],
            "Close": [10, 20, 35, 45],
            "Volume": [100] * 4,
        },
        index=index,
    )
    result = Backtest(ScheduledStrategy(), data, capital=1_000, commission=0).run()
    assert len(result.trades) == 1
    assert result.trades.iloc[0]["entry_date"] == index[2]
    assert result.trades.iloc[0]["entry_price"] == pytest.approx(30)
    assert result.trades.iloc[0]["exit_date"] == index[3]
    assert result.equity.iloc[-1] == pytest.approx(1_495)
    assert result.total_return == pytest.approx(0.495)


def test_backtest_rejects_bad_data(market_data) -> None:
    with pytest.raises(ValueError, match="missing"):
        Backtest(ScheduledStrategy(), market_data.drop(columns="Open"))
