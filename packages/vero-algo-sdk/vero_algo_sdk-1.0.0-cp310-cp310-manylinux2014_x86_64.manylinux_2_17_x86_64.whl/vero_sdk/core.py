"""
Vero Core Runner.

Provides the unified entry point for running trading algorithms in either 
LIVE or BACKTEST mode, abstracting away the underlying engine details.
"""

import time
import logging
import asyncio
from typing import Callable, Optional, List, Dict, Any, Union
from datetime import datetime

from .client import VeroClient
from .backtest.client import BacktestClient
from .config import VeroConfig
from .types import OrderSide, OrderType, AlgoStatus
from .backtest.settings import BacktestSettings
from .backtest.engine import BacktestEngine
from .strategy import Symbol, Bar, Position, RunMode
from .utils.logging_config import setup_logging
from .types import StrategyInitSettings

logger = logging.getLogger("vero")

# from .backtest.client import BacktestClient

class Vero:
    """
    Main entry point for Vero Algo SDK.
    
    Handles initialization and execution of strategies in Live or Backtest mode.
    """
    
    _instance = None
    
    def __init__(
        self, 
        mode: Union[RunMode, str] = RunMode.BACKTEST,
        symbol: str = "VN30F2401",
        # Live Settings
        jwt_token: str = "",
        # Strategy Init Settings (Backtest/Live)
        strategy_settings: Optional[StrategyInitSettings] = None,
        api_port: Optional[int] = None,
        # Config
        board: str = "G1"
    ):
        self._check_dependencies()
        self.mode = RunMode(mode) if isinstance(mode, str) else mode
        self.symbol = symbol
        self.jwt_token = jwt_token
        self.api_port = api_port
        self.board = board
        
        # Configure Strategy Settings
        self.strategy_settings = strategy_settings or StrategyInitSettings.default()
        
        # Unify Settings Global
        self.initial_capital = self.strategy_settings.initial_capital
        self.timeframe = self.strategy_settings.timeframe
        
        # Backwards compatibility / Mapping to legacy BacktestSettings if needed internaly
        # OR just use strategy_settings for everything.
        # For now, let's map to BacktestSettings if in Backtest mode
        
        self.backtest_settings: Optional[BacktestSettings] = None
        if self.mode == RunMode.BACKTEST:
             # Resolve Timeframe
            from .backtest.settings import Timeframe
            tf = self.strategy_settings.timeframe
            if isinstance(tf, str):
                try:
                    tf = Timeframe(tf)
                except ValueError:
                    if tf == "1 Day": tf = Timeframe.DAY_1
                    elif tf == "1 Hour": tf = Timeframe.HOUR_1
                    elif tf == "1 Minute" or tf == "1m": tf = Timeframe.MINUTE_1
                    else: tf = Timeframe.DAY_1
            
            # Use settings dates or default
            if self.strategy_settings.from_date and self.strategy_settings.to_date:
                self.backtest_settings = BacktestSettings(
                    symbols=self.strategy_settings.symbols or [symbol],
                    initial_capital=self.strategy_settings.initial_capital,
                    from_date=self.strategy_settings.from_date,
                    to_date=self.strategy_settings.to_date,
                    timeframe=tf
                )
            else:
                 self.backtest_settings = BacktestSettings.quick_1y(
                    symbols=self.strategy_settings.symbols or [symbol],
                    capital=self.strategy_settings.initial_capital,
                    timeframe=tf
                )

        
        # Runtime components
        self.client: Optional[Union[VeroClient, BacktestClient]] = None
        self.backtest_engine: Optional[BacktestEngine] = None
        self.api_server = None
        self._loop = None
        
        # Resolve API Port: Argument > Config
        # Note: self.client isn't initialized yet, but we can check default config logic if needed
        # Use a temporary config load if not passed, or assume config is loaded later.
        # However, VeroConfig usually handles env vars. 
        # Let's instantiate a default config to check env if not provided.
        from .config import VeroConfig
        cfg = VeroConfig()
        self.api_port = api_port if api_port is not None else cfg.control_api_port
        
        setup_logging()
        # PnL State
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
        self.avg_entry_price = 0.0
        self.position_qty = 0
        
        # API State
        self._status = AlgoStatus.IDLE
        self._progress = 0.0
        self._stop_event = asyncio.Event() # For clean stopping
        self._close_positions_on_stop = False
        self._latest_report = None
        # User Identity
        # Automated extraction removed per user request
        pass

    def _check_dependencies(self):
        """Check if required packages are installed."""
        required = [
            "requests",
            "websocket", # websocket-client
            "dateutil", 
            "centrifuge", # centrifuge-python
            "backtrader",
            "talipp"
        ]
        missing = []
        import importlib.util
        for pkg in required:
            import_name = pkg
            if pkg == "websocket": import_name = "websocket" 
            if pkg == "centrifuge": import_name = "centrifuge"
            
            if not importlib.util.find_spec(import_name):
                 missing.append(pkg)
        
        if missing:
             logger.warning(f"SDK dependencies missing: {', '.join(missing)}")
             print(f"WARNING: The following SDK dependencies appear to be missing: {', '.join(missing)}")
             print("Please run: pip install .")

    @classmethod
    def init(cls, *args, **kwargs):
        """Global initialization."""
        return cls(*args, **kwargs)

    async def run(
        self, 
        on_candle=None, 
        on_order=None, 
        on_trade=None,
        on_market_trade=None, # Public market trades
        on_depth=None,
        # on_tick removed (duplicate of on_market_trade)
        # on_depth_update removed (duplicate/unused)
        on_progress=None
    ):
        """Run the strategy asynchronously."""
        logger.info(f"Starting Vero in {self.mode.value} mode for {self.symbol}")
        self._status = AlgoStatus.RUNNING
        self._progress = 0.0
        self._stop_event.clear()
        
        # Capture loop for thread-safe operations
        self._loop = asyncio.get_running_loop()
        
        # Start API Server if configured
        if self.api_port:
            from .api_server import APIServer
            self.api_server = APIServer(self, self.api_port)
            self.api_server.start()
        
        try:
            if self.mode == RunMode.LIVE:
                await self._run_live(on_candle, on_order, on_trade, on_market_trade, on_depth)
            else:
                await self._run_backtest(on_candle, on_order, on_trade, on_progress)
        except Exception as e:
            self._status = AlgoStatus.ERROR
            logger.error(f"Runtime error: {e}")
            raise
        finally:
            if self._status != AlgoStatus.ERROR:
                self._status = AlgoStatus.STOPPED
            
            # Stop API Server
            if self.api_server:
                self.api_server.shutdown()

    def run_log(self, message: str):
        """Log message from runner components."""
        logger.info(message)

    async def _run_live(
        self, 
        on_candle, 
        on_order, 
        on_trade,
        on_market_trade=None,
        on_depth=None
    ):
        """Execute live trading loop."""
        if not self.jwt_token:
            raise ValueError("jwt_token required for LIVE mode")
            
        # Initialize client with board config
        config = VeroConfig(debug=False, board=self.board)
        self.client = VeroClient(config=config)
        
        self.client.set_jwt_token(self.jwt_token)
        account_id = self.strategy_settings.account_id or "user"

        logger.info(f"Connected to Vero Live Server")
        
        await self.client.stream.connect()
        await asyncio.sleep(2)
        
        # Restore Account Subscriptions
        if on_order:
            await self.client.stream.subscribe_order_execution_report(account_id, on_order)
        if on_trade:
             await self.client.stream.subscribe_algo_master(account_id, on_trade)

        # Append board suffix if needed for Market Data channels
        sub_symbol = self.symbol
        if self.board and not sub_symbol.endswith(f"-{self.board}"):
            sub_symbol = f"{sub_symbol}-{self.board}"


        if on_depth:
             await self.client.stream.subscribe_depth(sub_symbol, on_depth)
        if on_market_trade:
             await self.client.stream.subscribe_market_trades(sub_symbol, on_market_trade)
               
        logger.info(f"Subscribing to {self.symbol}...")
        
        # Determine sampling requirements
        target_tf = "1m"
        # Always use the unified timeframe setting
        tf = self.timeframe
        if str(tf).endswith("MINUTE_1") or tf == "1m": target_tf = "1m"
        elif str(tf).endswith("DAY_1") or tf == "1d": target_tf = "1d"
        else: target_tf = str(tf)
            
        NATIVE_RESOLUTIONS = {"1m": 60, "1d": 86400}
        
        if target_tf in NATIVE_RESOLUTIONS:
            if on_candle:
                await self.client.stream.subscribe_candles(
                    symbol=self.symbol,
                    resolution=NATIVE_RESOLUTIONS[target_tf],
                    callback=on_candle
                )
        else:
            logger.info(f"Timeframe {target_tf} not native. Subscribing to 1m and aggregating (implied).")
            if on_candle:
                 await self.client.stream.subscribe_candles(
                    symbol=self.symbol,
                    resolution=60, 
                    callback=on_candle
                )
        
        logger.info("Running... Press Ctrl+C to stop.")
        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            logger.info("Stopping...")
            # self.client.logout() removed

    def get_status(self) -> str:
        return self._status.value

    def get_progress(self) -> float:
        return self._progress

    async def stop(self, close_positions: bool = False):
        if self._status != AlgoStatus.RUNNING:
            logger.info("Strategy is not running (already stopped or idle).")
            return

        self._status = AlgoStatus.STOPPING
        logger.info(f"Signal received to stop strategy (Close Positions: {close_positions})")
        self._close_positions_on_stop = close_positions
        self._stop_event.set()

    def get_algo_stat_report(self) -> Dict[str, Any]:
        """Get current strategy performance report."""
        if self.mode == RunMode.BACKTEST:
             # Assuming result is generated at end, checking if available
             if self._latest_report:
                 return self._latest_report.to_dict()
             return {}
            
        elif self.mode == RunMode.LIVE:
            # Construct live metrics
            total_pnl = self.realized_pnl + self.unrealized_pnl
            return {
                "status": self._status.value,
                "net_profit": total_pnl,
                "realized_pnl": self.realized_pnl,
                "unrealized_pnl": self.unrealized_pnl,
                "current_position": self.position_qty,
                "avg_entry_price": self.avg_entry_price,
            }
        return {}

    def get_orders(self, account_id: Optional[str] = None, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get orders from the running strategy.
        
        Args:
            account_id: Optional filter by account ID
            symbol: Optional filter by symbol
            
        Returns:
            List of order dictionaries
        """
        if self.mode == RunMode.LIVE and self.client:
            try:
                orders = self.client.orders.get_orders(
                    account_id=account_id,
                    symbol=symbol
                )
                return [o.to_dict() if hasattr(o, 'to_dict') else vars(o) for o in orders]
            except Exception as e:
                logger.warning(f"Failed to fetch orders: {e}")
                return []
        
        # Backtest mode - return from engine if available
        if self.backtest_engine and hasattr(self.backtest_engine, 'strategy'):
            strategy = self.backtest_engine.strategy
            if hasattr(strategy, '_context') and strategy._context:
                # Get positions (open orders/positions)
                positions = []
                for pos in strategy._context.positions.values():
                    positions.append({
                        "id": pos.id,
                        "symbol": pos.symbol,
                        "side": "B" if pos.is_long else "S",
                        "qty": pos.quantity,
                        "entry_price": pos.entry_price,
                        "status": "OPEN"
                    })
                return positions
        return []

    def get_trades(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get trades from the running strategy.
        
        Args:
            account_id: Optional filter by account ID
            
        Returns:
            List of trade dictionaries
        """
        if self.mode == RunMode.LIVE and self.client:
            try:
                trades = self.client.orders.get_trades(account_id=account_id)
                return [t.to_dict() if hasattr(t, 'to_dict') else vars(t) for t in trades]
            except Exception as e:
                logger.warning(f"Failed to fetch trades: {e}")
                return []
        
        # Backtest mode - return closed positions as trades
        if self._latest_report and hasattr(self._latest_report, 'trades'):
            trades = self._latest_report.trades
            return [
                {
                    "id": t.id if hasattr(t, 'id') else str(i),
                    "symbol": t.symbol,
                    "side": "B" if t.side.value == "long" else "S",
                    "qty": t.quantity,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "pnl": t.pnl,
                    "entry_time": str(t.entry_time),
                    "exit_time": str(t.exit_time),
                }
                for i, t in enumerate(trades)
            ]
        
        # Check engine's strategy context history
        if self.backtest_engine and hasattr(self.backtest_engine, 'strategy'):
            strategy = self.backtest_engine.strategy
            if hasattr(strategy, '_context') and strategy._context:
                return [
                    {
                        "id": t.id if hasattr(t, 'id') else str(i),
                        "symbol": t.symbol,
                        "side": "B" if t.side.value == "long" else "S",
                        "qty": t.quantity,
                        "entry_price": t.entry_price,
                        "exit_price": t.exit_price,
                        "pnl": t.pnl,
                        "entry_time": str(t.entry_time),
                        "exit_time": str(t.exit_time),
                    }
                    for i, t in enumerate(strategy._context.history)
                ]
        return []

    def get_logs(self, limit: int = 100) -> List[str]:
        """Get recent log entries from the log file.
        
        Args:
            limit: Maximum number of lines to return (default 100, max 1000)
            
        Returns:
            List of log lines (most recent last)
        """
        import os
        from .utils.defaults import DEFAULT_LOG_FILE
        
        limit = min(limit, 1000)  # Cap at 1000
        
        log_file = DEFAULT_LOG_FILE
        if not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Read all lines and return last N
                lines = f.readlines()
                return [line.rstrip() for line in lines[-limit:]]
        except Exception as e:
            logger.warning(f"Failed to read log file: {e}")
            return []
    
    async def _run_backtest(self, on_candle, on_order, on_trade, on_progress=None):
        """Run backtest simulation using Internal Engine."""
        logger.info("Initializing backtest...")
        
        # Inject Backtest Client
        self.client = BacktestClient(self)
        
        # Ensure backtest settings are present
        if not self.backtest_settings:
            logger.error("No backtest settings provided")
            return

        # Initialize engine if not already done
        if not self.backtest_engine:
            from .strategy.base import Strategy
            from .backtest.engine import BacktestEngine
            from .config import TimeResolution
            
            # Check if on_candle is actually a Strategy instance
            if isinstance(on_candle, Strategy):
                strategy = on_candle
            else:
                # Create a wrapper strategy that delegates to callbacks
                class CallbackStrategy(Strategy):
                    def on_start(self2):
                        pass
                        
                    def on_stop(self2):
                        pass
                        
                    async def on_bar(self2, bar): # type: ignore
                        if on_candle:
                            if asyncio.iscoroutinefunction(on_candle):
                                await on_candle(bar)
                            else:
                                on_candle(bar)
                            
                strategy = CallbackStrategy()
                strategy.name = "UserStrategy"
            
            # Map resolution
            tf = self.backtest_settings.timeframe
            resolution = TimeResolution.DAY_1
            if isinstance(tf, str):
                if tf == "1m": resolution = TimeResolution.MINUTE_1
                elif tf == "1h": resolution = TimeResolution.HOUR_1
            
            self.backtest_engine = BacktestEngine(
                strategy=strategy,
                symbols=self.backtest_settings.symbols,
                start_date=str(self.backtest_settings.from_date or ""),
                end_date=str(self.backtest_settings.to_date or ""),
                initial_capital=self.backtest_settings.initial_capital,
                resolution=resolution,
                jwt_token=self.jwt_token,
                account_id=self.strategy_settings.account_id or "user@local"
            )
            
        logger.info("Running backtest simulation...")
        
        def internal_progress(p):
            self._progress = p
            if on_progress:
                on_progress(p)
                
        result = await self.backtest_engine.run(on_progress=internal_progress)
        self._latest_report = result
        
        # Display results
        result.print_report()
        
        # Keep alive for API retrieval if configured
        if self.api_port:
            logger.info("Backtest complete. API Server running. Waiting for stop signal...")
            while not self._stop_event.is_set():
                await asyncio.sleep(1)
