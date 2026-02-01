"""
Position management for strategy framework.

Tracks open positions with entry price, quantity, P&L, and stop/take-profit levels.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class PositionSide(str, Enum):
    """Position side."""
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class Position:
    """
    Represents an open trading position.
    
    Tracks entry details, current P&L, and risk management levels.
    """
    
    id: str
    symbol: str
    side: PositionSide
    quantity: int
    entry_price: float
    entry_time: datetime
    
    # Current state
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # Risk management / Contract Specs
    point_value: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: bool = False
    trailing_stop_distance: float = 0.0
    highest_price: float = 0.0  # For trailing stop
    lowest_price: float = 0.0   # For trailing stop
    
    # Metadata
    algo_id: str = ""
    account_id: str = ""
    order_id: str = ""  # Entry order ID
    
    def __post_init__(self):
        self.highest_price = self.entry_price
        self.lowest_price = self.entry_price
        self.current_price = self.entry_price
    
    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.side == PositionSide.LONG
    
    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.side == PositionSide.SHORT
    
    @property
    def market_value(self) -> float:
        """Calculate current market value."""
        return self.quantity * self.current_price * self.point_value
    
    @property
    def entry_value(self) -> float:
        """Calculate entry value."""
        return self.quantity * self.entry_price * self.point_value
    
    @property
    def pnl(self) -> float:
        """Get total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def pnl_percent(self) -> float:
        """Get P&L as percentage of entry value."""
        if self.entry_value == 0:
            return 0.0
        return (self.pnl / self.entry_value) * 100
    
    @property
    def duration(self) -> float:
        """Get position duration in seconds."""
        return (datetime.now() - self.entry_time).total_seconds()
    
    def update_price(self, price: float) -> None:
        """
        Update position with new market price.
        
        Recalculates unrealized P&L and updates trailing stop levels.
        """
        self.current_price = price
        
        # Update high/low for trailing stop
        if price > self.highest_price:
            self.highest_price = price
        if price < self.lowest_price:
            self.lowest_price = price
        
        # Calculate unrealized P&L
        if self.is_long:
            self.unrealized_pnl = (price - self.entry_price) * self.quantity * self.point_value
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.quantity * self.point_value
    
    def should_stop_loss(self) -> bool:
        """Check if stop loss should be triggered."""
        if self.stop_loss is None:
            return False
        
        if self.trailing_stop:
            # Calculate dynamic stop loss
            if self.is_long:
                dynamic_stop = self.highest_price - self.trailing_stop_distance
                return self.current_price <= dynamic_stop
            else:
                dynamic_stop = self.lowest_price + self.trailing_stop_distance
                return self.current_price >= dynamic_stop
        else:
            # Fixed stop loss
            if self.is_long:
                return self.current_price <= self.stop_loss
            else:
                return self.current_price >= self.stop_loss
    
    def should_take_profit(self) -> bool:
        """Check if take profit should be triggered."""
        if self.take_profit is None:
            return False
        
        if self.is_long:
            return self.current_price >= self.take_profit
        else:
            return self.current_price <= self.take_profit
    
    def close(self, exit_price: float) -> float:
        """
        Close the position and return final P&L.
        
        Args:
            exit_price: Price at which position is closed
            
        Returns:
            Final realized P&L
        """
        self.current_price = exit_price
        
        if self.is_long:
            final_pnl = (exit_price - self.entry_price) * self.quantity * self.point_value
        else:
            final_pnl = (self.entry_price - exit_price) * self.quantity * self.point_value
        
        self.realized_pnl = final_pnl
        self.unrealized_pnl = 0.0
        self.quantity = 0
        
        return final_pnl
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat(),
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "pnl_percent": self.pnl_percent,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "trailing_stop": self.trailing_stop,
        }


@dataclass
class ClosedPosition:
    """Record of a closed position for reporting."""
    
    id: str
    symbol: str
    side: PositionSide
    quantity: int
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_percent: float
    duration_seconds: float
    
    @classmethod
    def from_position(cls, position: Position, exit_price: float, point_value: Optional[float] = None) -> "ClosedPosition":
        """Create from an open position being closed."""
        exit_time = datetime.now()
        
        # Use provided point_value override or fallback to position's stored value
        pv = point_value if point_value is not None else position.point_value
        
        if position.is_long:
            pnl = (exit_price - position.entry_price) * position.quantity * pv
        else:
            pnl = (position.entry_price - exit_price) * position.quantity * pv
        
        entry_value = position.entry_price * position.quantity * pv
        pnl_percent = (pnl / entry_value * 100) if entry_value > 0 else 0
        
        return cls(
            id=position.id,
            symbol=position.symbol,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=exit_price,
            entry_time=position.entry_time,
            exit_time=exit_time,
            pnl=pnl,
            pnl_percent=pnl_percent,
            duration_seconds=(exit_time - position.entry_time).total_seconds(),
        )
