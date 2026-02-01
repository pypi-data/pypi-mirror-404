"""
Strategy module for Vero Algo SDK.

Provides cTrader-style strategy/robot framework with event-based processing.
"""

from .base import Strategy, RunMode
from .context import TradingContext
from .position import Position, PositionSide
from .symbol import Symbol, Bars, Bar

__all__ = [
    "Strategy",
    "RunMode",
    "TradingContext",
    "Position",
    "PositionSide",
    "Symbol",
    "Bars",
    "Bar",
]
