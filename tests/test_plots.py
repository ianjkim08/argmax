from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from argmax.backtest import Backtest
from argmax.plots import plot_drawdown, plot_equity, plot_rolling_sharpe, plot_trades
from argmax.strategies import MovingAverageCross

plt.switch_backend("Agg")


def test_all_plot_helpers_return_populated_axes(market_data) -> None:
    result = Backtest(MovingAverageCross(10, 30), market_data).run()
    figure, axes = plt.subplots(2, 2)
    assert plot_equity(result, axes[0, 0]).get_title() == "Equity Curve"
    assert plot_drawdown(result, axes[0, 1]).get_title() == "Drawdown"
    assert plot_trades(result, axes[1, 0]).get_title() == "Trades"
    assert "Rolling Sharpe" in plot_rolling_sharpe(result, 20, axes[1, 1]).get_title()
    plt.close(figure)


def test_rolling_sharpe_validates_window(market_data) -> None:
    result = Backtest(MovingAverageCross(10, 30), market_data).run()
    with pytest.raises(ValueError, match="greater than one"):
        plot_rolling_sharpe(result, 1)
