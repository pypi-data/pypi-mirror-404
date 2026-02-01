from dataclasses import dataclass
from typing import Optional, List, Union, Any

@dataclass
class StrategyInitSettings:
    """
    Settings for initializing a strategy, particularly for Backtesting.
    """
    initial_capital: float = 1000000000.0
    timeframe: Union[str, Any] = "1d"
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    symbols: Optional[List[str]] = None
    account_id: Optional[str] = None
    
    @classmethod
    def default(cls) -> "StrategyInitSettings":
        """Get default settings."""
        return cls()
