"""
Backtest settings for strategy configuration.

Provides dataclass for backtest configuration matching the UI.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from ..config import TimeResolution


class DatePreset(str, Enum):
    """Quick date range presets."""
    MONTH_1 = "1M"      # Last 1 month
    MONTH_3 = "3M"      # Last 3 months
    MONTH_6 = "6M"      # Last 6 months
    YEAR_1 = "1Y"       # Last 1 year
    YTD = "YTD"         # Year to date
    ALL = "ALL"         # All available data


class Timeframe(str, Enum):
    """Bar timeframes."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    
    def to_seconds(self) -> int:
        """Convert to seconds."""
        mapping = {
            "1m": TimeResolution.MINUTE_1,
            "5m": TimeResolution.MINUTE_5,
            "15m": TimeResolution.MINUTE_15,
            "30m": TimeResolution.MINUTE_30,
            "1h": TimeResolution.HOUR_1,
            "4h": TimeResolution.HOUR_4,
            "1d": TimeResolution.DAY_1,
        }
        return mapping.get(self.value, TimeResolution.DAY_1)


@dataclass
class BacktestSettings:
    """
    Backtest configuration settings.
    
    Matches the UI configuration panel:
    - Symbol
    - Timeframe
    - From/To Date
    - Initial Capital
    - Quick Presets (1M, 3M, 6M, 1Y, YTD)
    """
    
    # Symbol(s) to backtest
    symbols: List[str] = field(default_factory=list)
    
    # Timeframe / Resolution
    timeframe: Timeframe = Timeframe.DAY_1
    
    # Date range
    from_date: Optional[str] = None  # YYYY-MM-DD format
    to_date: Optional[str] = None    # YYYY-MM-DD format
    
    # Capital settings
    initial_capital: float = 100000.0
    max_nav_usage_pct: float = 100.0  # Max % of NAV to use
    
    # Execution simulation
    commission_pct: float = 0.1       # Commission as % of trade value
    slippage_ticks: int = 1           # Slippage in ticks
    fill_ratio: float = 1.0           # % of order filled (1.0 = 100%)
    
    # Data settings
    use_adjusted_prices: bool = True  # Use adjusted prices for splits/dividends
    warmup_bars: int = 100            # Bars to load before start for indicators
    
    # Report settings
    benchmark_symbol: str = ""         # Symbol to compare against (for alpha/beta)
    risk_free_rate: float = 0.02       # Annual risk-free rate (for Sharpe)
    
    def __post_init__(self):
        """Set default dates if not provided."""
        if not self.to_date:
            self.to_date = datetime.now().strftime("%Y-%m-%d")
        
        if not self.from_date:
            # Default to 1 year ago
            one_year_ago = datetime.now() - timedelta(days=365)
            self.from_date = one_year_ago.strftime("%Y-%m-%d")
    
    @property
    def resolution(self) -> int:
        """Get resolution in seconds."""
        return self.timeframe.to_seconds()
    
    @classmethod
    def from_preset(
        cls,
        symbols: List[str],
        preset: DatePreset = DatePreset.YEAR_1,
        initial_capital: float = 100000,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> "BacktestSettings":
        """
        Create settings from a preset.
        
        Args:
            symbols: Symbols to backtest
            preset: Date range preset
            initial_capital: Starting capital
            timeframe: Bar timeframe
        """
        now = datetime.now()
        to_date = now.strftime("%Y-%m-%d")
        
        if preset == DatePreset.MONTH_1:
            from_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        elif preset == DatePreset.MONTH_3:
            from_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
        elif preset == DatePreset.MONTH_6:
            from_date = (now - timedelta(days=180)).strftime("%Y-%m-%d")
        elif preset == DatePreset.YEAR_1:
            from_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
        elif preset == DatePreset.YTD:
            from_date = f"{now.year}-01-01"
        else:  # ALL
            from_date = "2020-01-01"  # Default historical start
        
        return cls(
            symbols=symbols,
            timeframe=timeframe,
            from_date=from_date,
            to_date=to_date,
            initial_capital=initial_capital,
        )
    
    @classmethod
    def quick_1m(cls, symbols: List[str], capital: float = 100000, timeframe: Timeframe = Timeframe.DAY_1) -> "BacktestSettings":
        """Last 1 month preset."""
        return cls.from_preset(symbols, DatePreset.MONTH_1, capital, timeframe)
    
    @classmethod
    def quick_3m(cls, symbols: List[str], capital: float = 100000, timeframe: Timeframe = Timeframe.DAY_1) -> "BacktestSettings":
        """Last 3 months preset."""
        return cls.from_preset(symbols, DatePreset.MONTH_3, capital, timeframe)
    
    @classmethod
    def quick_6m(cls, symbols: List[str], capital: float = 100000, timeframe: Timeframe = Timeframe.DAY_1) -> "BacktestSettings":
        """Last 6 months preset."""
        return cls.from_preset(symbols, DatePreset.MONTH_6, capital, timeframe)
    
    @classmethod
    def quick_1y(cls, symbols: List[str], capital: float = 100000, timeframe: Timeframe = Timeframe.DAY_1) -> "BacktestSettings":
        """Last 1 year preset."""
        return cls.from_preset(symbols, DatePreset.YEAR_1, capital, timeframe)
    
    @classmethod
    def quick_ytd(cls, symbols: List[str], capital: float = 100000, timeframe: Timeframe = Timeframe.DAY_1) -> "BacktestSettings":
        """Year to date preset."""
        return cls.from_preset(symbols, DatePreset.YTD, capital, timeframe)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "symbols": self.symbols,
            "timeframe": self.timeframe.value,
            "from_date": self.from_date,
            "to_date": self.to_date,
            "initial_capital": self.initial_capital,
            "max_nav_usage_pct": self.max_nav_usage_pct,
            "commission_pct": self.commission_pct,
            "slippage_ticks": self.slippage_ticks,
            "warmup_bars": self.warmup_bars,
        }
