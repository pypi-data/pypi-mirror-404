"""
Risk settings and rules for Vero Algo SDK.

Defines configuration for risk management controls.
"""

from dataclasses import dataclass
from typing import Optional

from ..utils.defaults import (
    DEFAULT_MAX_DAILY_LOSS,
    DEFAULT_MAX_DAILY_PROFIT,
    DEFAULT_MAX_POSITION_LOSS_PCT,
    DEFAULT_MAX_POSITION_PROFIT_PCT,
    DEFAULT_MAX_OPEN_POSITIONS,
    DEFAULT_MAX_ORDER_QTY,
    DEFAULT_MAX_DRAWDOWN_PCT,
    DEFAULT_TRAILING_STOP_PCT,
)


@dataclass
class RiskSettings:
    """
    Risk management settings.
    
    Configure these to control automated risk limits.
    """
    
    # Daily P&L limits (absolute values)
    max_daily_loss: float = DEFAULT_MAX_DAILY_LOSS
    max_daily_profit: float = DEFAULT_MAX_DAILY_PROFIT
    halt_on_daily_limit: bool = True  # Stop trading when limit reached
    
    # Per-position P&L limits (percentage)
    max_position_loss_pct: float = DEFAULT_MAX_POSITION_LOSS_PCT
    max_position_profit_pct: float = DEFAULT_MAX_POSITION_PROFIT_PCT
    auto_close_on_limit: bool = True  # Auto close position at limit
    
    # Position limits
    max_open_positions: int = DEFAULT_MAX_OPEN_POSITIONS
    max_positions_per_symbol: int = 1
    
    # Order limits
    max_order_qty: int = DEFAULT_MAX_ORDER_QTY
    max_order_value: float = 0  # 0 = no limit
    
    # Drawdown protection
    max_drawdown_pct: float = DEFAULT_MAX_DRAWDOWN_PCT
    halt_on_drawdown: bool = True
    
    # Trailing stop
    enable_trailing_stop: bool = False
    trailing_stop_pct: float = DEFAULT_TRAILING_STOP_PCT
    
    # Margin settings
    min_free_margin_pct: float = 10.0  # Min free margin to open new positions
    
    # Time-based rules
    no_trade_before: Optional[str] = None  # "HH:MM" format
    no_trade_after: Optional[str] = None   # "HH:MM" format
    close_all_at: Optional[str] = None     # Auto close all at time
    
    # Safety circuit breaker
    max_consecutive_losses: int = 0  # 0 = disabled
    pause_after_losses_minutes: int = 30
    
    def validate(self) -> bool:
        """Validate settings."""
        if self.max_daily_loss <= 0:
            return False
        if self.max_position_loss_pct <= 0 or self.max_position_loss_pct > 100:
            return False
        if self.max_drawdown_pct <= 0 or self.max_drawdown_pct > 100:
            return False
        return True
    
    @classmethod
    def conservative(cls) -> "RiskSettings":
        """Create conservative risk settings."""
        return cls(
            max_daily_loss=2000,
            max_position_loss_pct=1.0,
            max_position_profit_pct=3.0,
            max_open_positions=3,
            max_drawdown_pct=5.0,
            enable_trailing_stop=True,
            trailing_stop_pct=1.0,
        )
    
    @classmethod
    def moderate(cls) -> "RiskSettings":
        """Create moderate risk settings."""
        return cls(
            max_daily_loss=5000,
            max_position_loss_pct=2.0,
            max_position_profit_pct=5.0,
            max_open_positions=5,
            max_drawdown_pct=10.0,
            enable_trailing_stop=True,
            trailing_stop_pct=2.0,
        )
    
    @classmethod
    def aggressive(cls) -> "RiskSettings":
        """Create aggressive risk settings."""
        return cls(
            max_daily_loss=15000,
            max_position_loss_pct=5.0,
            max_position_profit_pct=15.0,
            max_open_positions=10,
            max_drawdown_pct=20.0,
            enable_trailing_stop=False,
        )
