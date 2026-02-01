"""
Market data service for Vero Algo SDK.

Provides access to OHLCV candles, product info, and price data.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import requests

from ..config import VeroConfig, TimeResolution
from ..types import Candle, ProductMaster


logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Market data service.
    
    Provides methods for fetching OHLCV candles, product information,
    and real-time price data.
    """
    
    def __init__(self, config: VeroConfig):
        """
        Initialize MarketDataService.
        
        Args:
            config: VeroConfig instance
        """
        self.config = config
        self._micro_api_url = config.micro_api_url
        self._rest_api_url = config.rest_api_url
    
    def _request(
        self,
        url: str,
        authenticated: bool = False
    ) -> Any:
        """Make API request."""
        headers = {}
        headers = {}
        if authenticated:
            if self.config.jwt_token:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config.jwt_token}",
                }
            else:
                logger.warning("Authenticated request to {url} missing JWT token")
        
        response = requests.get(url, headers=headers)
        
        if not response.ok:
            logger.error(f"Request failed: {response.status_code} {response.reason} | URL: {url} | Response: {response.text[:200]}")
            return None
        
        return response.json()
    
    def fetch_candles(
        self,
        symbol: str,
        resolution: int,
        from_ts: int,
        to_ts: int,
        divide_price: bool = False,
        count_back: Optional[int] = None,
    ) -> List[Candle]:
        """
        Fetch OHLCV candle data.
        
        Args:
            symbol: Trading symbol
            resolution: Time resolution in seconds (use TimeResolution constants)
            from_ts: Start time in Unix milliseconds
            to_ts: End time in Unix milliseconds
            divide_price: If True, divide prices by 1000 (for options/warrants)
            count_back: Optional limit on number of candles to return
            
        Returns:
            List of Candle objects
        """
        if count_back:
            url = f"{self._micro_api_url}/GetOhlcvHis/{symbol}/{resolution}/{from_ts}/{to_ts}/{count_back}"
        else:
            url = f"{self._micro_api_url}/GetOhlcvHis/{symbol}/{resolution}/{from_ts}/{to_ts}"
        
        data = self._request(url)
        
        if not data:
            return []
        
        candles = []
        for item in data:
            candle = Candle.from_dict(item)
            if divide_price:
                candle.open /= 1000
                candle.high /= 1000
                candle.low /= 1000
                candle.close /= 1000
            candles.append(candle)
        
        return candles
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Latest price or None if not available
        """
        now = int(datetime.now().timestamp() * 1000)
        one_day_ago = now - 24 * 60 * 60 * 1000
        
        # Try 1-minute candles first
        candles = self.fetch_candles(
            symbol,
            TimeResolution.MINUTE_1,
            one_day_ago,
            now
        )
        
        if candles:
            return candles[-1].close
        
        # Fallback to daily candles
        candles = self.fetch_candles(
            symbol,
            TimeResolution.DAY_1,
            one_day_ago,
            now
        )
        
        return candles[-1].close if candles else None
    
    def get_closing_price(self, symbol: str, date: datetime) -> Optional[float]:
        """
        Get closing price for a symbol on a specific date.
        
        Args:
            symbol: Trading symbol
            date: Target date
            
        Returns:
            Closing price or None if not available
        """
        start_of_day = datetime(date.year, date.month, date.day)
        end_of_day = start_of_day + timedelta(days=1, milliseconds=-1)
        
        candles = self.fetch_candles(
            symbol,
            TimeResolution.DAY_1,
            int(start_of_day.timestamp() * 1000),
            int(end_of_day.timestamp() * 1000)
        )
        
        return candles[-1].close if candles else None
    
    def get_closing_prices(
        self,
        symbols: List[str],
        date: datetime
    ) -> Dict[str, float]:
        """
        Get closing prices for multiple symbols on a date.
        
        Args:
            symbols: List of trading symbols
            date: Target date
            
        Returns:
            Dict mapping symbol to closing price
        """
        prices = {}
        for symbol in symbols:
            price = self.get_closing_price(symbol, date)
            if price is not None:
                prices[symbol] = price
        return prices
    
    def get_daily_candles(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Candle]:
        """
        Get daily candles for a date range.
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            List of daily Candle objects
        """
        return self.fetch_candles(
            symbol,
            TimeResolution.DAY_1,
            int(start_date.timestamp() * 1000),
            int(end_date.timestamp() * 1000)
        )

    def get_product_master(self, symbol: str) -> Optional[ProductMaster]:
        """
        Get complete product master data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            ProductMaster or None if not found
        """
        # Fixed: Use REST API matching sample/src/hooks/apps/marketData/index.ts
        url = f"{self._rest_api_url}/api/v1/MarketData/GetProductMaster/{symbol}"
        data = self._request(url, authenticated=True)
        
        if not data:
            return None
            
        # The REST API usually returns { "data": { ... } } or direct object?
        # sample/src/hooks/apps/marketData/index.ts says: "const data = await response.json(); return { ..., data }"
        # use-product-data.ts says: "const response = await getSymbolSearch... response.data.data.find..."
        # But for GetProductMaster(symbol):
        # sample/index.ts: return { status, symbol, data } where data = response.json()
        # So 'data' here is the JSON body.
        # If the JSON body wraps the result in "data", we need to unwrap.
        # Most of their APIs seem to return generic response envelope { "data": ... } or valid object.
        # I'll check 'data' key just in case, but usually from_dict handles flat mapping if root is the object.
        # Let's assume root is the object OR it has a 'data' wrapper.
        
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            return ProductMaster.from_dict(data["data"])
        
        return ProductMaster.from_dict(data)
    
    def get_margin_rate(self, symbol: str) -> float:
        """
        Get margin rate for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Margin rate (e.g. 0.1 for 10%). Defaults to 1.0 (100% / Cash).
        """
        try:
             # Fixed: Use correct endpoint from user curl verification
             url = f"{self._rest_api_url}/api/v1/diagnostics/margin-ratios/{symbol}"
             data = self._request(url, authenticated=True)
             
             if not data:
                 # Fallback to heuristics if API fails or returns nothing
                 if "VN30" in symbol or "F" in symbol:
                     return 0.15
                 return 1.0
                 
             # Handle response wrappers if any, though curl output showed direct object (after 'sample' label)
             # Curl output: { "forceCloseRate": ..., "marginRatio": 0.026, ... }
             # It seems to return the object directly.
             
             # If wrapped in "data":
             if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
                  margin_ratio = float(data["data"].get("marginRatio", 1.0))
                  return margin_ratio
             
             # Direct object
             margin_ratio = float(data.get("marginRatio", 1.0))
             
             # Note: The user curl output shows marginRatio: 0.026 (2.6%?).
             # Usually margin rate implies "Initial Margin Requirement".
             # If marginRatio is consistent (e.g. 0.026), we return it.
             return margin_ratio
             
        except Exception as e:
            logger.warning(f"Failed to fetch margin rate for {symbol}: {e}")
            # Fallback
            if "VN30" in symbol or "F" in symbol:
                 return 0.15
            return 1.0
    
