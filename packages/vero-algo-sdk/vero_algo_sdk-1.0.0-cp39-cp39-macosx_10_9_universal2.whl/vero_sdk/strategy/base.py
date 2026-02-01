"""
Strategy base class for Vero Algo SDK.

Provides cTrader-style robot/strategy framework with event-based processing.
"""

import time
import asyncio
import threading
import uuid
from abc import ABC
from enum import Enum
from typing import List, Optional, Dict, Any, Type
from datetime import datetime

from .context import TradingContext, AccountInfo
from .position import Position, PositionSide, ClosedPosition
from .symbol import Symbol, Bar, Bars
from ..utils.logging_config import StrategyLogger, setup_logging
from ..utils.defaults import (
    DEFAULT_BACKEND_SERVER,
    DEFAULT_AUTH_SERVER,
    DEFAULT_MICRO_API_SERVER,
    DEFAULT_STREAMING_WS,
)


class RunMode(str, Enum):
    """Strategy run mode."""
    LIVE = "LIVE"       # Real trading
    BACKTEST = "BACKTEST"  # Historical simulation


class Strategy(ABC):
    """
    Base class for trading strategies.
    
    Subclass this and implement event handlers:
    - on_start(): Called after initialization
    - on_stop(): Called before shutdown
    - on_bar(bar): Called when a new bar closes
    - on_tick(symbol): Called on price updates
    - on_order(order): Called on order status change
    - on_trade(trade): Called when trade executes
    - on_position_opened(position): Called when position opens
    - on_position_closed(position): Called when position closes
    
    Example:
        class MyStrategy(Strategy):
            def on_bar(self, bar):
                if bar.close > bar.open:
                    self.buy("VN30F2401", qty=1)
    """
    
    # Class-level configuration
    name: str = "Strategy"
    version: str = "1.0.0"
    
    def __init__(self):
        self._mode = RunMode.LIVE
        self._symbols: List[str] = []
        self._account_id = ""
        self._context: Optional[TradingContext] = None
        self._logger: Optional[StrategyLogger] = None
        self._client = None  # VeroClient instance
        self._running = False
        self._stop_event = threading.Event()
        
        # Risk manager reference (set by run method)
        self._risk_manager = None
        
        # Backtest engine reference (set in backtest mode)
        self._backtest_engine = None
    
    # ========================================================================
    # Properties
    # ========================================================================
    
    @property
    def logger(self) -> StrategyLogger:
        """Get strategy logger."""
        if self._logger is None:
            self._logger = StrategyLogger(self.name)
        return self._logger
    
    @property
    def context(self) -> Optional[TradingContext]:
        """Get trading context."""
        return self._context
    
    @property
    def positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        return self._context.positions if self._context else {}
    
    @property
    def orders(self) -> Dict[str, Any]:
        """Get all pending orders."""
        return self._context.orders if self._context else {}
    
    @property
    def account(self) -> AccountInfo:
        """Get account information."""
        return self._context.account if self._context else AccountInfo()
    
    @property
    def symbols(self) -> Dict[str, Symbol]:
        """Get subscribed symbols."""
        return self._context.symbols if self._context else {}
    
    @property
    def equity(self) -> float:
        """Get current equity."""
        return self._context.equity if self._context else 0
    
    @property
    def is_running(self) -> bool:
        """Check if strategy is running."""
        return self._running
    
    @property
    def mode(self) -> RunMode:
        """Get current run mode."""
        return self._mode
    
    @property
    def time(self) -> datetime:
        """Get current time."""
        return self._context.current_time if self._context else datetime.now()
    
    # ========================================================================
    # Event Handlers (Override in subclass)
    # ========================================================================
    
    def on_start(self) -> None:
        """
        Called when strategy starts.
        
        Override to perform initialization logic.
        Market data and symbols are already loaded at this point.
        """
        pass
    
    def on_stop(self) -> None:
        """
        Called when strategy stops.
        
        Override to perform cleanup logic.
        """
        pass
    
    def on_bar(self, bar: Bar) -> None:
        """
        Called when a new bar closes.
        
        Args:
            bar: The completed bar data
        """
        pass
    
    def on_tick(self, symbol: Symbol) -> None:
        """
        Called on price tick updates.
        
        Args:
            symbol: Symbol with updated price data
        """
        pass
    
    def on_depth(self, symbol: Symbol) -> None:
        """
        Called on order book depth updates.
        
        Args:
            symbol: Symbol with updated depth data
        """
        pass
    
    def on_order(self, order: Any) -> None:
        """
        Called when order status changes.
        
        Args:
            order: Order data with updated status
        """
        pass
    
    def on_trade(self, trade: Any) -> None:
        """
        Called when a trade executes.
        
        Args:
            trade: Trade execution data
        """
        pass
    
    def on_position_opened(self, position: Position) -> None:
        """
        Called when a position is opened.
        
        Args:
            position: The newly opened position
        """
        pass
    
    def on_position_closed(self, position: ClosedPosition) -> None:
        """
        Called when a position is closed.
        
        Args:
            position: The closed position record
        """
        pass
    
    def on_error(self, error: Exception) -> None:
        """
        Called when an error occurs.
        
        Args:
            error: The exception that occurred
        """
        self.logger.error(f"Error: {error}")
    
    # ========================================================================
    # Trading Methods
    # ========================================================================
    
    def buy(
        self,
        symbol: str,
        qty: int,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop: bool = False,
        trailing_stop_pct: float = 0,
    ) -> Optional[Position]:
        """
        Open a long position.
        
        Args:
            symbol: Trading symbol
            qty: Quantity to buy
            price: Limit price (None for market order)
            stop_loss: Stop loss price
            take_profit: Take profit price
            trailing_stop: Enable trailing stop
            trailing_stop_pct: Trailing stop percentage
            
        Returns:
            Position object if successful
        """
        return self._open_position(
            symbol=symbol,
            side=PositionSide.LONG,
            qty=qty,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=trailing_stop,
            trailing_stop_pct=trailing_stop_pct,
        )
    
    def sell(
        self,
        symbol: str,
        qty: int,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop: bool = False,
        trailing_stop_pct: float = 0,
    ) -> Optional[Position]:
        """
        Open a short position.
        
        Args:
            symbol: Trading symbol
            qty: Quantity to sell
            price: Limit price (None for market order)
            stop_loss: Stop loss price
            take_profit: Take profit price
            trailing_stop: Enable trailing stop
            trailing_stop_pct: Trailing stop percentage
            
        Returns:
            Position object if successful
        """
        return self._open_position(
            symbol=symbol,
            side=PositionSide.SHORT,
            qty=qty,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=trailing_stop,
            trailing_stop_pct=trailing_stop_pct,
        )
    

    def close_position(
        self,
        position: Position,
        price: Optional[float] = None,
    ) -> Optional[ClosedPosition]:
        """
        Close an open position.
        
        Args:
            position: Position to close
            price: Exit price (None for market)
            
        Returns:
            ClosedPosition record if successful
        """
        if not self._context:
            return None
        
        symbol = self._context.get_symbol(position.symbol)
        if not symbol:
            return None
        
        exit_price = price or symbol.last_price
        
        if self._mode == RunMode.LIVE and self._client:
            # Place close order via API
            side = "S" if position.is_long else "B"
            response = self._client.orders.place_order(
                symbol=position.symbol,
                side=side,
                price=exit_price,
                qty=position.quantity,
                account_id=self._account_id,
            )
            
            if not response.success:
                self.logger.error(f"Failed to close position: {response.message}")
                return None
        
        # Close in context
        closed = self._context.close_position(position.id, exit_price)
        
        if closed:
            self.logger.position("CLOSED", position.symbol, position.quantity, 
                               position.entry_price, closed.pnl)
            self.on_position_closed(closed)
        
        return closed
    
    def close_all_positions(self, symbol: Optional[str] = None) -> List[ClosedPosition]:
        """
        Close all open positions.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of closed positions
        """
        closed = []
        if not self._context:
            return closed
            
        positions = list(self._context.positions.values())
        
        for pos in positions:
            if symbol is None or pos.symbol == symbol:
                result = self.close_position(pos)
                if result:
                    closed.append(result)
        
        return closed
    
    def place_position(
        self,
        symbol: str,
        side: str,
        qty: int,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop: bool = False,
        trailing_stop_pct: float = 0,
    ) -> Optional[Position]:
        """
        Place a position with entry, stop-loss, and take-profit.
        
        Args:
            symbol: Trading symbol
            side: "BUY"/"LONG" or "SELL"/"SHORT"
            qty: Quantity
            entry_price: Entry price
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            trailing_stop: Enable trailing stop
            trailing_stop_pct: Trailing stop percentage
            
        Returns:
            Position object if successful
        """
        # Normalize side
        if side.upper() in ("BUY", "LONG", "B"):
            position_side = PositionSide.LONG
        else:
            position_side = PositionSide.SHORT
        
        return self._open_position(
            symbol=symbol,
            side=position_side,
            qty=qty,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=trailing_stop,
            trailing_stop_pct=trailing_stop_pct,
        )
    
    def cancel_position(self, position: Position) -> Optional[ClosedPosition]:
        """
        Cancel/close a position at current market price.
        
        Same as close_position but with clearer naming.
        
        Args:
            position: Position to cancel
            
        Returns:
            ClosedPosition record
        """
        return self.close_position(position)
    
    def cancel_all_positions(self, symbol: Optional[str] = None) -> List[ClosedPosition]:
        """
        Cancel all open positions.
        
        Same as close_all_positions but with clearer naming.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of closed positions
        """
        return self.close_all_positions(symbol)
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancellation request was sent/processed
        """
        if self._mode == RunMode.LIVE and self._client:
            # Call API
            response = self._client.orders.cancel_order(
                order_id=order_id,
                account_id=self._account_id
            )
            return response.success
            
        elif self._context:
            # Backtest context cancellation
            return self._context.cancel_order(order_id)
            
        return False
    
    # ========================================================================
    # NAV Access
    # ========================================================================
    
    @property
    def available_nav(self) -> float:
        """Get available NAV for new orders."""
        return self._context.available_nav if self._context else 0
    
    @property
    def used_nav(self) -> float:
        """Get currently used NAV."""
        return self._context.used_nav if self._context else 0
    
    @property
    def max_nav(self) -> float:
        """Get maximum allowed NAV."""
        return self._context.max_nav if self._context else 0
    
    @property
    def nav_usage_pct(self) -> float:
        """Get NAV usage percentage."""
        return self._context.nav_usage_pct if self._context else 0
    
    def _open_position(
        self,
        symbol: str,
        side: PositionSide,
        qty: int,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop: bool = False,
        trailing_stop_pct: float = 0,
    ) -> Optional[Position]:
        """Internal method to open a position."""
        if not self._context:
            return None
        
        sym = self._context.get_symbol(symbol)
        if not sym:
            self.logger.error(f"Symbol {symbol} not found")
            return None
        
        entry_price = price or sym.last_price
        order_value = qty * entry_price
        
        # Check NAV availability
        if not self._context.can_use_nav(order_value):
            self.logger.risk(f"Insufficient NAV: need {order_value:,.0f}, available {self._context.available_nav:,.0f}")
            return None
        
        # Check risk limits
        if self._risk_manager:
            can_trade, reason = self._risk_manager.can_open_position(
                symbol, side, qty, entry_price
            )
            if not can_trade:
                self.logger.risk(f"Trade blocked: {reason}")
                return None
        
        # Calculate trailing stop distance
        trailing_distance = 0
        if trailing_stop and trailing_stop_pct > 0:
            trailing_distance = entry_price * trailing_stop_pct / 100
        
        # Generate order ID for NAV tracking
        order_id = str(uuid.uuid4())
        
        # Reserve NAV
        if not self._context.reserve_nav(order_id, order_value):
            self.logger.risk(f"Failed to reserve NAV: {order_value:,.0f}")
            return None
        
        if self._mode == RunMode.LIVE and self._client:
            # Place order via API
            order_side = "B" if side == PositionSide.LONG else "S"
            response = self._client.orders.place_order(
                symbol=symbol,
                side=order_side,
                price=entry_price,
                qty=qty,
                account_id=self._account_id,
            )
            
            if not response.success:
                self.logger.error(f"Failed to place order: {response.message}")
                # Release NAV on rejection
                self._context.release_nav(order_id)
                return None
        
        # Convert NAV reservation to position
        self._context.convert_nav_to_position(order_id)
        
        # Open in context
        position = self._context.open_position(
            symbol=symbol,
            side=side,
            quantity=qty,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=trailing_stop,
            trailing_stop_distance=trailing_distance,
        )
        
        action = "BUY" if side == PositionSide.LONG else "SELL"
        self.logger.order(action, symbol, qty, entry_price)
        self.on_position_opened(position)
        
        return position
    
    # ========================================================================
    # Symbol Access
    # ========================================================================
    
    def bars(self, symbol: str) -> Bars:
        """
        Get bars for a symbol.
        
        Args:
            symbol: Symbol name
            
        Returns:
            Bars object with historical data
        """
        sym = self._context.get_symbol(symbol) if self._context else None
        return sym.bars if sym else Bars()
    
    def symbol(self, name: str) -> Optional[Symbol]:
        """
        Get symbol data.
        
        Args:
            name: Symbol name
            
        Returns:
            Symbol object or None
        """
        return self._context.get_symbol(name) if self._context else None
    
    # ========================================================================
    # Control Methods
    # ========================================================================
    
    def stop(self) -> None:
        """Stop the strategy."""
        self._stop_event.set()
        self._running = False
    
    # ========================================================================
    # Class Methods for Running
    # ========================================================================
    
    @classmethod
    def run(
        cls,
        mode: RunMode = RunMode.LIVE,
        symbols: Optional[List[str]] = None,
        account_id: str = "",
        jwt_token: str = "",
        # Backtest parameters
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_capital: float = 100000,
        resolution: int = 86400,  # Daily bars
        backtest_settings: Any = None,  # BacktestSettings object
        # Risk parameters
        risk_settings: Any = None,
        max_nav_usage_pct: float = 100.0,  # Max % of NAV to use
        # Connection parameters
        backend_server: Optional[str] = None,
        auth_server: Optional[str] = None,
        streaming_ws: Optional[str] = None,
    ):
        """
        Run the strategy.
        
        Args:
            mode: RunMode.LIVE or RunMode.BACKTEST
            symbols: List of symbols to trade
            account_id: Account ID for live trading
            account_id: Account ID for live trading
            jwt_token: JWT Token for authentication
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            initial_capital: Starting capital
            resolution: Bar resolution in seconds
            backtest_settings: BacktestSettings object (overrides individual params)
            risk_settings: RiskSettings object
            max_nav_usage_pct: Max percentage of NAV to use for trading
            backend_server: Override backend server URL
            auth_server: Override auth server URL
            streaming_ws: Override streaming WebSocket URL
            
        Returns:
            BacktestResult in BACKTEST mode, None in LIVE mode
        """
        # Setup logging
        setup_logging()
        
        # Create instance
        instance = cls()
        instance._mode = mode
        instance._symbols = symbols or []
        instance._account_id = account_id
        instance._logger = StrategyLogger(cls.name)
        
        # Apply backtest_settings if provided
        if backtest_settings:
            symbols = backtest_settings.symbols or symbols
            start_date = backtest_settings.from_date or start_date
            end_date = backtest_settings.to_date or end_date
            initial_capital = backtest_settings.initial_capital or initial_capital
            resolution = backtest_settings.resolution or resolution
            max_nav_usage_pct = backtest_settings.max_nav_usage_pct or max_nav_usage_pct
        
        instance._symbols = symbols or []
        
        instance.logger.info(f"Starting {cls.name} v{cls.version} in {mode.value} mode")
        
        if mode == RunMode.BACKTEST:
            return instance._run_backtest(
                symbols=symbols or [],
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                resolution=resolution,
                risk_settings=risk_settings,
                jwt_token=jwt_token,
                max_nav_usage_pct=max_nav_usage_pct,
                backtest_settings=backtest_settings,
            )
        else:
            return asyncio.run(instance._run_live(
                symbols=symbols or [],
                account_id=account_id,
                jwt_token=jwt_token,
                risk_settings=risk_settings,
                max_nav_usage_pct=max_nav_usage_pct,
                backend_server=backend_server or DEFAULT_BACKEND_SERVER,
                auth_server=auth_server or DEFAULT_AUTH_SERVER,
                streaming_ws=streaming_ws or DEFAULT_STREAMING_WS,
            ))
    
    async def _run_live(
        self,
        symbols: List[str],
        account_id: str,
        jwt_token: str,
        risk_settings: Any,
        max_nav_usage_pct: float,
        backend_server: str,
        auth_server: str,
        streaming_ws: str,
    ) -> None:
        """Run strategy in live mode."""
        from ..client import VeroClient
        from ..risk import RiskManager
        
        # Create client
        self._client = VeroClient(
            backend_server=backend_server,
            auth_server=auth_server,
            streaming_ws=streaming_ws,
        )
        
        if jwt_token:
            self._client.set_jwt_token(jwt_token)
        
        if not account_id:
             self.logger.warning("No account_id provided for Live Mode.")

        # Create context with NAV settings
        self._context = TradingContext(
            account_id=account_id,
            max_nav_usage_pct=max_nav_usage_pct,
        )
        
        # Setup risk manager
        if risk_settings:
            self._risk_manager = RiskManager(risk_settings, self._context, self.logger)
        
        # Load symbols and subscribe
        self.logger.info(f"Subscribing to {len(symbols)} symbols...")
        self._subscribe_symbols(symbols)
        
        # Start strategy
        self._running = True
        self.on_start()
        
        # Connect to streaming
        await self._client.stream.connect(
            on_connect=self._on_stream_connect,
            on_disconnect=self._on_stream_disconnect,
        )
        
        # Main loop
        try:
            while self._running and not self._stop_event.is_set():
                # Check risk limits
                if self._risk_manager:
                    self._risk_manager.check_positions()
                
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        finally:
            self._running = False
            self.on_stop()
            await self._client.stream.disconnect()
            # self._client.logout() removed
            self.logger.info("Strategy stopped")
    
    def _run_backtest(
        self,
        symbols: List[str],
        start_date: Optional[str],
        end_date: Optional[str],
        initial_capital: float,
        resolution: int,
        risk_settings: Any,
        jwt_token: str = "",
        max_nav_usage_pct: float = 100.0,
        backtest_settings: Any = None,
    ):
        """Run strategy in backtest mode."""
        from ..backtest import BacktestEngine
        from ..risk import RiskManager
        
        # Create context with NAV settings
        self._context = TradingContext(
            initial_capital=initial_capital,
            max_nav_usage_pct=max_nav_usage_pct,
        )
        
        # Setup risk manager
        if risk_settings:
            self._risk_manager = RiskManager(risk_settings, self._context, self.logger)
        
        # Validate dates
        if start_date is None or end_date is None:
             raise ValueError("start_date and end_date are required for backtest mode")
        
        # Get settings from backtest_settings if available
        commission_pct = 0.1
        slippage_ticks = 1
        if backtest_settings:
            commission_pct = getattr(backtest_settings, 'commission_pct', 0.1)
            slippage_ticks = getattr(backtest_settings, 'slippage_ticks', 1)
        
        # Create and run backtest engine
        engine = BacktestEngine(
            strategy=self,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            resolution=resolution,
            commission_pct=commission_pct,
            slippage_ticks=slippage_ticks,
            jwt_token=jwt_token,
            account_id=self._account_id or "user@local",
        )
        
        self._backtest_engine = engine
        
        return engine.run()
    
    def _subscribe_symbols(self, symbols: List[str]) -> None:
        """Subscribe to symbol data streams."""
        for symbol_name in symbols:
            if not self._context:
                continue
            symbol = self._context.add_symbol(symbol_name)
            
            # Load initial data
            if self._client:
                info = self._client.market_data.get_product_info(symbol_name)
                if info:
                    symbol.update_from_info(info)
                
                stat = self._client.market_data.get_product_stat(symbol_name)
                if stat:
                    symbol.update_from_stat(stat)
                
                # Load historical bars
                from datetime import datetime, timedelta
                end = datetime.now()
                start = end - timedelta(days=30)
                candles = self._client.market_data.get_daily_candles(symbol_name, start, end)
                
                bars = [Bar.from_candle(c, symbol_name) for c in candles]
                symbol.bars.load(bars)
            
            # Subscribe to real-time updates
            if self._client and self._mode == RunMode.LIVE:
                self._client.stream.subscribe_product_stat(
                    symbol_name,
                    lambda stat, s=symbol: self._handle_stat_update(s, stat)
                )
                
                self._client.stream.subscribe_depth(
                    symbol_name,
                    lambda depth, s=symbol: self._handle_depth_update(s, depth)
                )
            
            self.logger.info(f"Subscribed to {symbol_name}")
    
    def _handle_stat_update(self, symbol: Symbol, stat: Any) -> None:
        """Handle product stat update."""
        symbol.update_from_stat(stat)
        if self._context:
            self._context.update_prices()
        self.on_tick(symbol)
        
        # Check risk limits
        if self._risk_manager:
            self._risk_manager.check_positions()
    
    def _handle_depth_update(self, symbol: Symbol, depth: Any) -> None:
        """Handle depth update."""
        symbol.update_from_depth(depth)
        self.on_depth(symbol)
    
    def _handle_bar_update(self, symbol: Symbol, bar: Bar) -> None:
        """Handle new bar."""
        symbol.bars.add(bar)
        self.logger.bar(symbol.name, bar.open, bar.high, bar.low, bar.close, bar.volume)
        self.on_bar(bar)
    
    async def _on_stream_connect(self) -> None:
        """Handle stream connection."""
        self.logger.info("Stream connected")
    
    async def _on_stream_disconnect(self) -> None:
        """Handle stream disconnection."""
        self.logger.warning("Stream disconnected")
