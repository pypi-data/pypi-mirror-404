from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Candle:
    """OHLCV candle data."""
    time: int  # Unix timestamp in milliseconds
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Candle":
        """Create from API response dict."""
        return cls(
            time=int(data.get("unixTime", 0)),
            open=float(data.get("open", 0)),
            high=float(data.get("high", 0)),
            low=float(data.get("low", 0)),
            close=float(data.get("close", 0)),
            volume=float(data.get("volume", 0)),
        )


@dataclass
class PriceLevel:
    """Price level in order book depth."""
    price: float
    qty: int
    num_orders: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PriceLevel":
        """Create from API response dict."""
        return cls(
            price=float(data.get("price", 0)),
            qty=int(data.get("qty", 0)),
            num_orders=int(data.get("numOrders", 0)),
        )


@dataclass
class Depth:
    """Market depth / order book data."""
    symbol: str
    bid_price_depth: List[PriceLevel] = field(default_factory=list)
    ask_price_depth: List[PriceLevel] = field(default_factory=list)
    seq: int = 0
    board_id: str = "G1"
    time: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Depth":
        """Create from API response dict."""
        bid_depth = [PriceLevel.from_dict(p) for p in data.get("bidPriceDepth", [])]
        ask_depth = [PriceLevel.from_dict(p) for p in data.get("askPriceDepth", [])]
        return cls(
            symbol=data.get("symbol", ""),
            bid_price_depth=bid_depth,
            ask_price_depth=ask_depth,
            seq=data.get("seq", 0),
            board_id=data.get("boardID", "G1"),
            time=data.get("time", 0),
        )


@dataclass
class ProductInfo:
    """Product/instrument basic information."""
    symbol: str
    exchange: str = ""
    security_type: str = ""
    lot_size: int = 1
    tick_size: float = 0.01
    currency: str = "VND"
    isin: str = ""
    trading_session: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductInfo":
        """Create from API response dict."""
        return cls(
            symbol=data.get("symbol", ""),
            exchange=data.get("exchange", ""),
            security_type=data.get("securityType", ""),
            lot_size=data.get("lotSize", 1),
            tick_size=data.get("tickSize", 0.01),
            currency=data.get("currency", "VND"),
            isin=data.get("isin", ""),
            trading_session=data.get("tradingSession", ""),
        )


@dataclass
class ProductStat:
    """Product statistics / market data."""
    symbol: str
    last_price: float = 0
    last_qty: int = 0
    total_traded_qty: int = 0
    total_traded_value: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0
    ref_price: float = 0
    ceiling_price: float = 0
    floor_price: float = 0
    change: float = 0
    change_pct: float = 0
    bid_price: float = 0
    bid_qty: int = 0
    ask_price: float = 0
    ask_qty: int = 0
    point_value: float = 1.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductStat":
        """Create from API response dict."""
        return cls(
            symbol=data.get("symbol", ""),
            last_price=data.get("lsPrc", 0),
            last_qty=data.get("lsQty", 0),
            total_traded_qty=data.get("ttQty", 0),
            total_traded_value=data.get("ttVal", 0),
            open_price=data.get("opnPrc", 0),
            high_price=data.get("hiPrc", 0),
            low_price=data.get("loPrc", 0),
            close_price=data.get("clsPrc", 0),
            ref_price=data.get("refPrc", 0),
            ceiling_price=data.get("ceiPrc", 0),
            floor_price=data.get("flrPrc", 0),
            change=data.get("chg", 0),
            change_pct=data.get("chgPct", 0),
            bid_price=data.get("bidPrc", 0),
            bid_qty=data.get("bidQty", 0),
            ask_price=data.get("askPrc", 0),
            ask_qty=data.get("askQty", 0),
            point_value=float(data.get("pointValue", 1.0)),
        )

@dataclass
class MarginRatio:
    """Margin ratio information."""
    symbol: str
    product_group: str
    margin_ratio: float
    margin_call_rate: float
    force_close_rate: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarginRatio":
        """Create from API response dict."""
        return cls(
            symbol=data.get("symbol", ""),
            product_group=data.get("productGroup", ""),
            margin_ratio=float(data.get("marginRatio", 1.0)),
            margin_call_rate=float(data.get("marginCallRate", 0.0)),
            force_close_rate=float(data.get("forceCloseRate", 0.0)),
        )


@dataclass
class ProductMaster:
    """Complete product master data."""
    symbol: str
    company_name: str = ""
    industry_name: str = ""
    logo_id: str = ""
    sector_lvl1: str = ""
    sector_lvl2: str = ""
    sector_lvl3: str = ""
    info: Optional[ProductInfo] = None
    stat: Optional[ProductStat] = None
    depth: Optional[Depth] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductMaster":
        """Create from API response dict."""
        info = ProductInfo.from_dict(data.get("info", {})) if data.get("info") else None
        stat = ProductStat.from_dict(data.get("stat", {})) if data.get("stat") else None
        depth = Depth.from_dict(data.get("depth", {})) if data.get("depth") else None
        
        return cls(
            symbol=data.get("symbol", ""),
            company_name=data.get("companyname", ""),
            industry_name=data.get("industryname", ""),
            logo_id=data.get("logoId", ""),
            sector_lvl1=data.get("sectorLvl1", ""),
            sector_lvl2=data.get("sectorLvl2", ""),
            sector_lvl3=data.get("sectorLvl3", ""),
            info=info,
            stat=stat,
            depth=depth,
        )
