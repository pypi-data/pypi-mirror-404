"""
Default configuration for Vero Algo SDK.

Contains hardcoded server URLs - no environment variables needed.
"""

# ============================================================================
# Default Server URLs (from tenant.json)
# ============================================================================

# Main API server for trading operations
DEFAULT_BACKEND_SERVER = "api-gw-dev.verolabs.co"

# Authentication server
DEFAULT_AUTH_SERVER = "https://api-gw-dev.verolabs.co/api/authen"

# Micro API for market data (OpenAPI)
DEFAULT_MICRO_API_SERVER = "https://openapi.verolabs.co"

# Static content server
DEFAULT_STATIC_SERVER = "static.verolabs.co"

# Streaming endpoints
DEFAULT_STREAMING_WS = "wss://streaming.verolabs.co/connection/websocket"
DEFAULT_STREAMING_HTTP = "https://streaming.verolabs.co/connection/http_stream"
DEFAULT_STREAMING_SSE = "https://streaming.verolabs.co/connection/sse"

# Default protocol
DEFAULT_PROTOCOL = "https"

# Storage key for session token
DEFAULT_STORAGE_TOKEN_KEY = "vero_session_token"


# ============================================================================
# Default Risk Settings
# ============================================================================

DEFAULT_MAX_DAILY_LOSS = 10000.0  # Maximum daily loss before halting
DEFAULT_MAX_DAILY_PROFIT = 50000.0  # Optional profit target
DEFAULT_MAX_POSITION_LOSS_PCT = 5.0  # Max loss per position (%)
DEFAULT_MAX_POSITION_PROFIT_PCT = 10.0  # Take profit per position (%)
DEFAULT_MAX_OPEN_POSITIONS = 10  # Max concurrent positions
DEFAULT_MAX_ORDER_QTY = 1000  # Max order quantity
DEFAULT_MAX_DRAWDOWN_PCT = 15.0  # Max portfolio drawdown (%)
DEFAULT_TRAILING_STOP_PCT = 2.0  # Trailing stop percentage


# ============================================================================
# Default Backtest Settings
# ============================================================================

DEFAULT_INITIAL_CAPITAL = 100000.0  # Starting capital for backtest
DEFAULT_COMMISSION_PCT = 0.1  # Commission percentage
DEFAULT_SLIPPAGE_TICKS = 1  # Slippage in ticks


# ============================================================================
# Logging Defaults
# ============================================================================

DEFAULT_LOG_LEVEL = "DEBUG"
DEFAULT_LOG_FILE = "logs/vero_strategy.log"
DEFAULT_WARN_LOG_FILE = "logs/warn.log"
DEFAULT_STREAM_LOG_FILE = "logs/stream.log"
DEFAULT_LOG_MAX_SIZE_MB = 10
DEFAULT_LOG_BACKUP_COUNT = 5
