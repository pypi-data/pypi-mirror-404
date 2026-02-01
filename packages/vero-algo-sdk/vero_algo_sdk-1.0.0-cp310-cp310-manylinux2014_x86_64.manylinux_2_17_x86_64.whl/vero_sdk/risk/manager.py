"""
Risk manager for Vero Algo SDK.

Monitors positions and enforces risk limits automatically.
"""

from datetime import datetime
from typing import Tuple, Optional, List

from .rules import RiskSettings
from ..strategy.context import TradingContext
from ..strategy.position import Position, PositionSide
from ..utils.logging_config import StrategyLogger


class RiskManager:
    """
    Automated risk management engine.
    
    Monitors positions and enforces:
    - Daily P&L limits
    - Per-position stop-loss and take-profit
    - Max drawdown protection
    - Position count limits
    - Order size limits
    - Trailing stops
    """
    
    def __init__(
        self,
        settings: RiskSettings,
        context: TradingContext,
        logger: StrategyLogger,
    ):
        """
        Initialize RiskManager.
        
        Args:
            settings: RiskSettings configuration
            context: TradingContext to monitor
            logger: Logger for risk events
        """
        self.settings = settings
        self.context = context
        self.logger = logger
        
        # State tracking
        self._halted = False
        self._halt_reason = ""
        self._consecutive_losses = 0
        self._paused_until: Optional[datetime] = None
        self._positions_to_close: List[str] = []
    
    @property
    def is_halted(self) -> bool:
        """Check if trading is halted."""
        return self._halted
    
    @property
    def halt_reason(self) -> str:
        """Get reason for trading halt."""
        return self._halt_reason
    
    def can_open_position(
        self,
        symbol: str,
        side: PositionSide,
        qty: int,
        price: float,
    ) -> Tuple[bool, str]:
        """
        Check if a new position can be opened.
        
        Args:
            symbol: Trading symbol
            side: Position side
            qty: Quantity
            price: Entry price
            
        Returns:
            Tuple of (allowed, reason)
        """
        # Check if halted
        if self._halted:
            return False, f"Trading halted: {self._halt_reason}"
        
        # Check if paused
        if self._paused_until and datetime.now() < self._paused_until:
            remaining = (self._paused_until - datetime.now()).seconds // 60
            return False, f"Trading paused for {remaining} more minutes"
        
        # Check time restrictions
        if not self._check_trading_time():
            return False, "Outside trading hours"
        
        # Check daily loss limit
        if abs(self.context.daily_pnl) >= self.settings.max_daily_loss:
            if self.settings.halt_on_daily_limit:
                self._halt("Daily loss limit reached")
            return False, "Daily loss limit reached"
        
        # Check drawdown
        if self.context.drawdown >= self.settings.max_drawdown_pct:
            if self.settings.halt_on_drawdown:
                self._halt("Max drawdown reached")
            return False, "Max drawdown reached"
        
        # Check max positions
        if len(self.context.positions) >= self.settings.max_open_positions:
            return False, f"Max {self.settings.max_open_positions} positions allowed"
        
        # Check positions per symbol
        symbol_positions = self.context.get_positions_by_symbol(symbol)
        if len(symbol_positions) >= self.settings.max_positions_per_symbol:
            return False, f"Max {self.settings.max_positions_per_symbol} positions per symbol"
        
        # Check order quantity
        if qty > self.settings.max_order_qty:
            return False, f"Qty {qty} exceeds max {self.settings.max_order_qty}"
        
        # Check order value
        order_value = qty * price
        if self.settings.max_order_value > 0 and order_value > self.settings.max_order_value:
            return False, f"Order value {order_value} exceeds max {self.settings.max_order_value}"
        
        # Check free margin
        margin_required = order_value * 0.1  # Simplified
        min_margin = self.context.equity * self.settings.min_free_margin_pct / 100
        if self.context.account.free_margin - margin_required < min_margin:
            return False, "Insufficient free margin"
        
        return True, ""
    
    def check_positions(self) -> List[str]:
        """
        Check all positions against risk limits.
        
        Returns:
            List of position IDs that should be closed
        """
        positions_to_close = []
        
        for pos_id, position in list(self.context.positions.items()):
            should_close, reason = self._check_position(position)
            if should_close:
                positions_to_close.append(pos_id)
                self.logger.risk(f"Position {pos_id} flagged for close: {reason}")
        
        return positions_to_close
    
    def _check_position(self, position: Position) -> Tuple[bool, str]:
        """Check a single position against limits."""
        # Check stop loss trigger
        if position.should_stop_loss():
            return True, "Stop loss triggered"
        
        # Check take profit trigger
        if position.should_take_profit():
            return True, "Take profit triggered"
        
        # Calculate position P&L percentage
        pnl_pct = position.pnl_percent
        
        # Check max loss
        if pnl_pct <= -self.settings.max_position_loss_pct:
            if self.settings.auto_close_on_limit:
                return True, f"Max loss {self.settings.max_position_loss_pct}% reached"
        
        # Check max profit
        if pnl_pct >= self.settings.max_position_profit_pct:
            if self.settings.auto_close_on_limit:
                return True, f"Profit target {self.settings.max_position_profit_pct}% reached"
        
        return False, ""
    
    def on_position_closed(self, pnl: float) -> None:
        """
        Handle position close event for consecutive loss tracking.
        
        Args:
            pnl: Realized P&L of closed position
        """
        if pnl < 0:
            self._consecutive_losses += 1
            
            if (self.settings.max_consecutive_losses > 0 and 
                self._consecutive_losses >= self.settings.max_consecutive_losses):
                
                self._pause_trading(self.settings.pause_after_losses_minutes)
                self.logger.risk(
                    f"Paused trading for {self.settings.pause_after_losses_minutes} minutes "
                    f"after {self._consecutive_losses} consecutive losses"
                )
        else:
            self._consecutive_losses = 0
    
    def _halt(self, reason: str) -> None:
        """Halt all trading."""
        self._halted = True
        self._halt_reason = reason
        self.logger.risk(f"TRADING HALTED: {reason}")
    
    def _pause_trading(self, minutes: int) -> None:
        """Pause trading for specified minutes."""
        from datetime import timedelta
        self._paused_until = datetime.now() + timedelta(minutes=minutes)
    
    def _check_trading_time(self) -> bool:
        """Check if current time is within trading hours."""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        if self.settings.no_trade_before:
            if current_time < self.settings.no_trade_before:
                return False
        
        if self.settings.no_trade_after:
            if current_time > self.settings.no_trade_after:
                return False
        
        return True
    
    def should_close_all(self) -> bool:
        """Check if all positions should be closed (end of day)."""
        if not self.settings.close_all_at:
            return False
        
        current_time = datetime.now().strftime("%H:%M")
        return current_time >= self.settings.close_all_at
    
    def reset_daily(self) -> None:
        """Reset daily counters (call at start of new trading day)."""
        self.context.reset_daily_pnl()
        self._consecutive_losses = 0
        self._paused_until = None
        
        # Only resume if halted due to daily limit
        if self._halted and "daily" in self._halt_reason.lower():
            self._halted = False
            self._halt_reason = ""
            self.logger.info("Daily limits reset, trading resumed")
    
    def resume_trading(self) -> None:
        """Manually resume trading after halt."""
        self._halted = False
        self._halt_reason = ""
        self._paused_until = None
        self.logger.info("Trading manually resumed")
