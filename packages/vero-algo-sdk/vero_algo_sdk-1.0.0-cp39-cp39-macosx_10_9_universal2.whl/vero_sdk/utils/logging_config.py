"""
Logging configuration for Vero Algo SDK.

Provides detailed logging with colors, file rotation, and formatted output.
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime

from .defaults import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_FILE,
    DEFAULT_LOG_MAX_SIZE_MB,
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_WARN_LOG_FILE,
    DEFAULT_STREAM_LOG_FILE,
)


# ============================================================================
# ANSI Colors for Console Output
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Log levels
    DEBUG = "\033[36m"     # Cyan
    INFO = "\033[32m"      # Green
    WARNING = "\033[33m"   # Yellow
    ERROR = "\033[31m"     # Red
    CRITICAL = "\033[35m"  # Magenta
    
    # Components
    TIMESTAMP = "\033[90m"  # Gray
    NAME = "\033[34m"       # Blue
    
    # Trading
    BUY = "\033[32m"        # Green
    SELL = "\033[31m"       # Red
    PROFIT = "\033[32m"     # Green
    LOSS = "\033[31m"       # Red


# ============================================================================
# Custom Formatters
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """Formatter with ANSI colors for console output."""
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.DEBUG,
        logging.INFO: Colors.INFO,
        logging.WARNING: Colors.WARNING,
        logging.ERROR: Colors.ERROR,
        logging.CRITICAL: Colors.CRITICAL,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)
        
        # Format timestamp: YYYY-MM-DD HH:MM:SS.mmm
        dt = datetime.fromtimestamp(record.created)
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S") + f".{int(record.msecs):03d}"
        
        # Build colored message
        # Format: TIMESTAMP | LEVEL | NAME | MESSAGE
        parts = [
            f"{Colors.TIMESTAMP}{timestamp}{Colors.RESET}",
            "|",
            f"{level_color}{record.levelname:<8}{Colors.RESET}",
            "|",
            f"{Colors.NAME}{record.name}{Colors.RESET}",
            "|",
            record.getMessage(),
        ]
        
        formatted = " ".join(parts)
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class DetailedFormatter(logging.Formatter):
    """Detailed formatter for file logging."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


# ============================================================================
# Logger Setup
# ============================================================================

_configured = False


def setup_logging(
    level: str = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = DEFAULT_LOG_FILE,
    warn_log_file: Optional[str] = DEFAULT_WARN_LOG_FILE,
    stream_log_file: Optional[str] = DEFAULT_STREAM_LOG_FILE,
    console: bool = True,
    max_size_mb: int = DEFAULT_LOG_MAX_SIZE_MB,
    backup_count: int = DEFAULT_LOG_BACKUP_COUNT,
) -> None:
    """
    Configure logging for Vero SDK.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None to disable file logging)
        warn_log_file: Path to warning/error log file
        stream_log_file: Path to dedicated streaming log file
        console: Enable console output
        max_size_mb: Max log file size before rotation
        backup_count: Number of backup log files to keep
    """
    global _configured
    
    if _configured:
        return
    
    # Configure Root Logger to capture EVERYTHING
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers to prevent duplicates/default format
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler with colors
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)
    
    # Helper to ensure directory exists
    def _ensure_dir(path: str):
        if not path: return
        log_dir = os.path.dirname(path)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception as e:
                # Fallback to stderr if we can't create directory
                sys.stderr.write(f"Failed to create log directory {log_dir}: {e}\n")

    # File handler with rotation
    if log_file:
        _ensure_dir(log_file)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(DetailedFormatter())
        logger.addHandler(file_handler)

    # Warn File handler (Errors and Warnings only)
    if warn_log_file:
        _ensure_dir(warn_log_file)
        warn_handler = RotatingFileHandler(
            warn_log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
        )
        warn_handler.setLevel(logging.WARNING)
        warn_handler.setFormatter(DetailedFormatter())
        logger.addHandler(warn_handler)

    # Separate Streaming Log Handler
    if stream_log_file:
        _ensure_dir(stream_log_file)
        stream_handler = RotatingFileHandler(
            stream_log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
        )
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(DetailedFormatter())
        
        # Configure streaming loggers (Internal + External)
        # These will log to stream.log and Console, but NOT to main strategy.log
        stream_loggers = [
            "vero_sdk.features.streaming",
            "websockets",
            "centrifuge"
        ]
        
        for name in stream_loggers:
            s_logger = logging.getLogger(name)
            s_logger.setLevel(logging.DEBUG)
            s_logger.addHandler(stream_handler)
            s_logger.propagate = False # Stop bubbling up to root (strategy.log)
            
            # Re-attach console handler if enabled, as propagation is stopped
            if console and 'console_handler' in locals():
                s_logger.addHandler(console_handler)
    
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a component.
    
    Args:
        name: Component name (e.g., "strategy", "risk", "backtest")
        
    Returns:
        Logger instance
    """
    # Ensure logging is configured
    if not _configured:
        setup_logging()
    
    # If name is 'vero', return the root vero_sdk logger or map it accordingly.
    # The warning uses logger name "vero", which might be outside "vero_sdk" namespace in some files.
    if name == "vero":
        return logging.getLogger("vero_sdk.core") # Map 'vero' to inside SDK namespace
        
    return logging.getLogger(f"vero_sdk.{name}")


# ============================================================================
# Strategy-specific Logging Helpers
# ============================================================================

class StrategyLogger:
    """Enhanced logger for strategy/robot with trading-specific methods."""
    
    def __init__(self, strategy_name: str):
        self._logger = get_logger(f"strategy.{strategy_name}")
        self.strategy_name = strategy_name
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message."""
        self._logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message."""
        self._logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message."""
        self._logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message."""
        self._logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log critical message."""
        self._logger.critical(msg, *args, **kwargs)
    
    def order(self, action: str, symbol: str, qty: int, price: float, **kwargs) -> None:
        """Log order action."""
        side_color = Colors.BUY if action.upper() in ("BUY", "LONG") else Colors.SELL
        self._logger.info(
            f"ORDER: {side_color}{action.upper()}{Colors.RESET} "
            f"{symbol} {qty}@{price}"
        )
    
    def trade(self, symbol: str, side: str, qty: int, price: float, pnl: float = 0) -> None:
        """Log trade execution."""
        side_color = Colors.BUY if side.upper() in ("B", "BUY") else Colors.SELL
        pnl_color = Colors.PROFIT if pnl >= 0 else Colors.LOSS
        pnl_str = f" P&L: {pnl_color}{pnl:+.2f}{Colors.RESET}" if pnl != 0 else ""
        self._logger.info(
            f"TRADE: {side_color}{side}{Colors.RESET} "
            f"{symbol} {qty}@{price}{pnl_str}"
        )
    
    def position(self, action: str, symbol: str, qty: int, entry: float, pnl: float = 0) -> None:
        """Log position change."""
        pnl_color = Colors.PROFIT if pnl >= 0 else Colors.LOSS
        self._logger.info(
            f"POSITION {action.upper()}: {symbol} {qty}@{entry} "
            f"P&L: {pnl_color}{pnl:+.2f}{Colors.RESET}"
        )
    
    def risk(self, msg: str) -> None:
        """Log risk management event."""
        self._logger.warning(f"RISK: {msg}")
    
    def bar(self, symbol: str, o: float, h: float, l: float, c: float, v: float) -> None:
        """Log bar data (debug level)."""
        self._logger.debug(f"BAR: {symbol} O={o} H={h} L={l} C={c} V={v}")
