from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Account:
    """User account / portfolio data."""
    id: str  # Unique ID
    account_id: str
    account_name: str = ""
    total_equity: float = 0
    credit: float = 0
    maintenance_margin: float = 0
    temp_maintenance_margin: float = 0
    total_realized_pnl: float = 0
    total_unrealized_pnl: float = 0
    trading_power: float = 0
    cross_margin: bool = False
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        """Create from API response dict."""
        return cls(
            id=str(data.get("id", "") or ""),
            account_id=str(data.get("accountId", data.get("accountID", "")) or ""),
            account_name=str(data.get("accountName", "") or ""),
            total_equity=float(data.get("totalEquity", data.get("equity", 0)) or 0),
            credit=float(data.get("credit", 0) or 0),
            maintenance_margin=float(data.get("maintenanceMargin", 0) or 0),
            temp_maintenance_margin=float(data.get("tempMaintenanceMargin", 0) or 0),
            total_realized_pnl=float(data.get("totalRealizedPnl", data.get("realizedPnl", 0)) or 0),
            total_unrealized_pnl=float(data.get("totalUnrealizedPnl", data.get("unrealizedPnl", 0)) or 0),
            trading_power=float(data.get("tradingPower", 0) or 0),
            cross_margin=bool(data.get("crossMargin", False)),
        )
