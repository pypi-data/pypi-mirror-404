"""
Vero Algo SDK for Python

A Python SDK for the Vero Algo trading platform with authentication,
order management, streaming, market data, and algorithmic trading capabilities.
"""

from .client import VeroClient
from .config import VeroConfig
from .features.orders import OrderService
from .features.market_data import MarketDataService
from .features.streaming import VeroStream
from .utils.defaults import (
    DEFAULT_BACKEND_SERVER,
    DEFAULT_AUTH_SERVER,
    DEFAULT_MICRO_API_SERVER,
    DEFAULT_STREAMING_WS,
)
from .utils.logging_config import setup_logging, get_logger
from .types import (
    OrderSide,
    OrderType,
    OrderStatus,
    NewOrderRequest,
    CancelOrderRequest,
    OrderData,
    OrderResponse,
    Trade,
    Candle,
    ProductMaster,
    PriceLevel,
    AlgoStatus,
    PersistenceInfo,
    MarginRatio,
    Account,
    SubscribeData,
    StreamMessage,
    StrategyInitSettings,
)

# Strategy framework
from .strategy import Strategy, RunMode, TradingContext, Position, PositionSide, Symbol, Bars

# Risk management
from .risk import RiskManager, RiskSettings

# Backtesting
from .backtest import BacktestEngine, BacktestResult, PerformanceReport, BacktestSettings, DatePreset, Timeframe

from .core import Vero

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"
__all__ = [
    # Core
    "VeroClient",
    "VeroConfig",
    "OrderService",
    "MarketDataService",
    "VeroStream",
    # Enums
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "AlgoStatus",
    # Orders
    "PersistenceInfo",
    "NewOrderRequest",
    "CancelOrderRequest",
    "OrderData",
    "OrderResponse",
    "Trade",
    # Market Data
    "Candle",
    "PriceLevel",
    "ProductMaster",
    "MarginRatio",
    # Account
    "Account",
    # Streaming
    "SubscribeData",
    "StreamMessage",
    # Settings
    "StrategyInitSettings",
    # Strategy
    "Strategy",
    "RunMode",
    "TradingContext",
    "Position",
    "PositionSide",
    "Symbol",
    "Bars",
    # Risk
    "RiskManager",
    "RiskSettings",
    # Backtest
    "BacktestEngine",
    "BacktestResult",
    "PerformanceReport",
    "BacktestSettings",
    "DatePreset",
    "Timeframe",
    "Vero",
    # Logging
    "setup_logging",
    "get_logger",
]
