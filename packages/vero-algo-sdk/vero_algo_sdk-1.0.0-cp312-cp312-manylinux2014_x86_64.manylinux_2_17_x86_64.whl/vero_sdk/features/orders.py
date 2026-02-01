"""
Order service for Vero Algo SDK.

Handles placing, canceling, modifying orders and retrieving order/trade data.
"""

import uuid
import logging
from typing import List, Optional, Dict, Any

from ..config import VeroConfig
from ..types import (
    NewOrderRequest,
    CancelOrderRequest,
    OrderData,
    OrderResponse,
    Trade,
)


logger = logging.getLogger(__name__)


class OrderService:
    """
    Order management service.
    
    Provides methods for placing, canceling, and modifying orders,
    as well as retrieving order history and trades.
    """
    
    def __init__(self, config: VeroConfig):
        """
        Initialize OrderService.
        
        Args:
            config: VeroConfig instance
        """
        self.config = config
        self._base_url = config.rest_api_url
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        import requests
        
        url = f"{self._base_url}{endpoint}"
        if not self.config.jwt_token:
            raise ValueError("Authentication token not set")

        headers = {
             "Content-Type": "application/json",
             "Authorization": f"Bearer {self.config.jwt_token}",
        }
        
        logger.debug(f"API Request: {method} {url}")
        if data:
            logger.debug(f"Request body: {data}")
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params
        )
        
        logger.debug(f"API Response: {response.status_code} {response.text[:500]}")
        
        if not response.ok:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get("error") or error_data.get("message") or error_data.get("detail") or str(error_data)
            except Exception:
                error_msg = response.text or error_msg
            
            logger.error(f"API Error: {error_msg}")
            
            return {
                "status": response.status_code,
                "message": error_msg,
                "data": None,
            }
        
        return response.json()
    
    def place_order(
        self,
        symbol: str,
        side: str,
        price: float,
        qty: int,
        order_type: str = "LO",
        account_id: str = "",
        ref_order_id: Optional[str] = None,
    ) -> OrderResponse:
        """
        Place a new order.
        
        Args:
            symbol: Trading symbol (e.g., "VN30F2401")
            side: Order side - "B" for Buy, "S" for Sell
            price: Order price
            qty: Order quantity
            order_type: Order type - "LO", "MTL", "ATO", "ATC"
            account_id: Account ID to place order for
            ref_order_id: Optional reference order ID (auto-generated if not provided)
            
        Returns:
            OrderResponse with result
        """
        if not ref_order_id:
            ref_order_id = str(uuid.uuid4())
        
        # Map side enum to string
        order_side = side if isinstance(side, str) else ("B" if "BUY" in str(side) else "S")
        
        logger.info(f"Placing order: {symbol} {order_side} {qty}@{price}")
        
        # Use URL path parameters like TypeScript sample:
        # /api/v1/orders/new/{refOrderID}/{accountID}/{symbol}/{orderSide}/{price}/{qty}/{orderType}
        endpoint = f"/api/v1/orders/new/{ref_order_id}/{account_id}/{symbol}/{order_side}/{price}/{qty}/{order_type}"
        
        result = self._request("POST", endpoint)
        return OrderResponse.from_dict(result)
    
    def cancel_order(self, order_id: str, account_id: str) -> OrderResponse:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
            account_id: Account ID
            
        Returns:
            OrderResponse with result
        """
        logger.info(f"Canceling order: {order_id}")
        
        # Endpoint: /api/v1/orders/cancel/{orderID}
        # Note: Some versions might use JSON body, but TypeScript sample suggests path param
        # If path param fails, we can revert or try both.
        # Based on sample: ${apiConfig.restapi.endpoint}/api/v1/orders/cancel/${orderID}
        
        result = self._request("POST", f"/api/v1/orders/cancel/{order_id}")
        return OrderResponse.from_dict(result)

    def close_position(
        self,
        symbol: str, 
        qty: float, 
        side: str, # Side of the POSITION (e.g. "LONG" or "BUY")
        account_id: str
    ) -> OrderResponse:
        """
        Close a position by placing an opposing market order.
        
        Args:
            symbol: Trading symbol
            qty: Quantity to close
            side: Side of the CURRENT POSITION ("B"/"BUY" or "S"/"SELL")
            account_id: Account ID
            
        Returns:
            OrderResponse
        """
        # Determine opposing side
        is_long = side.upper() in ["B", "BUY", "LONG"]
        close_side = "S" if is_long else "B" # If Long, Sell to close. If Short, Buy to close.
        
        logger.info(f"Closing position: {symbol} {side} {qty} -> Placing {close_side} order")
        
        return self.place_order(
            symbol=symbol,
            side=close_side,
            price=0, # Market order usually ignores price or uses reference
            qty=int(qty),
            order_type="MTL", # Market To Limit is verifying to work/safe
            account_id=account_id
        )
    
    
    def get_orders(
        self,
        account_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[OrderData]:
        """
        Get orders with optional filters.
        
        Args:
            account_id: Filter by account ID
            start_time: Start time in Unix ms
            end_time: End time in Unix ms
            symbol: Filter by symbol
            status: Filter by order status
            
        Returns:
            List of OrderData objects
        """
        params: Dict[str, Any] = {}
        if account_id:
            params["accountId"] = account_id
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if symbol:
            params["symbol"] = symbol
        if status:
            params["status"] = status
        
        result = self._request("GET", "/api/v1/orders", params=params)
        
        data = result.get("data", [])
        if not data:
            return []
        
        return [OrderData.from_dict(order) for order in data]
    
    def get_execution_reports(self) -> List[OrderData]:
        """
        Get all execution reports for the current user.
        
        Returns:
            List of OrderData objects
        """
        result = self._request("GET", "/api/v1/execution-reports")
        
        data = result.get("data", [])
        if not data:
            return []
        
        return [OrderData.from_dict(order) for order in data]
    
    def get_trades(
        self,
        account_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Trade]:
        """
        Get trades with optional filters.
        
        Args:
            account_id: Filter by account ID
            start_time: Start time in Unix ms
            end_time: End time in Unix ms
            
        Returns:
            List of Trade objects
        """
        params: Dict[str, Any] = {}
        if account_id:
            params["accountId"] = account_id
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        result = self._request("GET", "/api/v1/trades", params=params)
        
        data = result.get("data", [])
        if not data:
            return []
        
        return [Trade.from_dict(trade) for trade in data]
    
    # ========================================================================
    # Stop Orders
    # ========================================================================
    
    def place_stop_order(
        self,
        symbol: str,
        side: str,
        stop_price: float,
        qty: int,
        account_id: str,
        limit_price: Optional[float] = None,
    ) -> OrderResponse:
        """
        Place a new stop order.
        
        Args:
            symbol: Trading symbol
            side: Order side - "B" or "S"
            stop_price: Trigger price for the stop order
            qty: Order quantity
            account_id: Account ID
            limit_price: Optional limit price (for stop-limit orders)
            
        Returns:
            OrderResponse with result
        """
        data = {
            "refOrderID": str(uuid.uuid4()),
            "accountID": account_id,
            "symbol": symbol,
            "orderSide": side,
            "stopPrice": stop_price,
            "qty": qty,
        }
        if limit_price is not None:
            data["limitPrice"] = limit_price
        
        logger.info(f"Placing stop order: {symbol} {side} {qty}@stop={stop_price}")
        
        result = self._request("POST", "/api/v1/stop-orders", data=data)
        return OrderResponse.from_dict(result)
    
    def get_stop_orders(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get stop orders.
        
        Args:
            account_id: Optional account ID filter
            
        Returns:
            List of stop order dicts
        """
        params = {}
        if account_id:
            params["accountId"] = account_id
        
        result = self._request("GET", "/api/v1/stop-orders", params=params)
        return result.get("data", [])
    
    # ========================================================================
    # Bracket Orders
    # ========================================================================
    
    def place_bracket_order(
        self,
        symbol: str,
        side: str,
        price: float,
        qty: int,
        account_id: str,
        take_profit_price: float,
        stop_loss_price: float,
    ) -> OrderResponse:
        """
        Place a bracket order with take-profit and stop-loss.
        
        Args:
            symbol: Trading symbol
            side: Order side - "B" or "S"
            price: Entry price
            qty: Quantity
            account_id: Account ID
            take_profit_price: Take profit price
            stop_loss_price: Stop loss price
            
        Returns:
            OrderResponse with result
        """
        # Map side enum to string
        order_side = side if isinstance(side, str) else ("B" if "BUY" in str(side) else "S")
        
        # Determine condition type based on side for Limit orders
        # Buy Limit: price <= limit_price
        # Sell Limit: price >= limit_price
        condition_type = "<=" if order_side == "B" else ">="
        
        data = {
            "symbol": symbol,
            "side": order_side,
            "account": account_id,
            "quantity": qty,
            "orderType": "LO", # Default to Limit Order
            "conditionPrice": price,
            "conditionType": condition_type,
            "takeProfitPrice": take_profit_price,
            "stopLossPrice": stop_loss_price,
        }
        
        logger.info(f"Placing bracket order: {symbol} {order_side} {qty}@{price} TP={take_profit_price} SL={stop_loss_price}")
        
        # Correct endpoint from sample: /api/v1/orders/bracket-order
        result = self._request("POST", "/api/v1/orders/bracket-order", data=data)
        return OrderResponse.from_dict(result)
    
    def get_bracket_orders(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get bracket orders.
        
        Args:
            account_id: Optional account ID filter
            
        Returns:
            List of bracket order dicts
        """
        params = {}
        if account_id:
            params["accountId"] = account_id
        
        result = self._request("GET", "/api/v1/bracket-orders", params=params)
        return result.get("data", [])
