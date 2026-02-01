"""
Symbol and Bars data wrapper for strategy framework.

Provides easy access to symbol information and historical/live bar data.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


from ..types import Candle, ProductInfo, ProductStat, Depth


@dataclass
class Bar:
    """
    OHLCV bar with additional computed properties.
    
    Extends Candle with convenience methods for strategy logic.
    """
    
    symbol: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @classmethod
    def from_candle(cls, candle: Candle, symbol: str) -> "Bar":
        """Create from Candle type."""
        return cls(
            symbol=symbol,
            time=datetime.fromtimestamp(candle.time / 1000),
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
        )
    
    @property
    def is_bullish(self) -> bool:
        """Check if bar closed higher than open."""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """Check if bar closed lower than open."""
        return self.close < self.open
    
    @property
    def body(self) -> float:
        """Get bar body size (absolute)."""
        return abs(self.close - self.open)
    
    @property
    def range(self) -> float:
        """Get bar range (high - low)."""
        return self.high - self.low
    
    @property
    def upper_wick(self) -> float:
        """Get upper wick size."""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> float:
        """Get lower wick size."""
        return min(self.open, self.close) - self.low
    
    @property
    def mid_price(self) -> float:
        """Get mid price (HL/2)."""
        return (self.high + self.low) / 2
    
    @property
    def typical_price(self) -> float:
        """Get typical price (HLC/3)."""
        return (self.high + self.low + self.close) / 3


class Bars:
    """
    Collection of bars with indexed access.
    
    Provides array-like access to historical bars:
    - bars[0] = current/latest bar
    - bars[-1] = previous bar
    - bars[-2] = bar before previous
    """
    
    def __init__(self, max_bars: int = 1000):
        self._bars: List[Bar] = []
        self._max_bars = max_bars
    
    def __len__(self) -> int:
        return len(self._bars)
    
    def __getitem__(self, index: int) -> Optional[Bar]:
        """
        Get bar by index.
        
        Index 0 = current bar, negative indices go back in time.
        e.g., bars[-1] = previous bar
        """
        if not self._bars:
            return None
        
        # Convert to list index (reverse order)
        # bars[0] = latest, bars[-1] = previous
        if index <= 0:
            actual_index = -1 - index
        else:
            actual_index = len(self._bars) - 1 - index
        
        if 0 <= actual_index < len(self._bars):
            return self._bars[actual_index]
        return None
    
    @property
    def current(self) -> Optional[Bar]:
        """Get current (latest) bar."""
        return self[0]
    
    @property
    def previous(self) -> Optional[Bar]:
        """Get previous bar."""
        return self[-1]
    
    @property
    def count(self) -> int:
        """Get number of bars."""
        return len(self._bars)
    
    def add(self, bar: Bar) -> None:
        """Add a new bar."""
        self._bars.append(bar)
        
        # Trim if exceeds max
        if len(self._bars) > self._max_bars:
            self._bars = self._bars[-self._max_bars:]
    
    def update(self, bar: Bar) -> None:
        """Update the current (latest) bar."""
        if self._bars:
            self._bars[-1] = bar
        else:
            self._bars.append(bar)
    
    def load(self, bars: List[Bar]) -> None:
        """Load historical bars."""
        self._bars = bars[-self._max_bars:]
    
    def closes(self, count: Optional[int] = None) -> List[float]:
        """Get list of close prices."""
        bars = self._bars[-count:] if count else self._bars
        return [b.close for b in bars]
    
    def opens(self, count: Optional[int] = None) -> List[float]:
        """Get list of open prices."""
        bars = self._bars[-count:] if count else self._bars
        return [b.open for b in bars]
    
    def highs(self, count: Optional[int] = None) -> List[float]:
        """Get list of high prices."""
        bars = self._bars[-count:] if count else self._bars
        return [b.high for b in bars]
    
    def lows(self, count: Optional[int] = None) -> List[float]:
        """Get list of low prices."""
        bars = self._bars[-count:] if count else self._bars
        return [b.low for b in bars]
    
    def volumes(self, count: Optional[int] = None) -> List[float]:
        """Get list of volumes."""
        bars = self._bars[-count:] if count else self._bars
        return [b.volume for b in bars]
    
    def highest(self, period: int) -> float:
        """Get highest high in period."""
        highs = self.highs(period)
        return max(highs) if highs else 0
    
    def lowest(self, period: int) -> float:
        """Get lowest low in period."""
        lows = self.lows(period)
        return min(lows) if lows else 0
    
    def sma(self, period: int) -> float:
        """Calculate Simple Moving Average of close prices."""
        closes = self.closes(period)
        return sum(closes) / len(closes) if closes else 0
    
    def ema(self, period: int) -> float:
        """Calculate Exponential Moving Average of close prices."""
        closes = self.closes(period)
        if not closes:
            return 0
        
        multiplier = 2 / (period + 1)
        ema = closes[0]
        
        for price in closes[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema




@dataclass
class Symbol:
    """
    Symbol data wrapper with market information.
    
    Provides access to:
    - Symbol info (tick size, lot size, etc.)
    - Current market data (bid, ask, last price)
    - Historical and live bars
    """
    
    name: str
    
    # Symbol info
    tick_size: float = 0.01
    lot_size: int = 1
    min_qty: int = 1
    max_qty: int = 1000000
    digits: int = 2
    currency: str = "VND"
    
    # Risk / Calculation info
    point_value: float = 1.0
    margin_rate: float = 1.0 # Default 100% (Cash) if not set. 0.1 for 10% margin.

    # Current market data
    bid: float = 0.0
    ask: float = 0.0
    last_price: float = 0.0
    volume: float = 0.0
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    close_price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    
    # Bars data
    bars: Bars = field(default_factory=Bars)
    
    # Order book
    bid_depth: List[tuple] = field(default_factory=list)  # [(price, qty), ...]
    ask_depth: List[tuple] = field(default_factory=list)
    
    @property
    def spread(self) -> float:
        """Get bid-ask spread."""
        return self.ask - self.bid
    
    @property
    def spread_pct(self) -> float:
        """Get spread as percentage of mid price."""
        mid = (self.bid + self.ask) / 2
        return (self.spread / mid * 100) if mid > 0 else 0
    
    @property
    def mid_price(self) -> float:
        """Get mid price."""
        return (self.bid + self.ask) / 2
    
    def update_from_stat(self, stat: ProductStat) -> None:
        """Update from ProductStat data."""
        self.last_price = stat.last_price
        self.bid = stat.bid_price
        self.ask = stat.ask_price
        self.volume = stat.total_traded_qty
        self.open_price = stat.open_price
        self.high_price = stat.high_price
        self.low_price = stat.low_price
        self.close_price = stat.close_price
        self.change = stat.change
        self.change_pct = stat.change_pct
    
    def update_from_info(self, info: ProductInfo) -> None:
        """Update from ProductInfo data."""
        self.tick_size = info.tick_size
        self.lot_size = info.lot_size
        self.currency = info.currency
    
    def update_from_master(self, master: Any) -> None: # Type Any to avoid circular import if ProductMaster not available
        """Update from ProductMaster object."""
        if master.info:
            self.update_from_info(master.info)
        # Attempt to infer point value/margin if present in generic dict or extra fields
        # Note: API might provided these separately.
    
    def update_from_depth(self, depth: Depth) -> None:
        """Update from Depth data."""
        self.bid_depth = [(l.price, l.qty) for l in depth.bid_price_depth[:5]]
        self.ask_depth = [(l.price, l.qty) for l in depth.ask_price_depth[:5]]
        
        if depth.bid_price_depth:
            self.bid = depth.bid_price_depth[0].price
        if depth.ask_price_depth:
            self.ask = depth.ask_price_depth[0].price
    
    def normalize_price(self, price: float) -> float:
        """Round price to valid tick size."""
        if self.tick_size <= 0: return price
        steps = round(price / self.tick_size)
        return steps * self.tick_size
    
    def normalize_quantity(self, qty: float) -> int:
        """Round quantity to valid lot size and enforce min/max."""
        if self.lot_size <= 0: return int(qty)
        
        # Round to lot size
        steps = int(qty / self.lot_size)
        rounded = steps * self.lot_size
        
        # Clamp
        if rounded < self.min_qty:
            return 0 # Or min_qty? usually 0 if below min. user asks "follow min".
                     # If user wants 0.5 and min is 1, return 0 or 1?
                     # Return 0 implies reject? Or clamp to min?
                     # "Follow min... too" implies enforcement.
                     # Safest is to clamp to min if non-zero, but if input is tiny?
                     # Let's return rounded, but check bounds in caller or here?
                     # "normalize" usually implies making valid.
            rounded = self.min_qty if rounded > 0 else 0
            
        if rounded > self.max_qty:
            rounded = self.max_qty
            
        return rounded
