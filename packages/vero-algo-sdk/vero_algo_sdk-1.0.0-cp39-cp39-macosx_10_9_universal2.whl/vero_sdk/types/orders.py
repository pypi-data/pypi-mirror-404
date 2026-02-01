from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class PersistenceInfo:
    """Persistence information for algo orders."""
    algo_id: str = ""
    position_id: str = ""
    user_id: str = ""
    cap_price: float = 0.0
    stoploss_pct: float = 0.0
    trailing: bool = False
    best_trail_price: float = 0.0
    state_str: str = ""
    persis_state: str = ""


@dataclass
class NewOrderRequest:
    """Request to place a new order."""
    ref_order_id: str
    account_id: str
    symbol: str
    order_side: str  # "B" or "S"
    price: float
    qty: int
    order_type: str = "LO"  # LO, MTL, ATO, ATC
    persistence: Optional[PersistenceInfo] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API request dict."""
        data: Dict[str, Any] = {
            "refOrderID": self.ref_order_id,
            "accountID": self.account_id,
            "symbol": self.symbol,
            "orderSide": self.order_side,
            "price": self.price,
            "qty": self.qty,
            "orderType": self.order_type,
        }
        if self.persistence:
            data["persistence"] = {
                "algoID": self.persistence.algo_id,
                "positionID": self.persistence.position_id,
                "userID": self.persistence.user_id,
                "capPrice": self.persistence.cap_price,
                "stoplossPct": self.persistence.stoploss_pct,
                "trailing": self.persistence.trailing,
                "bestTrailPrice": self.persistence.best_trail_price,
                "stateStr": self.persistence.state_str,
                "persisState": self.persistence.persis_state,
            }
        return data


@dataclass
class CancelOrderRequest:
    """Request to cancel an order."""
    order_id: str
    account_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API request dict."""
        return {
            "orderID": self.order_id,
            "accountID": self.account_id,
        }




@dataclass
class OrderData:
    """Order data returned from API."""
    order_id: str
    account_id: str
    symbol: str
    order_side: str
    order_status: str
    order_type: str
    order_entry_price: float
    order_entry_qty: int
    order_current_price: float
    order_current_qty: int
    filled_qty: int
    avg_fill_price: float
    cancelled_qty: int
    unix_utc_time_ms: int
    create_unix_utc_time_ms: int
    ref_order_id: str = ""
    internal_order_id: str = ""
    order_text: str = ""
    persis_state: str = ""
    bracket_order_id: str = ""
    special_order_type: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderData":
        """Create from API response dict."""
        return cls(
            order_id=data.get("orderID", ""),
            ref_order_id=data.get("refOrderID", ""),
            internal_order_id=data.get("internalOrderID", ""),
            account_id=data.get("accountID", ""),
            symbol=data.get("symbol", ""),
            order_side=data.get("orderSide", ""),
            order_status=data.get("orderStatus", ""),
            order_type=data.get("orderType", ""),
            order_entry_price=data.get("orderEntryPrice", 0),
            order_entry_qty=data.get("orderEntryQty", 0),
            order_current_price=data.get("orderCurrentPrice", 0),
            order_current_qty=data.get("orderCurrentQty", 0),
            filled_qty=data.get("filledQty", 0),
            avg_fill_price=data.get("avgFillPrice", 0),
            cancelled_qty=data.get("cancelledQty", 0),
            order_text=data.get("orderText", ""),
            unix_utc_time_ms=data.get("unixUTCTimeMs", 0),
            create_unix_utc_time_ms=data.get("createunixUTCTimeMs", 0),
            persis_state=data.get("persisState", ""),
            bracket_order_id=data.get("bracketOrderId", ""),
            special_order_type=data.get("specialOrderType", ""),
        )


@dataclass
class OrderResponse:
    """Response from order API calls."""
    success: bool
    message: str
    data: Optional[Any] = None
    status: int = 200
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderResponse":
        """Create from API response dict."""
        return cls(
            success=data.get("status", 500) < 400,
            message=data.get("message", ""),
            data=data.get("data"),
            status=data.get("status", 200),
        )


@dataclass
class Trade:
    """Trade execution data."""
    trade_id: str
    order_id: str
    ref_order_id: str
    external_order_id: str
    account_id: str
    symbol: str
    order_side: str
    traded_price: float
    traded_qty: int
    unix_utc_time_ms: int
    algo_id: str = ""
    algo_instance_id: str = "" # Matches algoInstanceID
    position_id: str = ""
    persis_state: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trade":
        """Create from API response dict."""
        return cls(
            trade_id=data.get("tradeID", ""),
            order_id=data.get("orderID", ""),
            ref_order_id=data.get("refOrderID", ""),
            external_order_id=data.get("externalOrderID", ""),
            account_id=data.get("accountID", ""),
            symbol=data.get("symbol", ""),
            order_side=data.get("orderSide", ""),
            traded_price=data.get("tradedPrice", 0),
            traded_qty=data.get("tradedQty", 0),
            unix_utc_time_ms=int(data.get("unixUTCTimeMs", data.get("createTime", 0)) or 0),
            algo_id=str(data.get("algoID", data.get("algoInstanceID", "")) or ""), # Map instance ID if simple ID missing
            algo_instance_id=data.get("algoInstanceID", ""),
            position_id=data.get("positionID", ""),
            persis_state=data.get("persisState", ""),
        )
