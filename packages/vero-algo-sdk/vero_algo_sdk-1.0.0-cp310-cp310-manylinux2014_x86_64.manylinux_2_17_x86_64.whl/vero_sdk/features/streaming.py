import asyncio
import logging
from typing import Callable, Optional, Dict, List, Any, Awaitable, Union
from dataclasses import dataclass

from centrifuge import Client, Subscription, ClientState, ClientEventHandler, SubscriptionEventHandler

from ..config import VeroConfig, Channels, DataTypes
from ..types import Candle, ProductInfo, ProductStat, Depth


logger = logging.getLogger(__name__)


@dataclass
class VeroSubscription:
    """Represents an active subscription wrapper."""
    channel_name: str
    callbacks: Optional[List[Union[Callable[[Any], Awaitable[None]], Callable[[Any], None]]]] = None  # Changed to list of callbacks
    sub_obj: Optional[Subscription] = None
    active: bool = True
    
    def __post_init__(self):
        if self.callbacks is None:
            self.callbacks = []


class VeroStream:
    """
    Real-time streaming client using OFFICIAL Centrifuge Python library (Async).
    Pure async implementation.
    """
    
    def __init__(self, config: VeroConfig):
        """Initialize VeroStream."""
        self.config = config
        self._client: Optional[Client] = None
        
        # Track subscriptions
        self._subscriptions: Dict[str, VeroSubscription] = {}
        
        # Callbacks
        self._on_connect: Optional[Callable[[], Awaitable[None]]] = None
        self._on_disconnect: Optional[Callable[[], Awaitable[None]]] = None
        self._on_error: Optional[Callable[[Exception], Awaitable[None]]] = None

    @property
    def connected(self) -> bool:
        """Check if currently connected."""
        return self._client.state == ClientState.CONNECTED if self._client else False
    
    async def connect(
        self,
        on_connect: Optional[Callable[[], Awaitable[None]]] = None,
        on_disconnect: Optional[Callable[[], Awaitable[None]]] = None,
        on_error: Optional[Callable[[Exception], Awaitable[None]]] = None,
    ) -> None:
        """Connect to the streaming server asynchronously."""
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_error = on_error
        
        token = ""
        cookies = {}
        headers = {}
        
        if self.config.jwt_token:
             token = self.config.jwt_token
             
        # Format cookies for WebSocket header if present
        if cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            headers["Cookie"] = cookie_str
            # If using cookies, don't send the token in the payload to avoid conflicts
            token = "" 
            logger.debug("Using Cookie authentication for WebSocket (Token cleared)")
        
        # Define Client Event Handlers
        events = ClientEventHandler()
        events.on_connected = self._handle_connected
        events.on_disconnected = self._handle_disconnected
        events.on_error = self._handle_error

        self._client = Client(
            self.config.streaming_ws,
            events=events,
            token=token,
            headers=headers
        )
        
        logger.info(f"Connecting to {self.config.streaming_ws} (Async)...")
        await self._client.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from the streaming server."""
        if self._client:
            await self._client.disconnect()
        self._subscriptions.clear()
        
    async def _handle_connected(self, ctx):
        logger.info(f"Centrifuge Connected: {ctx}")
        if self._on_connect:
            if asyncio.iscoroutinefunction(self._on_connect):
                await self._on_connect()
            else:
                self._on_connect()
            
    async def _handle_disconnected(self, ctx):
        logger.info(f"Centrifuge Disconnected: {ctx}")
        if self._on_disconnect:
             if asyncio.iscoroutinefunction(self._on_disconnect):
                await self._on_disconnect()
             else:
                self._on_disconnect()
            
    async def _handle_error(self, ctx):
        logger.error(f"Centrifuge Error: {ctx}")
        if self._on_error:
             if asyncio.iscoroutinefunction(self._on_error):
                await self._on_error(Exception(str(ctx)))
             else:
                self._on_error(Exception(str(ctx)))

    # ========================================================================
    # Subscription Logic
    # ========================================================================

    async def _subscribe(
        self,
        channel: str,
        data_type: str,
        data_id: str,
        callback: Union[Callable[[Any], Awaitable[None]], Callable[[Any], None]],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """Create a subscription asynchronously."""
        channel_name = f"{channel}:{data_type}:{data_id}"
        
        if not self._client:
            raise RuntimeError("Client not initialized. Call connect() first.")
            
        if channel_name in self._subscriptions:
            logger.info(f"Subscription to {channel_name} exists. Adding callback.")
            wrapper = self._subscriptions[channel_name]
            if wrapper.callbacks is None: wrapper.callbacks = []
            wrapper.callbacks.append(callback)
            return wrapper
        
        logger.info(f"Subscribing to {channel_name}...")
        
        wrapper = VeroSubscription(
            channel_name=channel_name,
            callbacks=[callback]
        )
        self._subscriptions[channel_name] = wrapper
        
        # Defines handlers
        async def on_publication(ctx):
            try:
                if hasattr(ctx, 'data'):
                    data = ctx.data
                elif hasattr(ctx, 'pub') and hasattr(ctx.pub, 'data'):
                    data = ctx.pub.data
                else:
                    # Fallback or introspection
                    logger.warning(f"Publication event missing data attribute. Attrs: {dir(ctx)}")
                    if hasattr(ctx, 'pub'):
                        data = ctx.pub
                    else:
                        return

                # Support both async and sync callbacks
                if wrapper.callbacks:
                    for cb in wrapper.callbacks:
                        try:
                            result = cb(data)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            logger.error(f"Error in subscription callback {cb} for {channel_name}: {e}")
            except Exception as e:
                logger.error(f"Error in subscription handler for {channel_name}: {e}")
                
        async def on_sub_subscribed(ctx):
            logger.debug(f"Subscribed to {channel_name}: {ctx}")
            
        async def on_sub_error(ctx):
            logger.error(f"Subscription error {channel_name}: {ctx}")

        # Setup Subscription Event Handlers
        sub_events = SubscriptionEventHandler()
        sub_events.on_publication = on_publication
        sub_events.on_subscribed = on_sub_subscribed
        sub_events.on_error = on_sub_error
        
        sub = self._client.new_subscription(channel_name, events=sub_events)
        
        wrapper.sub_obj = sub
        await sub.subscribe()
        
        return wrapper

    async def unsubscribe(self, subscription: VeroSubscription) -> None:
        """Unsubscribe."""
        if subscription.active and subscription.sub_obj:
            await subscription.sub_obj.unsubscribe()
            subscription.active = False
            if subscription.channel_name in self._subscriptions:
                del self._subscriptions[subscription.channel_name]
    
    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all channels."""
        for sub in list(self._subscriptions.values()):
            await self.unsubscribe(sub)
    
    async def _subscribe_channel(
        self,
        channel_name: str,
        callback: Union[Callable[[Any], Awaitable[None]], Callable[[Any], None]],
    ) -> VeroSubscription:
        """
        Create a subscription to a full channel name string.
        
        Args:
            channel_name: Full channel name (e.g. "order:MarginCall:USER123")
            callback: Async callback function
            
        Returns:
            VeroSubscription object
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Call connect() first.")
            
        if channel_name in self._subscriptions:
            logger.info(f"Subscription to {channel_name} exists. Adding callback.")
            wrapper = self._subscriptions[channel_name]
            if wrapper.callbacks is None: wrapper.callbacks = []
            wrapper.callbacks.append(callback)
            return wrapper
        
        logger.info(f"Subscribing to {channel_name}...")
        
        wrapper = VeroSubscription(
            channel_name=channel_name,
            callbacks=[callback]
        )
        self._subscriptions[channel_name] = wrapper
        
        # Defines handlers
        async def on_publication(ctx):
            try:
                if hasattr(ctx, 'data'):
                    data = ctx.data
                elif hasattr(ctx, 'pub') and hasattr(ctx.pub, 'data'):
                    data = ctx.pub.data
                else:
                    logger.warning(f"Publication event missing data attribute. Attrs: {dir(ctx)}")
                    if hasattr(ctx, 'pub'):
                        data = ctx.pub
                    else:
                        return

                # Support both async and sync callbacks
                if wrapper.callbacks:
                    for cb in wrapper.callbacks:
                        try:
                            result = cb(data)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            logger.error(f"Error in subscription callback {cb} for {channel_name}: {e}")
            except Exception as e:
                logger.error(f"Error in subscription handler for {channel_name}: {e}")
                
        async def on_sub_subscribed(ctx):
            logger.debug(f"Subscribed to {channel_name}: {ctx}")
            
        async def on_sub_error(ctx):
            logger.error(f"Subscription error {channel_name}: {ctx}")

        # Setup Subscription Event Handlers
        sub_events = SubscriptionEventHandler()
        sub_events.on_publication = on_publication
        sub_events.on_subscribed = on_sub_subscribed
        sub_events.on_error = on_sub_error
        
        sub = self._client.new_subscription(channel_name, events=sub_events)
        
        wrapper.sub_obj = sub
        await sub.subscribe()
        
        return wrapper
    
    # ========================================================================
    # Market Data Subscriptions
    # ========================================================================
    
    async def subscribe_product_info(
        self,
        symbol: str,
        callback: Callable[[ProductInfo], Awaitable[None]],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to product info updates.
        
        Args:
            symbol: Trading symbol
            callback: Callback function receiving ProductInfo
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        async def wrapper(data):
            if data:
                result = callback(ProductInfo.from_dict(data))
                if asyncio.iscoroutine(result): await result
        
        return await self._subscribe(
            channel=Channels.MARKET,
            data_type=DataTypes.PRODUCT_INFO,
            data_id=symbol,
            callback=wrapper,
            listener_id=listener_id,
        )
    
    async def subscribe_product_stat(
        self,
        symbol: str,
        callback: Callable[[ProductStat], Awaitable[None]],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to product statistics updates.
        
        Args:
            symbol: Trading symbol
            callback: Callback function receiving ProductStat
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        async def wrapper(data):
            if data:
                result = callback(ProductStat.from_dict(data))
                if asyncio.iscoroutine(result): await result
        
        return await self._subscribe(
            channel=Channels.MARKET,
            data_type=DataTypes.PRODUCT_STAT,
            data_id=symbol,
            callback=wrapper,
            listener_id=listener_id,
        )
    
    async def subscribe_depth(
        self,
        symbol: str,
        callback: Callable[[Depth], Awaitable[None]],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to order book depth updates.
        
        Args:
            symbol: Trading symbol
            callback: Callback function receiving Depth
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        async def wrapper(data):
            if data:
                result = callback(Depth.from_dict(data))
                if asyncio.iscoroutine(result): await result
        
        return await self._subscribe(
            channel=Channels.MARKET,
            data_type=DataTypes.DEPTH,
            data_id=symbol,
            callback=wrapper,
            listener_id=listener_id,
        )
    
    async def subscribe_candles(
        self,
        symbol: str,
        resolution: int,
        callback: Callable[[Candle], Awaitable[None]],
        divide_price: bool = False,
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to OHLCV candle updates.
        
        Args:
            symbol: Trading symbol
            resolution: Time resolution in seconds
            callback: Callback function receiving Candle
            divide_price: If True, divide prices by 1000
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        async def wrapper(data):
            if data:
                candle = Candle.from_dict(data)
                if divide_price:
                    candle.open /= 1000
                    candle.high /= 1000
                    candle.low /= 1000
                    candle.close /= 1000
                result = callback(candle)
                if asyncio.iscoroutine(result): await result
        
        return await self._subscribe(
            channel=Channels.MARKET,
            data_type=DataTypes.OHLCV,
            data_id=f"{symbol}:{resolution}",
            callback=wrapper,
            listener_id=listener_id,
        )
    
    async def subscribe_market_trades(
        self,
        symbol: str,
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to market trades (Trade Log).
        Alias for subscribe_trade_log.
        
        Args:
            symbol: Trading symbol
            callback: Callback function receiving trade log data
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        return await self.subscribe_trade_log(symbol, callback, listener_id)



    async def subscribe_trade_log(
        self,
        symbol: str,
        callback: Union[Callable[[Dict[str, Any]], None], Callable[[Dict[str, Any]], Awaitable[None]]],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to trade log updates.
        
        Args:
            symbol: Trading symbol
            callback: Callback function receiving trade log data
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        return await self._subscribe(
            channel=Channels.MARKET,
            data_type=DataTypes.TRADE_LOG,
            data_id=symbol,
            callback=callback,
            listener_id=listener_id,
        )
    
    
    # ========================================================================
    # Order Subscriptions
    # ========================================================================
    
    async def subscribe_order_execution_report(
        self,
        connection_id: str,
        callback: Callable[[Dict[str, Any]], None],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to order execution report updates.
        
        Args:
            connection_id: Connection ID to subscribe for
            callback: Callback function receiving order execution data
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        return await self._subscribe(
            channel=Channels.ORDER,
            data_type=DataTypes.ORDER_EXECUTION_REPORT,
            data_id=connection_id,
            callback=callback,
            listener_id=listener_id,
        )
    
    # ========================================================================
    # Algo Subscriptions
    # ========================================================================
    
    async def subscribe_algo_master(
        self,
        account_id: str,
        callback: Callable[[Dict[str, Any]], None],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to algo master updates.
        
        Args:
            account_id: Account ID to subscribe for
            callback: Callback function receiving algo master data
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        return await self._subscribe(
            channel=Channels.ALGO,
            data_type=DataTypes.ALGO_MASTER,
            data_id=account_id,
            callback=callback,
            listener_id=listener_id,
        )
    async def subscribe_algo_order(
        self,
        account_id: str,
        callback: Callable[[Dict[str, Any]], None],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to algo order updates.
        
        Args:
            account_id: Account ID to subscribe for
            callback: Callback function receiving algo order data
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        return await self._subscribe(
            channel=Channels.ALGO,
            data_type=DataTypes.ALGO_ORDER,
            data_id=account_id,
            callback=callback,
            listener_id=listener_id,
        )
    
    async def subscribe_algo_position(
        self,
        account_id: str,
        callback: Callable[[Dict[str, Any]], None],
        listener_id: Optional[str] = None,
    ) -> VeroSubscription:
        """
        Subscribe to algo position updates.
        
        Args:
            account_id: Account ID to subscribe for
            callback: Callback function receiving algo position data
            listener_id: Optional unique listener ID
            
        Returns:
            Subscription object
        """
        return await self._subscribe(
            channel=Channels.ALGO,
            data_type=DataTypes.ALGO_POSITION,
            data_id=account_id,
            callback=callback,
            listener_id=listener_id,
        )


    async def subscribe(
        self,
        channel: str,
        callback: Callable[[Any], Awaitable[None]],
    ) -> VeroSubscription:
        """
        Generic subscription to any channel string.
        
        Args:
            channel: Full channel name (e.g. "order:MarginCall:USER123")
            callback: Async callback function
        """
        return await self._subscribe_channel(
            channel_name=channel,
            callback=callback
        )
