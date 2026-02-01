from enum import Enum

class OrderSide(str, Enum):
    """Order side - Buy or Sell."""
    BUY = "B"
    SELL = "S"


class OrderType(str, Enum):
    """Order types supported by the platform."""
    LIMIT = "LO"  # Limit Order
    MARKET_TO_LIMIT = "MTL"  # Market to Limit
    AT_THE_OPENING = "ATO"  # At The Opening
    AT_THE_CLOSE = "ATC"  # At The Close


class OrderStatus(str, Enum):
    """Order status values."""
    NEW = "New"
    PARTIALLY_FILLED = "PartiallyFilled"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    PENDING_NEW = "PendingNew"
    PENDING_CANCEL = "PendingCancel"
    EXPIRED = "Expired"


class AlgoStatus(str, Enum):
    """Execution status of the strategy."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
