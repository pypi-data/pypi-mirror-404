"""
Main client for Vero Algo SDK.

Provides unified access to all SDK services.
"""

import logging
from typing import Optional

from .config import VeroConfig
from .features.orders import OrderService
from .features.market_data import MarketDataService
from .features.streaming import VeroStream


logger = logging.getLogger(__name__)


class VeroClient:
    """
    Main Vero Algo SDK client.
    
    Provides unified access to authentication, orders, market data, and streaming.
    
    Example:
        ```python
        client = VeroClient(
            backend_server="api.example.com",
            auth_server="auth.example.com",
            streaming_ws="wss://stream.example.com/connection/websocket"
        )
        
        # Login
        client.auth.login("user@example.com", "password")
        
        # Place order
        response = client.orders.place_order(
            symbol="VN30F2401",
            side="B",
            price=1200,
            qty=1,
            account_id="my-account"
        )
        
        # Subscribe to market data
        client.stream.connect()
        client.stream.subscribe_product_stat("VN30F2401", print)
        ```
    """
    
    def __init__(
        self,
        backend_server: str = "",
        auth_server: str = "",
        micro_api_server: str = "",
        streaming_ws: str = "",
        protocol: str = "https",
        config: Optional[VeroConfig] = None,
        debug: bool = False,
    ):
        """
        Initialize VeroClient.
        
        Args:
            backend_server: Backend API server URL
            auth_server: Authentication server URL
            micro_api_server: Micro API server URL
            streaming_ws: WebSocket streaming URL
            protocol: HTTP protocol (http or https)
            config: Optional VeroConfig instance (overrides individual params)
            debug: Enable debug logging
        """
        # Configure logging
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        
        # Create config
        if config:
            self._config = config
        else:
            self._config = VeroConfig(
                backend_server=backend_server,
                auth_server=auth_server,
                micro_api_server=micro_api_server,
                streaming_ws=streaming_ws,
                protocol=protocol,
                debug=debug,
            )
        
        # Initialize services
        self._orders = OrderService(self._config)
        self._market_data = MarketDataService(self._config)
        self._stream = VeroStream(self._config)
    
    def set_jwt_token(self, token: str) -> None:
        """
        Set authentication using a direct JWT token.
        
        Args:
            token: JWT token string
        """
        self._config.jwt_token = token
        # Force update stream token if needed (stream reads from config now)
        logger.info("Authentication set via direct JWT token")
    
    @property
    def config(self) -> VeroConfig:
        """Get the configuration."""
        return self._config
    
    # auth property removed
    
    @property
    def orders(self) -> OrderService:
        """Get the order service."""
        return self._orders
    
    @property
    def market_data(self) -> MarketDataService:
        """Get the market data service."""
        return self._market_data
    
    @property
    def stream(self) -> VeroStream:
        """Get the streaming client."""
        return self._stream
    
    @classmethod
    def from_config(cls, config: VeroConfig) -> "VeroClient":
        """
        Create client from a VeroConfig instance.
        
        Args:
            config: VeroConfig instance
            
        Returns:
            VeroClient instance
        """
        return cls(config=config)
    
    @classmethod
    def from_tenant_json(cls, path: str, debug: bool = False) -> "VeroClient":
        """
        Create client from a tenant.json file.
        
        Args:
            path: Path to tenant.json file
            debug: Enable debug logging
            
        Returns:
            VeroClient instance
        """
        config = VeroConfig.from_tenant_json(path)
        config.debug = debug
        return cls(config=config)
    
    @classmethod
    def from_env(cls, debug: bool = False) -> "VeroClient":
        """
        Create client from environment variables.
        
        Expected environment variables:
        - VERO_BACKEND_SERVER
        - VERO_AUTH_SERVER
        - VERO_MICRO_API_SERVER
        - VERO_STREAMING_WS
        - VERO_PROTOCOL
        
        Args:
            debug: Enable debug logging
            
        Returns:
            VeroClient instance
        """
        config = VeroConfig.from_env()
        config.debug = debug
        return cls(config=config)
    

    
    # logout removed
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return bool(self._config.jwt_token)
