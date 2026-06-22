"""Long-only portfolio ledger."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class Trade:
    """Completed or open round-trip trade."""

    entry_date: pd.Timestamp
    entry_price: float
    shares: int
    entry_cost: float
    exit_date: pd.Timestamp | None = None
    exit_price: float | None = None
    exit_cost: float = 0.0
    pnl: float | None = None
    return_pct: float | None = None


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """End-of-session account state."""

    date: pd.Timestamp
    cash: float
    position: int
    holdings: float
    equity: float


class Portfolio:
    """A single-asset, integer-share, long-only portfolio."""

    def __init__(self, capital: float, commission: float = 0.0, slippage: float = 0.0) -> None:
        if capital <= 0:
            raise ValueError("capital must be positive")
        if commission < 0 or slippage < 0:
            raise ValueError("commission and slippage cannot be negative")
        self.initial_capital = float(capital)
        self.cash = float(capital)
        self.position = 0
        self.commission = float(commission)
        self.slippage = float(slippage)
        self.trades: list[Trade] = []
        self._open_trade: Trade | None = None

    def buy(self, date: pd.Timestamp, price: float, size: float = 1.0) -> int:
        """Buy integer shares using ``size`` fraction of cash and return quantity."""
        if self.position:
            return 0
        if not 0 < size <= 1:
            raise ValueError("position size must be in (0, 1]")
        fill = float(price) * (1 + self.slippage)
        shares = int((self.cash * size) // (fill * (1 + self.commission)))
        if shares <= 0:
            return 0
        gross = shares * fill
        cost = gross * self.commission
        self.cash -= gross + cost
        self.position = shares
        self._open_trade = Trade(pd.Timestamp(date), fill, shares, cost)
        return shares

    def sell(self, date: pd.Timestamp, price: float) -> int:
        """Liquidate the current position and return quantity sold."""
        if not self.position or self._open_trade is None:
            return 0
        shares = self.position
        fill = float(price) * (1 - self.slippage)
        gross = shares * fill
        cost = gross * self.commission
        self.cash += gross - cost
        opened = self._open_trade
        basis = shares * opened.entry_price + opened.entry_cost
        pnl = gross - cost - basis
        self.trades.append(
            Trade(
                entry_date=opened.entry_date,
                entry_price=opened.entry_price,
                shares=shares,
                entry_cost=opened.entry_cost,
                exit_date=pd.Timestamp(date),
                exit_price=fill,
                exit_cost=cost,
                pnl=pnl,
                return_pct=pnl / basis,
            )
        )
        self.position = 0
        self._open_trade = None
        return shares

    def mark(self, date: pd.Timestamp, close: float) -> PortfolioSnapshot:
        """Mark holdings to market at the session close."""
        holdings = self.position * float(close)
        return PortfolioSnapshot(
            pd.Timestamp(date), self.cash, self.position, holdings, self.cash + holdings
        )

    @property
    def open_trade(self) -> Trade | None:
        """Current incomplete trade, if any."""
        return self._open_trade
