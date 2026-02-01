import logging
from typing import Any

from ..types import OrderSide

logger = logging.getLogger("vero")

class BacktestOrderService:
    def __init__(self, vero):
        self.vero = vero
        
    def place_bracket_order(self, symbol, side, price, qty, account_id, take_profit_price, stop_loss_price):
        if self._get_strategy():
             return self._place_via_strategy(symbol, side, price, qty)
        logger.warning("[Backtest] Strategy not initialized, ignoring order")

    def place_order(self, symbol, side, price, qty, order_type, account_id):
        if self._get_strategy():
            # Treat all as bracket-less for now
            return self._place_via_strategy(symbol, side, price, qty)
        logger.warning("[Backtest] Strategy not initialized, ignoring order")
            
    def cancel_order(self, order_id: str, account_id: str):
        """Cancel an order in backtest."""
        strategy = self._get_strategy()
        if strategy and strategy.context:
            strategy.context.cancel_order(order_id)
            logger.info(f"[Backtest] Cancelled order {order_id}")
            # Identify expected return type - OrderResponse
            from ..types import OrderResponse
            return OrderResponse(success=True, message="Order cancelled", data={"orderID": order_id})
        return None

    def close_position(self, symbol: str, qty: float, side: str, account_id: str):
        """Close position in backtest."""
        strategy = self._get_strategy()
        if strategy:
            # Emulate closing properties using Strategy methods
            # Note: side passed here is the POSITION side (user says "Close Long"), or the ORDER side?
            # OrderService docs said: "side: Side of the CURRENT POSITION".
            # So if side="B", we want to Sell.
            # Strategy.close_all_positions(symbol) might be too aggressive if qty is partial?
            # Strategy.close_position takes a Position object.
            # We need to find the matching position.
            
            ctx = strategy.context
            positions = ctx.get_positions_by_symbol(symbol)
            target_side = "LONG" if side.upper() in ["B", "BUY", "LONG"] else "SHORT"
            
            closed_count = 0
            for pos in positions:
                if pos.side.name == target_side:
                    # Found a position to close
                    # TODO: Handle partial close if qty < pos.quantity
                    strategy.close_position(pos)
                    closed_count += 1
            
            if closed_count > 0:
                 logger.info(f"[Backtest] Closed {closed_count} positions for {symbol}")
                 from ..types import OrderResponse
                 return OrderResponse(success=True, message=f"Closed {closed_count} positions")
                 
        return None
        
    def _get_strategy(self):
        if self.vero.backtest_engine and self.vero.backtest_engine.strategy:
             return self.vero.backtest_engine.strategy
        return None
        
    def _place_via_strategy(self, symbol, side, price, qty):
         strategy = self._get_strategy()
         if not strategy:
             from ..types import OrderResponse
             return OrderResponse(success=False, message="Strategy not active")
         
         from ..types import OrderSide, OrderResponse
         import uuid
         
         # Convert side
         side_enum = OrderSide.BUY if (str(side).upper() in ["B", "BUY"]) else OrderSide.SELL
         
         # Execute
         if side_enum == OrderSide.BUY:
             strategy.buy(symbol, qty, price)
         else:
             strategy.sell(symbol, qty, price)
             
         logger.info(f"[Backtest] Placed {side} order @ {price} for {qty}")
         # Return backtest OrderResponse
         return OrderResponse(success=True, message="Order placed (Backtest)", data={"orderID": str(uuid.uuid4())})


class BacktestClient:
    def __init__(self, vero):
        self.orders = BacktestOrderService(vero)
        self.stream = None # Not used stream in backtest usually
