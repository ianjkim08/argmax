"""Bias-aware, next-bar long-only backtesting engine."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from argmax.analytics import calculate_metrics
from argmax.backtest.result import BacktestResult
from argmax.portfolio import Portfolio
from argmax.strategies import Strategy


class Backtest:
    """Run a strategy against a single asset's OHLCV history."""

    def __init__(
        self,
        strategy: Strategy,
        data: pd.DataFrame,
        capital: float = 100_000.0,
        commission: float = 0.001,
        slippage: float = 0.0,
        position_size: float = 1.0,
        *,
        liquidate_at_end: bool = True,
        risk_free_rate: float = 0.0,
    ) -> None:
        required = {"Open", "High", "Low", "Close", "Volume"}
        missing = required.difference(data.columns)
        if missing:
            raise ValueError(f"Backtest data is missing columns: {sorted(missing)}")
        if data.empty:
            raise ValueError("Backtest data cannot be empty")
        if not 0 < position_size <= 1:
            raise ValueError("position_size must be in (0, 1]")
        self.strategy = strategy
        self.data = data.sort_index().copy()
        self.capital = capital
        self.commission = commission
        self.slippage = slippage
        self.position_size = position_size
        self.liquidate_at_end = liquidate_at_end
        self.risk_free_rate = risk_free_rate

    def run(self) -> BacktestResult:
        """Simulate target changes at the next session's open."""
        raw_signals = self.strategy.signals(self.data)
        executable = raw_signals.shift(1).fillna(0.0)
        account = Portfolio(self.capital, self.commission, self.slippage)
        snapshots = []
        previous_target = 0.0
        for date, row in self.data.iterrows():
            target = float(executable.loc[date])
            if target > previous_target and not account.position:
                account.buy(pd.Timestamp(date), float(row["Open"]), self.position_size)
            elif target < previous_target and account.position:
                account.sell(pd.Timestamp(date), float(row["Open"]))
            snapshots.append(account.mark(pd.Timestamp(date), float(row["Close"])))
            previous_target = target

        if self.liquidate_at_end and account.position:
            last_date = pd.Timestamp(self.data.index[-1])
            account.sell(last_date, float(self.data["Close"].iloc[-1]))
            snapshots[-1] = account.mark(last_date, float(self.data["Close"].iloc[-1]))

        portfolio = pd.DataFrame([asdict(item) for item in snapshots]).set_index("date")
        portfolio.index.name = "Date"
        portfolio["returns"] = portfolio["equity"].pct_change().fillna(0.0)
        trades = pd.DataFrame([asdict(trade) for trade in account.trades])
        if trades.empty:
            trades = pd.DataFrame(
                columns=[
                    "entry_date",
                    "entry_price",
                    "shares",
                    "entry_cost",
                    "exit_date",
                    "exit_price",
                    "exit_cost",
                    "pnl",
                    "return_pct",
                ]
            )
        pnls = trades["pnl"] if "pnl" in trades else pd.Series(dtype=float)
        metrics = calculate_metrics(portfolio["equity"], pnls, risk_free_rate=self.risk_free_rate)
        return BacktestResult(portfolio, trades, raw_signals, metrics, self.data.copy())
