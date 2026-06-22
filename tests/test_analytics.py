from __future__ import annotations

import pandas as pd
import pytest

from argmax.analytics import calculate_metrics, compare_results, drawdown_series
from argmax.backtest import Backtest
from argmax.strategies import MomentumStrategy, MovingAverageCross


def test_performance_metrics_and_trade_statistics() -> None:
    equity = pd.Series([100.0, 110.0, 99.0])
    metrics = calculate_metrics(equity, pd.Series([10.0, -5.0]))
    assert metrics.total_return == pytest.approx(-0.01)
    assert metrics.max_drawdown == pytest.approx(0.10)
    assert metrics.win_rate == pytest.approx(0.5)
    assert metrics.profit_factor == pytest.approx(2.0)
    assert metrics.volatility > 0
    assert drawdown_series(equity).iloc[-1] == pytest.approx(-0.10)


def test_profit_factor_for_no_losses() -> None:
    metrics = calculate_metrics(pd.Series([100.0, 101.0]), pd.Series([5.0]))
    assert metrics.profit_factor == float("inf")


def test_metrics_reject_invalid_equity() -> None:
    with pytest.raises(ValueError, match="positive"):
        calculate_metrics(pd.Series([100.0, 0.0]))


def test_compare_results_and_result_facade(market_data) -> None:
    trend = Backtest(MovingAverageCross(10, 30), market_data).run()
    momentum = Backtest(MomentumStrategy(20), market_data).run()
    comparison = compare_results({"trend": trend, "momentum": momentum})
    assert comparison.index.name == "strategy"
    assert comparison["sharpe_ratio"].is_monotonic_decreasing
    assert trend.summary()["total_return"] == trend.total_return
    assert trend.annualized_return == trend.metrics.annualized_return
    assert trend.volatility == trend.metrics.volatility
    assert trend.sortino_ratio == trend.metrics.sortino_ratio
    assert trend.max_drawdown == trend.metrics.max_drawdown
    assert trend.win_rate == trend.metrics.win_rate
    assert trend.profit_factor == trend.metrics.profit_factor
    assert trend.drawdown.index.equals(trend.equity.index)
    with pytest.raises(ValueError, match="At least one"):
        compare_results({})
