"""Base strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    """Abstract long-only strategy producing target exposure signals.

    A signal of 1 means fully invested according to the backtest's position-size
    setting; 0 means cash. Signals are observed at the close and executed on the
    next bar.
    """

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Return a Series indexed like ``data`` containing target values 0 or 1."""

    def signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate and validate a signal stream."""
        result = self.generate_signals(data)
        if not isinstance(result, pd.Series):
            raise TypeError("generate_signals must return a pandas Series")
        result = result.reindex(data.index).fillna(0).astype(float)
        invalid = ~result.isin([0.0, 1.0])
        if invalid.any():
            raise ValueError("Long-only strategy signals must contain only 0 and 1")
        return result.rename("signal")
