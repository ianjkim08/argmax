"""Strategy protocol and built-in strategies."""

from argmax.strategies.base import Strategy
from argmax.strategies.builtin import (
    BollingerReversion,
    MomentumStrategy,
    MovingAverageCross,
    RSIMeanReversion,
)

__all__ = [
    "BollingerReversion",
    "MomentumStrategy",
    "MovingAverageCross",
    "RSIMeanReversion",
    "Strategy",
]
