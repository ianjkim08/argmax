"""Standard backtest performance metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from argmax.backtest.result import BacktestResult


@dataclass(frozen=True, slots=True)
class Metrics:
    """Annualized return and realized-trade statistics."""

    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float

    def to_dict(self) -> dict[str, float]:
        """Return metric names and values."""
        return asdict(self)


def drawdown_series(equity: pd.Series) -> pd.Series:
    """Return percentage drawdown from the running high-water mark."""
    values = equity.astype(float)
    return (values / values.cummax() - 1.0).rename("drawdown")


def calculate_metrics(
    equity: pd.Series,
    trade_pnls: pd.Series | None = None,
    *,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> Metrics:
    """Calculate performance metrics from an equity curve and realized P&Ls."""
    clean = equity.astype(float).dropna()
    if clean.empty or (clean <= 0).any():
        raise ValueError("equity must contain positive values")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    returns = clean.pct_change().dropna()
    total = clean.iloc[-1] / clean.iloc[0] - 1.0
    years = max(len(returns) / periods_per_year, 1 / periods_per_year)
    annualized = (clean.iloc[-1] / clean.iloc[0]) ** (1 / years) - 1.0
    volatility = float(returns.std(ddof=1) * np.sqrt(periods_per_year)) if len(returns) > 1 else 0.0
    daily_rf = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
    excess = returns - daily_rf
    excess_std = excess.std(ddof=1)
    sharpe = (
        float(excess.mean() / excess_std * np.sqrt(periods_per_year))
        if len(excess) > 1 and excess_std > 0
        else 0.0
    )
    downside = excess[excess < 0]
    downside_deviation = float(np.sqrt((downside**2).mean())) if not downside.empty else 0.0
    sortino = (
        float(excess.mean() / downside_deviation * np.sqrt(periods_per_year))
        if downside_deviation > 0
        else 0.0
    )
    maximum_drawdown = abs(float(drawdown_series(clean).min()))

    pnls = pd.Series(dtype=float) if trade_pnls is None else trade_pnls.dropna().astype(float)
    win_rate = float((pnls > 0).mean()) if not pnls.empty else 0.0
    gross_profit = float(pnls[pnls > 0].sum())
    gross_loss = abs(float(pnls[pnls < 0].sum()))
    profit_factor = (
        gross_profit / gross_loss if gross_loss else (float("inf") if gross_profit else 0.0)
    )
    return Metrics(
        total_return=float(total),
        annualized_return=float(annualized),
        volatility=volatility,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        max_drawdown=maximum_drawdown,
        win_rate=win_rate,
        profit_factor=profit_factor,
    )


def compare_results(results: dict[str, BacktestResult]) -> pd.DataFrame:
    """Compare named backtests in a metric table sorted by Sharpe ratio."""
    if not results:
        raise ValueError("At least one backtest result is required")
    comparison = pd.DataFrame(
        {name: result.metrics.to_dict() for name, result in results.items()}
    ).T
    comparison.index.name = "strategy"
    return comparison.sort_values("sharpe_ratio", ascending=False)
