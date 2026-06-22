"""Argmax: research-friendly quantitative strategy backtesting."""

from argmax.backtest import Backtest, BacktestResult
from argmax.strategies import Strategy

__all__ = ["Backtest", "BacktestResult", "Strategy"]
__version__ = "0.2.0"
