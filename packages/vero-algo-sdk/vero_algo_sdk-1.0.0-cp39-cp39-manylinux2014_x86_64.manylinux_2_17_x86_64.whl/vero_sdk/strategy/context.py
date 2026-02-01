"""
Trading context for strategy framework.

Provides access to market data, positions, orders, and account information.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .position import Position, PositionSide, ClosedPosition
from .symbol import Symbol, Bar, Bars
from ..types import OrderData, Trade, Account
from ..utils.logging_config import StrategyLogger


@dataclass
class AccountInfo:
    """Account information and balance."""
    
    account_id: str = ""
    equity: float = 0.0
    balance: float = 0.0
    margin: float = 0.0
    free_margin: float = 0.0
    margin_level: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    @classmethod
    def from_account(cls, account: Account) -> "AccountInfo":
        """Create from Account type."""
        return cls(
            account_id=account.account_id,
            equity=account.total_equity,
            balance=account.credit,
            margin=0,
            free_margin=account.trading_power,
            unrealized_pnl=account.total_unrealized_pnl,
            realized_pnl=account.total_realized_pnl,
        )


class TradingContext:
    """
    Trading context providing access to all trading data.
    
    Used by Strategy to access:
    - symbols: Dict of Symbol objects with market data
    - positions: Dict of open Position objects
    - orders: Dict of pending OrderData objects
    - history: List of ClosedPosition objects
    - account: AccountInfo
    """
    
    def __init__(self, account_id: str = "", initial_capital: float = 100000, max_nav_usage_pct: float = 100.0):
        # Symbols
        self._symbols: Dict[str, Symbol] = {}
        
        # Positions and orders
        self._positions: Dict[str, Position] = {}
        self._orders: Dict[str, OrderData] = {}
        self._history: List[ClosedPosition] = []
        self._trades: List[Trade] = []
        
        # Account
        self._account = AccountInfo(
            account_id=account_id,
            equity=initial_capital,
            balance=initial_capital,
            free_margin=initial_capital,
        )
        
        # Tracking
        self._initial_capital = initial_capital
        self._peak_equity = initial_capital
        self._daily_pnl = 0.0
        self._daily_start_equity = initial_capital
        
        # NAV Management
        self._max_nav_usage_pct = max_nav_usage_pct  # Max % of NAV to use
        self._max_nav = initial_capital * max_nav_usage_pct / 100
        self._used_nav = 0.0  # Currently reserved NAV
        self._reserved_orders: Dict[str, float] = {}  # order_id -> reserved amount
        
        # Current time (for backtesting)
        self._current_time = datetime.now()
    
    @property
    def symbols(self) -> Dict[str, Symbol]:
        """Get all subscribed symbols."""
        return self._symbols
    
    @property
    def positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        return self._positions
    
    @property
    def orders(self) -> Dict[str, OrderData]:
        """Get all pending orders."""
        return self._orders
    
    @property
    def history(self) -> List[ClosedPosition]:
        """Get trade history (closed positions)."""
        return self._history
    
    @property
    def trades(self) -> List[Trade]:
        """Get all trades."""
        return self._trades
    
    @property
    def account(self) -> AccountInfo:
        """Get account information."""
        return self._account
    
    @property
    def equity(self) -> float:
        """Get current equity."""
        return self._account.equity
    
    @property
    def balance(self) -> float:
        """Get current balance."""
        return self._account.balance
    
    @property
    def unrealized_pnl(self) -> float:
        """Get total unrealized P&L across all positions."""
        return sum(p.unrealized_pnl for p in self._positions.values())
    
    @property
    def realized_pnl(self) -> float:
        """Get total realized P&L."""
        return sum(p.pnl for p in self._history)
    
    @property
    def daily_pnl(self) -> float:
        """Get today's P&L."""
        return self._daily_pnl
    
    @property
    def drawdown(self) -> float:
        """Get current drawdown from peak equity."""
        if self._peak_equity <= 0:
            return 0
        return (self._peak_equity - self._account.equity) / self._peak_equity * 100
    
    @property
    def current_time(self) -> datetime:
        """Get current time (for backtesting)."""
        return self._current_time
    
    def add_symbol(self, symbol_name: str) -> Symbol:
        """Add and return a symbol."""
        if symbol_name not in self._symbols:
            self._symbols[symbol_name] = Symbol(name=symbol_name)
        return self._symbols[symbol_name]
    
    def get_symbol(self, symbol_name: str) -> Optional[Symbol]:
        """Get a symbol by name."""
        return self._symbols.get(symbol_name)
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol."""
        for pos in self._positions.values():
            if pos.symbol == symbol:
                return pos
        return None
    
    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get all positions for a symbol."""
        return [p for p in self._positions.values() if p.symbol == symbol]
    
    def has_position(self, symbol: str) -> bool:
        """Check if there's an open position for symbol."""
        return any(p.symbol == symbol for p in self._positions.values())
    
    def open_position(
        self,
        symbol: str,
        side: PositionSide,
        quantity: int,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop: bool = False,
        trailing_stop_distance: float = 0,
    ) -> Position:
        """
        Open a new position.
        
        Returns:
            The new Position object
        """
        # 1. Get Symbol info
        sym_obj = self.get_symbol(symbol)
        point_value = sym_obj.point_value if sym_obj else 1.0
        margin_rate = sym_obj.margin_rate if sym_obj else 1.0 # Default cash
        
        # 2. Normalize
        if sym_obj:
            quantity = sym_obj.normalize_quantity(quantity)
            price = sym_obj.normalize_price(price)
            
        position = Position(
            id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=price,
            entry_time=self._current_time,
            current_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=trailing_stop,
            trailing_stop_distance=trailing_stop_distance,
            account_id=self._account.account_id,
            point_value=point_value,
        )
        
        self._positions[position.id] = position
        
        # 3. Update Margin
        # Cost = Qty * Price * MarginRate * PointValue
        margin_required = quantity * price * margin_rate * point_value
        
        self._account.margin += margin_required
        # Free margin = Equity - Margin
        self._account.free_margin = self._account.equity - self._account.margin
        
        # Note: If NAV logic was used to reserve this, caller must handle conversion context.
        # But 'open_position' is the definitive state change.
        
        return position
    
    def close_position(self, position_id: str, price: float) -> Optional[ClosedPosition]:
        """
        Close a position.
        
        Returns:
            ClosedPosition record or None if position not found
        """
        position = self._positions.get(position_id)
        if not position:
            return None
            
        # 1. Get Symbol info
        sym_obj = self.get_symbol(position.symbol)
        point_value = sym_obj.point_value if sym_obj else 1.0
        margin_rate = sym_obj.margin_rate if sym_obj else 1.0
        
        # Normalize exit price
        if sym_obj:
            price = sym_obj.normalize_price(price)
        
        # 2. Calculate PnL
        # Long: (Exit - Entry) * Qty * PointValue
        # Short: (Entry - Exit) * Qty * PointValue
        price_diff = price - position.entry_price
        if position.side == PositionSide.SHORT:
            price_diff = -price_diff
            
        realized_pnl = price_diff * position.quantity * point_value
        
        # Create closed position record
        closed = ClosedPosition.from_position(position, price, point_value=point_value)
        closed.pnl = realized_pnl # Override with precise calculation
        self._history.append(closed)
        
        # 3. Update account
        self._account.balance += realized_pnl
        self._account.equity = self._account.balance + self.unrealized_pnl
        self._daily_pnl += realized_pnl
        
        # Update peak equity
        if self._account.equity > self._peak_equity:
            self._peak_equity = self._account.equity
        
        # 4. Release Margin (Capital)
        # Assuming margin is based on ENTRY price.
        margin_released = position.quantity * position.entry_price * margin_rate * point_value
        self._account.margin = max(0, self._account.margin - margin_released)
        self._account.free_margin = self._account.equity - self._account.margin
        
        # Remove from open positions
        del self._positions[position_id]
        
        # 5. Return Released Capital info (implicit via margin update, but maybe return value?)
        # User asked "return used capital...". The method returns ClosedPosition.
        # The account state is updated.
        
        return closed
    
    def update_prices(self) -> None:
        """Update all position prices from symbol data."""
        for position in self._positions.values():
            symbol = self._symbols.get(position.symbol)
            if symbol:
                position.update_price(symbol.last_price)
        
        # Update account equity
        self._account.unrealized_pnl = self.unrealized_pnl
        self._account.equity = self._account.balance + self._account.unrealized_pnl
        
        # Update max NAV based on current equity
        self._max_nav = self._account.equity * self._max_nav_usage_pct / 100
    
    def reset_daily_pnl(self) -> None:
        """Reset daily P&L tracking (call at start of new day)."""
        self._daily_pnl = 0.0
        self._daily_start_equity = self._account.equity
    
    def set_time(self, time: datetime) -> None:
        """Set current time (for backtesting)."""
        self._current_time = time
    
    # ========================================================================
    # NAV Management
    # ========================================================================
    
    @property
    def max_nav(self) -> float:
        """Get maximum NAV allowed for trading."""
        return self._max_nav
    
    @property
    def used_nav(self) -> float:
        """Get currently used NAV."""
        return self._used_nav
    
    @property
    def available_nav(self) -> float:
        """Get available NAV for new orders."""
        return max(0, self._max_nav - self._used_nav)
    
    @property
    def nav_usage_pct(self) -> float:
        """Get NAV usage percentage."""
        if self._max_nav <= 0:
            return 100.0
        return (self._used_nav / self._max_nav) * 100
    
    def can_use_nav(self, amount: float) -> bool:
        """
        Check if NAV is available for an order.
        
        Args:
            amount: Order value to check
            
        Returns:
            True if NAV is available
        """
        return amount <= self.available_nav
    
    def reserve_nav(self, order_id: str, amount: float) -> bool:
        """
        Reserve NAV for a pending order.
        
        Args:
            order_id: Order ID
            amount: Value to reserve
            
        Returns:
            True if reserved successfully
        """
        if not self.can_use_nav(amount):
            return False
        
        self._used_nav += amount
        self._reserved_orders[order_id] = amount
        return True
    
    def release_nav(self, order_id: str) -> float:
        """
        Release reserved NAV for an order (cancelled/rejected).
        
        Args:
            order_id: Order ID
            
        Returns:
            Amount released
        """
        if order_id in self._reserved_orders:
            amount = self._reserved_orders.pop(order_id)
            self._used_nav = max(0, self._used_nav - amount)
            return amount
        return 0
    
    def convert_nav_to_position(self, order_id: str) -> float:
        """
        Convert reserved NAV to used (order filled -> position opened).
        NAV stays used, just no longer tied to order_id.
        
        Args:
            order_id: Order ID
            
        Returns:
            Amount converted
        """
        if order_id in self._reserved_orders:
            amount = self._reserved_orders.pop(order_id)
            # NAV remains used (now in position)
            return amount
        return 0
    
    def close_position_release_nav(self, position_id: str, amount: float) -> None:
        """
        Release NAV when position is closed.
        
        Args:
            position_id: Position ID
            amount: Amount to release
        """
        self._used_nav = max(0, self._used_nav - amount)

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if found and cancelled
        """
        # In this context, 'orders' are just reserved NAV records or explicit pending orders if tracked.
        # But _orders dict was defined. Let's see if we populate it in Strategy.buy?
        # Strategy.buy calls _open_position which does NOT add to _orders (it processes immediately).
        # So _orders is currently unused in simple backtest!
        # But if we want to simulate pending limit orders, we need to add them.
        # For now, we mainly handle NAV release.
        
        if order_id in self._reserved_orders:
            self.release_nav(order_id)
            return True
            
        # Check _orders dict just in case future implementation uses it
        if order_id in self._orders:
            del self._orders[order_id]
            return True
            
        return False
