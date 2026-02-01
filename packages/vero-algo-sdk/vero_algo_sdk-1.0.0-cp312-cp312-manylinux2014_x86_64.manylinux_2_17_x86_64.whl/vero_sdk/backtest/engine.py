"""
Backtest simulation engine for Vero Algo SDK.

Runs strategy against historical data and produces performance report.
"""

from dataclasses import dataclass, field
import asyncio
from typing import List, Optional, Any, TYPE_CHECKING, Callable
from datetime import datetime, timedelta

from .metrics import BacktestMetrics, calculate_metrics
from .report import PerformanceReport
from ..strategy.symbol import Bar, Bars
from ..strategy.position import ClosedPosition, PositionSide
from ..strategy.context import TradingContext
from ..utils.logging_config import get_logger
from ..utils.defaults import DEFAULT_MICRO_API_SERVER, DEFAULT_COMMISSION_PCT, DEFAULT_SLIPPAGE_TICKS
from ..config import TimeResolution

if TYPE_CHECKING:
    from ..strategy.base import Strategy

logger = get_logger("backtest")


@dataclass
class BacktestResult:
    """Result of a backtest run."""
    
    strategy_name: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = 0
    final_equity: float = 0
    
    # Performance data
    metrics: BacktestMetrics = field(default_factory=BacktestMetrics)
    report: PerformanceReport = field(default_factory=PerformanceReport)
    
    # Time series
    equity_curve: List[float] = field(default_factory=list)
    equity_dates: List[datetime] = field(default_factory=list)
    
    # Trade history
    trades: List[ClosedPosition] = field(default_factory=list)
    
    def print_report(self) -> None:
        """Print performance report."""
        self.report.print_report()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.report.to_dict()


