"""
Backtest module for Vero Algo SDK.

Provides historical simulation engine and performance reporting.
"""

from .engine import BacktestEngine, BacktestResult
from .metrics import calculate_metrics
from .report import PerformanceReport
from .settings import BacktestSettings, DatePreset, Timeframe

__all__ = [
    "BacktestEngine",
    "BacktestResult",
    "calculate_metrics",
    "PerformanceReport",
    "BacktestSettings",
    "DatePreset",
    "Timeframe",
]
