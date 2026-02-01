"""
Configuration management for Vero Algo SDK.

Supports loading from environment variables, defaults, or direct configuration.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Optional

from .utils.defaults import (
    DEFAULT_BACKEND_SERVER,
    DEFAULT_AUTH_SERVER,
    DEFAULT_MICRO_API_SERVER,
    DEFAULT_STREAMING_WS,
    DEFAULT_STREAMING_HTTP,
    DEFAULT_STREAMING_SSE,
    DEFAULT_STATIC_SERVER,
    DEFAULT_PROTOCOL,
)


@dataclass
class VeroConfig:
    """Configuration for Vero Algo SDK."""
    
    # Server URLs (defaults provided - no env vars required)
    backend_server: str = ""
    auth_server: str = ""
    micro_api_server: str = ""
    streaming_ws: str = ""
    streaming_http: str = ""
    streaming_sse: str = ""
    static_server: str = ""
    
    # Protocol
    protocol: str = "https"
    
    # Token storage key name
    storage_token_key: str = "vero_session_token"
    
    # Debug mode
    debug: bool = False

    # JWT Token
    jwt_token: str = ""
    
    # Control API Port (0 or None to disable by default)
    control_api_port: Optional[int] = None
    
    # Board suffix (e.g., "G1")
    board: str = "G1"
    
    def __post_init__(self):
        """Load from environment variables or use defaults if not set."""
        # Use provided value > env var > default
        self.backend_server = (self.backend_server or 
                               os.getenv("VERO_BACKEND_SERVER") or 
                               DEFAULT_BACKEND_SERVER)
        self.auth_server = (self.auth_server or 
                            os.getenv("VERO_AUTH_SERVER") or 
                            DEFAULT_AUTH_SERVER)
        self.micro_api_server = (self.micro_api_server or 
                                 os.getenv("VERO_MICRO_API_SERVER") or 
                                 DEFAULT_MICRO_API_SERVER)
        self.streaming_ws = (self.streaming_ws or 
                             os.getenv("VERO_STREAMING_WS") or 
                             DEFAULT_STREAMING_WS)
        self.streaming_http = (self.streaming_http or 
                               os.getenv("VERO_STREAMING_HTTP") or 
                               DEFAULT_STREAMING_HTTP)
        self.streaming_sse = (self.streaming_sse or 
                              os.getenv("VERO_STREAMING_SSE") or 
                              DEFAULT_STREAMING_SSE)
        self.static_server = (self.static_server or 
                              os.getenv("VERO_STATIC_SERVER") or 
                              DEFAULT_STATIC_SERVER)
        self.protocol = (self.protocol or 
                         os.getenv("VERO_PROTOCOL") or 
                         DEFAULT_PROTOCOL)
        
        # Load Control API Port
        if self.control_api_port is None:
            env_port = os.getenv("VERO_CONTROL_API_PORT")
            if env_port:
                try:
                    self.control_api_port = int(env_port)
                except ValueError:
                    pass
        
        self.debug = self.debug or os.getenv("VERO_DEBUG", "").lower() == "true"
    
    @property
    def rest_api_url(self) -> str:
        """Get the full REST API base URL."""
        if self.backend_server.startswith("http"):
            return self.backend_server
        return f"{self.protocol}://{self.backend_server}"
    
    @property
    def micro_api_url(self) -> str:
        """Get the full Micro API base URL."""
        if self.micro_api_server.startswith("http"):
            return self.micro_api_server
        return f"{self.protocol}://{self.micro_api_server}"
    
    @property
    def auth_url(self) -> str:
        """Get the full authentication server URL."""
        if self.auth_server.startswith("http"):
            return self.auth_server
        return f"{self.protocol}://{self.auth_server}"
    
    @classmethod
    def from_tenant_json(cls, path: str) -> "VeroConfig":
        """
        Load configuration from a tenant.json file.
        
        Args:
            path: Path to the tenant.json file
            
        Returns:
            VeroConfig instance
        """
        with open(path, "r") as f:
            data = json.load(f)
        
        return cls(
            backend_server=data.get("backendServer", ""),
            auth_server=data.get("authenticationServer", ""),
            micro_api_server=data.get("microApiServer", ""),
            streaming_ws=data.get("streamingWebsocket", ""),
            streaming_http=data.get("streamingHttpStream", ""),
            streaming_sse=data.get("streamingSse", ""),
            static_server=data.get("staticServer", ""),
            protocol=data.get("protocol", "https"),
            storage_token_key=data.get("storageTokenKeyName", "vero_session_token"),
        )
    
    @classmethod
    def from_env(cls) -> "VeroConfig":
        """
        Load configuration from environment variables.
        
        Returns:
            VeroConfig instance with all values from env vars
        """
        return cls()


# Channel names for streaming
class Channels:
    """Channel names for Centrifuge subscriptions."""
    MARKET = "mkt"
    ALGO = "algo"
    ORDER = "order"
    NOTIFY = "order"


# Data types for streaming
class DataTypes:
    """Data types for Centrifuge subscriptions."""
    DEPTH = "depth"
    PRODUCT_INFO = "productInfo"
    PRODUCT_STAT = "productStat"
    HEAT_MAP = "HeatMap"
    TRADE_LOG = "tradeLog"
    OHLCV = "OhlcvDTO"
    ALGO_MASTER = "AlgoMaster"
    ALGO_LOG = "AlgoLog"
    ALGO_PLAN = "AlgoPlan"
    ALGO_POSITION = "AlgoPosition"
    ALGO_ORDER = "AlgoOrder"
    ALGO_STATUS = "AlgoStatus"
    ALGO_NOTIFY = "AlgoNotify"
    ORDER_EXECUTION_REPORT = "OrderExecutionReport"


# Time resolutions for candle data (in seconds)
class TimeResolution:
    """Time resolution constants for OHLCV data (in seconds)."""
    MINUTE_1 = 60
    MINUTE_5 = 300
    MINUTE_15 = 900
    MINUTE_30 = 1800
    HOUR_1 = 3600
    HOUR_4 = 14400
    DAY_1 = 86400
