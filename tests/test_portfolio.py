from __future__ import annotations

import pandas as pd
import pytest

from argmax.portfolio import Portfolio


def test_round_trip_cash_accounting_includes_costs_and_slippage() -> None:
    portfolio = Portfolio(capital=1_000, commission=0.01, slippage=0.01)
    entry = pd.Timestamp("2024-01-02")
    exit_date = pd.Timestamp("2024-01-03")
    assert portfolio.buy(entry, price=100) == 9
    assert portfolio.cash == pytest.approx(81.91)
    snapshot = portfolio.mark(entry, close=105)
    assert snapshot.holdings == pytest.approx(945)
    assert snapshot.equity == pytest.approx(1_026.91)
    assert portfolio.sell(exit_date, price=110) == 9
    assert portfolio.cash == pytest.approx(1_052.209)
    assert portfolio.trades[0].pnl == pytest.approx(52.209)
    assert portfolio.position == 0


def test_portfolio_ignores_duplicate_orders() -> None:
    portfolio = Portfolio(1_000)
    date = pd.Timestamp("2024-01-02")
    portfolio.buy(date, 100)
    assert portfolio.buy(date, 100) == 0
    portfolio.sell(date, 100)
    assert portfolio.sell(date, 100) == 0


@pytest.mark.parametrize(
    "kwargs",
    [{"capital": 0}, {"capital": 100, "commission": -0.1}, {"capital": 100, "slippage": -0.1}],
)
def test_invalid_portfolio_configuration(kwargs) -> None:
    with pytest.raises(ValueError):
        Portfolio(**kwargs)