class BacktestEngine:
    """
    Backtesting simulation engine.
    
    Runs a strategy against historical bar data and produces
    performance metrics and trade history.
    """
    
    def __init__(
        self,
        strategy: "Strategy",
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 100000,
        resolution: int = TimeResolution.DAY_1,
        commission_pct: float = DEFAULT_COMMISSION_PCT,
        slippage_ticks: int = DEFAULT_SLIPPAGE_TICKS,
        jwt_token: str = "",
        account_id: str = "user",
    ):
        """
        Initialize BacktestEngine.
        
        Args:
            strategy: Strategy instance to test
            symbols: List of symbols to load
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_capital: Starting capital
            resolution: Bar resolution in seconds
            commission_pct: Commission percentage per trade
            slippage_ticks: Slippage in ticks per trade
            jwt_token: JWT token for API data fetching
            account_id: Account ID for the simulation
        """
        self.strategy = strategy
        self.symbols = symbols
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.initial_capital = initial_capital
        self.resolution = resolution
        self.commission_pct = commission_pct
        self.slippage_ticks = slippage_ticks
        self.jwt_token = jwt_token
        self.account_id = account_id
        
        # Historical data
        self._bars_data: dict = {}  # symbol -> list of Bar
        self._current_bar_index = 0
        
        # Results tracking
        self._equity_curve: List[float] = []
        self._equity_dates: List[datetime] = []
        self._closed_positions: List[ClosedPosition] = []
    

    async def run(self, on_progress: Optional[Callable[[float], None]] = None) -> BacktestResult:
        """
        Execute the backtest.
        
        Args:
            on_progress: Optional callback(float) for progress percentage (0.0 to 100.0)
            
        Returns:
            BacktestResult with all metrics and trade history
        """
        from ..features.market_data import MarketDataService
        from ..config import VeroConfig, DEFAULT_MICRO_API_SERVER
        
        logger.info(f"Starting backtest from {self.start_date.date()} to {self.end_date.date()}")
        logger.info(f"Initial capital: {self.initial_capital:,.0f}")
        logger.info(f"Symbols: {', '.join(self.symbols)}")
        
        # Initialize Services
        from ..utils.defaults import DEFAULT_AUTH_SERVER
        
        config = VeroConfig(
            micro_api_server=DEFAULT_MICRO_API_SERVER,
            auth_server=DEFAULT_AUTH_SERVER
        )
        
        # Authenticate if token provided
        if self.jwt_token:
            logger.info("Setting up auth for backtest data...")
            config.jwt_token = self.jwt_token
        
        market_data = MarketDataService(config)

        # Initialize context with strategy
        self.strategy._context = TradingContext(initial_capital=self.initial_capital)
        
        # Load Symbol Data (Master + Margin)
        for symbol in self.symbols:
            logger.info(f"Fetching Product Info for {symbol}...")
            sym_obj = self.strategy._context.add_symbol(symbol)
            
            # Fetch Master
            try:
                master = market_data.get_product_master(symbol)
                if master:
                    sym_obj.update_from_master(master)
                    logger.debug(f"Updated {symbol} master data: Tick={sym_obj.tick_size}, Lot={sym_obj.lot_size}")
            except Exception as e:
                logger.warning(f"Failed to fetch master for {symbol}: {e}")
                
            # Fetch Margin
            try:
                mr = market_data.get_margin_rate(symbol)
                sym_obj.margin_rate = mr
                logger.debug(f"Updated {symbol} Margin Rate: {mr}")
            except Exception:
                pass
                
            # Point Value Heuristic (since API doesn't provide it yet)
            if "VN30" in symbol or "41I" in symbol:
                sym_obj.point_value = 100000.0
            
        
        # Load historical data
        self._load_historical_data(market_data)
        
        if not self._bars_data:
            logger.error("No historical data loaded")
            return BacktestResult()
            
        # ... (rest of function)

        
        # Record initial equity
        self._equity_curve.append(self.initial_capital)
        self._equity_dates.append(self.start_date)
        
        # Call strategy on_start
        self.strategy._running = True
        if asyncio.iscoroutinefunction(self.strategy.on_start):
            await self.strategy.on_start()
        else:
            self.strategy.on_start()
        
        # Get the primary symbol for bar iteration
        primary_symbol = self.symbols[0]
        bars = self._bars_data.get(primary_symbol, [])
        
        if not bars:
            logger.error(f"No bars for primary symbol {primary_symbol}")
            return BacktestResult()
        
        logger.info(f"Processing {len(bars)} bars...")
        
        # Iterate through bars
        for i, bar in enumerate(bars):
            self._current_bar_index = i
            
            # Progress update
            if on_progress and i % 100 == 0:
                progress = (i / len(bars)) * 100.0
                if asyncio.iscoroutinefunction(on_progress):
                     await on_progress(progress)
                else:
                    on_progress(progress)
            
            # Update context time
            self.strategy._context.set_time(bar.time)
            
            # Update all symbol prices
            for symbol_name in self.symbols:
                symbol = self.strategy._context.get_symbol(symbol_name)
                if symbol and symbol_name in self._bars_data:
                    symbol_bars = self._bars_data[symbol_name]
                    if i < len(symbol_bars):
                        sym_bar = symbol_bars[i]
                        symbol.last_price = sym_bar.close
                        symbol.bid = sym_bar.close
                        symbol.ask = sym_bar.close
                        symbol.bars.add(sym_bar)
            
            # Update position prices
            self.strategy._context.update_prices()
            
            # Check risk limits and close positions if needed
            if self.strategy._risk_manager:
                positions_to_close = self.strategy._risk_manager.check_positions()
                for pos_id in positions_to_close:
                    pos = self.strategy._context.positions.get(pos_id)
                    if pos:
                        closed = self._close_position(pos)
                        if closed:
                            self._closed_positions.append(closed)
            
            # Call strategy on_bar for primary symbol
            if asyncio.iscoroutinefunction(self.strategy.on_bar):
                await self.strategy.on_bar(bar)
            else:
                self.strategy.on_bar(bar)
            
            # Record equity
            self._equity_curve.append(self.strategy._context.equity)
            self._equity_dates.append(bar.time)
        
        # Close any remaining positions at final price
        if on_progress:
            if asyncio.iscoroutinefunction(on_progress):
                await on_progress(100.0)
            else:
                on_progress(100.0)

        for pos in list(self.strategy._context.positions.values()):
            closed = self._close_position(pos)
            if closed:
                self._closed_positions.append(closed)
        
        # Call strategy on_stop
        self.strategy.on_stop()
        self.strategy._running = False
        
        # Calculate final metrics
        logger.info("Calculating metrics...")
        
        # Use history from context as it contains all closed positions (manual + risk + end of test)
        all_trades = self.strategy._context.history
        
        metrics = calculate_metrics(
            trades=all_trades,
            equity_curve=self._equity_curve,
            initial_capital=self.initial_capital,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        
        # Generate report
        report = PerformanceReport.from_backtest(
            strategy_name=self.strategy.name,
            start_date=self.start_date,
            end_date=self.end_date,
            metrics=metrics,
            equity_curve=self._equity_curve,
            equity_dates=self._equity_dates,
            closed_positions=all_trades,
        )
        
        # Create result
        result = BacktestResult(
            strategy_name=self.strategy.name,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=self.initial_capital,
            final_equity=self._equity_curve[-1] if self._equity_curve else self.initial_capital,
            metrics=metrics,
            report=report,
            equity_curve=self._equity_curve,
            equity_dates=self._equity_dates,
            trades=all_trades,
        )
        
        logger.info(f"Backtest complete. Net profit: {metrics.net_profit:,.2f} ({metrics.net_profit_pct:.2f}%)")
        logger.info(f"Total trades: {metrics.total_trades}, Win rate: {metrics.win_rate:.1f}%")
        
        return result
    
    def _load_historical_data(self, market_data) -> None:
        """Load historical bar data for all symbols."""
        # Reuse service
        
        start_ts = int(self.start_date.timestamp() * 1000)
        end_ts = int(self.end_date.timestamp() * 1000)
        
        for symbol in self.symbols:
            logger.info(f"Loading historical data for {symbol}...")
            
            try:
                candles = market_data.fetch_candles(
                    symbol=symbol,
                    resolution=self.resolution,
                    from_ts=start_ts,
                    to_ts=end_ts,
                )
                
                bars = [Bar.from_candle(c, symbol) for c in candles]
                self._bars_data[symbol] = bars
                
                logger.info(f"Loaded {len(bars)} bars for {symbol}")
                
                if not bars:
                    raise Exception(f"No historical data loaded for {symbol} within the specified date range.")
                
            except Exception as e:
                logger.error(f"Failed to load data for {symbol}: {e}")
                raise
    
    def _close_position(self, position) -> Optional[ClosedPosition]:
        """Close a position and apply commission/slippage."""
        if not self.strategy._context:
            return None
        symbol = self.strategy._context.get_symbol(position.symbol)
        if not symbol:
            return None
        
        exit_price = symbol.last_price
        
        # Apply slippage
        if position.is_long:
            exit_price -= self.slippage_ticks * symbol.tick_size
        else:
            exit_price += self.slippage_ticks * symbol.tick_size
        
        # Close in context
        if not self.strategy._context: return None
        closed = self.strategy._context.close_position(position.id, exit_price)
        
        if closed:
            # Apply commission
            commission = abs(closed.pnl) * self.commission_pct / 100
            closed.pnl -= commission
            
            # Update account
            if self.strategy._context:
                self.strategy._context._account.balance -= commission
            
            # Notify strategy
            self.strategy.on_position_closed(closed)
            
            # Track for risk manager
            if self.strategy._risk_manager:
                self.strategy._risk_manager.on_position_closed(closed.pnl)
        
        return closed
