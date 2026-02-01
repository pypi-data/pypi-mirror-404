"""
Type definitions for Vero Algo SDK.

Re-exports types from sub-modules for backward compatibility.
"""

from .enums import OrderSide, OrderType, OrderStatus, AlgoStatus
from .orders import (
    PersistenceInfo,
    NewOrderRequest,
    CancelOrderRequest,
    OrderData,
    OrderResponse,
    Trade,
)
from .market_data import (
    Candle,
    PriceLevel,
    ProductMaster,
    MarginRatio,
    ProductInfo,
    ProductStat,
    Depth,
)
from .account import Account
from .streaming import SubscribeData, StreamMessage
from .settings import StrategyInitSettings

__all__ = [
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
    "ProductInfo",
    "ProductStat",
    "Depth",
    # Account
    "Account",
    # Streaming
    "SubscribeData",
    "StreamMessage",
    "StrategyInitSettings",
]
