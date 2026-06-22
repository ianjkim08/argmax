"""Backtest plotting helpers."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import dates as mdates
from matplotlib.axes import Axes

from argmax.backtest import BacktestResult


def _axes(ax: Axes | None, figsize: tuple[float, float] = (10, 5)) -> Axes:
    if ax is not None:
        return ax
    _, created = plt.subplots(figsize=figsize)
    return created


def plot_equity(result: BacktestResult, ax: Axes | None = None) -> Axes:
    """Plot portfolio equity."""
    target = _axes(ax)
    result.equity.plot(ax=target, color="navy", linewidth=1.6)
    target.set(title="Equity Curve", xlabel="Date", ylabel="Equity")
    target.grid(alpha=0.25)
    return target


def plot_drawdown(result: BacktestResult, ax: Axes | None = None) -> Axes:
    """Plot drawdown as a percentage below the high-water mark."""
    target = _axes(ax)
    values = result.drawdown * 100
    target.fill_between(values.index, values.to_numpy(), 0, color="firebrick", alpha=0.35)
    target.set(title="Drawdown", xlabel="Date", ylabel="Drawdown (%)")
    target.grid(alpha=0.25)
    return target


def plot_trades(result: BacktestResult, ax: Axes | None = None) -> Axes:
    """Plot close prices with entry and exit markers."""
    target = _axes(ax)
    result.data["Close"].plot(ax=target, color="slategray", linewidth=1.2, label="Close")
    if not result.trades.empty:
        target.scatter(
            mdates.date2num(result.trades["entry_date"].to_numpy()),
            result.trades["entry_price"],
            marker="^",
            color="green",
            s=55,
            label="Entry",
            zorder=3,
        )
        target.scatter(
            mdates.date2num(result.trades["exit_date"].to_numpy()),
            result.trades["exit_price"],
            marker="v",
            color="red",
            s=55,
            label="Exit",
            zorder=3,
        )
    target.set(title="Trades", xlabel="Date", ylabel="Price")
    target.legend()
    target.grid(alpha=0.25)
    return target


def plot_rolling_sharpe(result: BacktestResult, window: int = 63, ax: Axes | None = None) -> Axes:
    """Plot annualized rolling Sharpe ratio using zero risk-free return."""
    if window <= 1:
        raise ValueError("window must be greater than one")
    target = _axes(ax)
    returns = result.returns
    rolling = (returns.rolling(window).mean() / returns.rolling(window).std(ddof=1)) * np.sqrt(252)
    rolling.plot(ax=target, color="darkorange", linewidth=1.4)
    target.axhline(0, color="black", linewidth=0.8)
    target.set(title=f"Rolling Sharpe ({window} sessions)", xlabel="Date", ylabel="Sharpe")
    target.grid(alpha=0.25)
    return target
